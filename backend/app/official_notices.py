"""Reviewed announcement facts, separate from eligibility publications and draft edits.

This snapshot is shipped with the release. There is no runtime scraping, automatic
publication, or inference that a portal is accepting applications right now.
"""
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, field_validator, model_validator

from .db import utcnow
from .schemas import RoundInput, StrictModel

SNAPSHOT = Path(__file__).resolve().parents[2] / 'data/official/notices.json'


class AnnouncementSource(StrictModel):
    url: HttpUrl
    document: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    finance_page: int = Field(ge=1)
    dates_page: int = Field(ge=1)


class Announcement(StrictModel):
    measure_id: str
    title: str
    category: Literal['grant', 'subsidy']
    audience: str
    round: RoundInput
    funding_year: int = Field(ge=2020, le=2100)
    budget_rub: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    recipient_limit_rub: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    limit_status: Literal['stated', 'not_set_in_announcement']
    finance_note: str
    legal_edition: str
    source: AnnouncementSource
    checked_at: datetime
    missing_evidence: list[str] = Field(min_length=1)
    verification_scope: Literal['announcement_facts_only'] = 'announcement_facts_only'

    @field_validator('budget_rub', 'recipient_limit_rub', mode='before')
    @classmethod
    def exact_money(cls, value):
        if value is not None and not isinstance(value, (str, Decimal)):
            raise ValueError('Денежная сумма должна быть десятичной строкой')
        return value

    @model_validator(mode='after')
    def consistent(self):
        if self.checked_at.tzinfo is None:
            raise ValueError('Дата проверки требует часовой пояс')
        if (self.limit_status == 'stated') != (self.recipient_limit_rub is not None):
            raise ValueError('Неустановленный предел нельзя подменять нулём')
        if self.round.state != 'unknown':
            raise ValueError('Снимок объявления не подтверждает текущий приём на портале')
        if self.source.url.host != 'minagro.saratov.gov.ru' or self.source.url.scheme != 'https':
            raise ValueError('Требуется официальный первоисточник')
        if self.round.application_url.host != 'promote.budget.gov.ru' or self.round.application_url.scheme != 'https':
            raise ValueError('Неподтверждённый маршрут подачи')
        return self


class AnnouncementView(Announcement):
    deadline_status: Literal['not_started_in_notice', 'within_notice_dates', 'ended_in_notice']
    acceptance_status: Literal['unconfirmed'] = 'unconfirmed'


class AnnouncementsView(StrictModel):
    release_id: str
    items: list[AnnouncementView]


def announcements(now: datetime | None = None, path: Path = SNAPSHOT) -> AnnouncementsView:
    now = now or utcnow()
    snapshot = json.loads(path.read_text(encoding='utf-8'))
    items = []
    codes = set()
    for raw in snapshot['items']:
        item = Announcement.model_validate(raw)
        if item.round.code in codes or item.checked_at > now:
            raise ValueError('Повтор отбора или дата проверки из будущего')
        codes.add(item.round.code)
        status = ('ended_in_notice' if now >= item.round.ends_at else
                  'not_started_in_notice' if now < item.round.starts_at else 'within_notice_dates')
        items.append(AnnouncementView(**item.model_dump(), deadline_status=status))
    items.sort(key=lambda x: (x.deadline_status == 'ended_in_notice', x.round.ends_at, x.title))
    return AnnouncementsView(release_id=snapshot['release_id'], items=items)
