from datetime import datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BusinessProfile(StrictModel):
    registration_region: str | None = Field(default=None, max_length=60)
    activity_region: str | None = Field(default=None, max_length=60)
    legal_form: Literal["ip", "company", "cooperative", "individual"] | None = None
    is_kfh: bool | None = None
    tax_regime: Literal["eshn", "usn", "npd", "general"] | None = None
    sector: Literal["crops", "livestock", "processing", "mixed"] | None = None
    goal: Literal["equipment", "construction", "working_capital", "consultation"] | None = None
    expense_stage: Literal["planned", "incurred"] | None = None
    years_active: int | None = Field(default=None, ge=0, le=100)
    own_funds: Decimal | None = Field(default=None, ge=0, le=Decimal("1000000000000"), max_digits=15, decimal_places=2)
    is_sme: bool | None = None
    special_category: bool | None = None


class Rule(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    label: str = Field(min_length=1, max_length=300)
    field: str | None = None
    op: Literal["eq", "in", "gte", "lte", "all", "any", "manual"]
    value: str | int | bool | list[str] | None = None
    children: list["Rule"] = Field(default_factory=list, max_length=15)
    source_ref: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def valid_rule(self):
        if self.op == "manual":
            if self.field is not None or self.value is not None or self.children:
                raise ValueError("Ручная проверка не принимает field, value или children")
        elif self.op in ("all", "any"):
            if not self.children or self.field is not None:
                raise ValueError("Группа должна содержать условия, но не field")
        else:
            if self.field not in BusinessProfile.model_fields or self.children or self.value is None:
                raise ValueError("Некорректное поле или значение условия")
            if self.op == "in" and not isinstance(self.value, list):
                raise ValueError("in требует список")
            if self.field in ("is_kfh", "is_sme", "special_category") and (self.op != "eq" or type(self.value) is not bool):
                raise ValueError("Логическое поле требует eq и true/false")
            if self.op == "eq" and isinstance(self.value, list):
                raise ValueError("eq не принимает список")
            if self.field in ("years_active", "own_funds") and self.op == "in":
                raise ValueError("Числовое поле требует eq, gte или lte")
            if self.op in ("gte", "lte") or (self.op == "eq" and self.field in ("years_active", "own_funds")):
                if self.field not in ("years_active", "own_funds"):
                    raise ValueError("Числовое сравнение требует числового поля")
                try:
                    if isinstance(self.value, bool) or not Decimal(str(self.value)).is_finite():
                        raise ValueError()
                except Exception:
                    raise ValueError("Некорректное число")
        return self


class Source(StrictModel):
    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl
    reference: str = Field(min_length=1, max_length=300)
    published_on: str = Field(max_length=30)


class Document(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    title: str = Field(min_length=1, max_length=200)
    hint: str = Field(max_length=700)


class VersionData(StrictModel):
    summary: str = Field(min_length=10, max_length=1500)
    benefit: str = Field(min_length=1, max_length=500)
    operator: str = Field(min_length=1, max_length=200)
    obligations: str = Field(max_length=1500)
    contact: str = Field(max_length=300)
    rules: list[Rule] = Field(default_factory=list, max_length=30)
    documents: list[Document] = Field(default_factory=list, max_length=30)
    sources: list[Source] = Field(min_length=1, max_length=20)
    verified_at: datetime | None = None
    verification_status: Literal["unverified", "verified", "conflict"] = "unverified"
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    legal_edition: str = Field(default="", max_length=2000)
    research_checked_at: datetime | None = None
    missing_evidence: list[str] = Field(default_factory=list, max_length=30)
    verification_notes: str = Field(default="", max_length=4000)

    @field_validator("verified_at", "valid_from", "valid_until", "research_checked_at")
    @classmethod
    def require_timezone(cls, value):
        if value and value.tzinfo is None:
            raise ValueError("Укажите часовой пояс")
        return value

    @model_validator(mode="after")
    def consistency(self):
        if self.valid_until and self.valid_from and self.valid_until <= self.valid_from:
            raise ValueError("Некорректный период условий")
        ids = [d.id for d in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("Повторяющиеся ID документов")
        def visit(rules, depth=0):
            if depth > 5:
                raise ValueError("Слишком глубокое дерево правил")
            result = []
            for rule in rules:
                result.append(rule.id)
                result.extend(visit(rule.children, depth + 1))
            return result
        rule_ids = visit(self.rules)
        if len(rule_ids) != len(set(rule_ids)) or len(rule_ids) > 100:
            raise ValueError("Повторяющиеся ID или слишком много условий")
        return self


class RoundInput(StrictModel):
    code: str = Field(min_length=1, max_length=100)
    starts_at: datetime
    ends_at: datetime
    timezone: str = "Europe/Moscow"
    state: Literal["announced", "suspended", "cancelled", "unknown"] = "announced"
    application_url: HttpUrl
    channel: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def dates(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None or self.ends_at <= self.starts_at:
            raise ValueError("Неверные даты / часовой пояс отбора")
        try:
            ZoneInfo(self.timezone)
        except Exception:
            raise ValueError("Неизвестный часовой пояс")
        return self


class DraftInput(StrictModel):
    revision: int = Field(ge=1)
    data: VersionData
    rounds: list[RoundInput] = Field(default_factory=list, max_length=10)


class NewMeasure(StrictModel):
    title: str = Field(min_length=3, max_length=200)
    category: Literal["grant", "subsidy", "consultation"]
    synthetic: bool = False
    data: VersionData
    rounds: list[RoundInput] = Field(default_factory=list, max_length=10)


class RevisionInput(StrictModel):
    revision: int = Field(ge=1)


class PlanInput(StrictModel):
    round_id: str = Field(max_length=36)


class CheckInput(RevisionInput):
    done: bool


class DemoInput(StrictModel):
    persona: Literal["farmer", "editor", "second"] = "farmer"


class MaxInput(StrictModel):
    init_data: str = Field(min_length=1, max_length=16384)


class RoundView(RoundInput):
    id: str
    availability: str


class MeasureView(StrictModel):
    id: str
    title: str
    category: str
    synthetic: bool
    version_id: str
    version: int
    state: str
    revision: int
    data: VersionData
    rounds: list[RoundView]


class CheckView(StrictModel):
    id: str
    label: str
    status: Literal["PASS", "FAIL", "UNKNOWN"]
    field: str | None
    source_ref: str
    children: list["CheckView"]


class MatchView(StrictModel):
    measure: MeasureView
    status: Literal["PASS", "FAIL", "UNKNOWN"]
    checks: list[CheckView]


class MatchesView(StrictModel):
    evaluation_id: str
    results: list[MatchView]


class PlanDocument(Document):
    done: bool


class PlanView(StrictModel):
    id: str
    revision: int
    created_at: datetime
    items: list[PlanDocument]
    measure: MeasureView
    round_id: str
    needs_review: bool
    current_version_id: str | None


class UserView(StrictModel):
    id: str
    name: str
    role: str
    demo: bool


class SessionView(StrictModel):
    user: UserView
    csrf: str
