import hashlib
import hmac
import json
from copy import deepcopy
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .auth import create_session, current_session, current_user, editor
from .catalog import (
    add_rounds,
    audit,
    current_version,
    evaluation_snapshot,
    lock_version,
    publication_checks,
    serialize_measure,
    serialize_plan,
    visible_versions,
)
from .config import settings
from .db import get_db, utcnow
from .matching import availability, evaluate, evaluate_documents
from .max_adapter import prepare_event, validate_launch
from .models import (
    AuthSession,
    BotEvent,
    Evaluation,
    Measure,
    Plan,
    Profile,
    SelectionRound,
    UsedLaunch,
    User,
    Version,
)
from .schemas import (
    BusinessProfile,
    CheckInput,
    DemoInput,
    DraftInput,
    MatchesView,
    MaxInput,
    MeasureView,
    NewMeasure,
    PlanInput,
    PlanView,
    RevisionInput,
    RoundInput,
    SessionView,
    PreviewInput,
    PreviewView,
    ProfileQuestion,
    PlanAssessment,
)

router = APIRouter(prefix="/api")

from .official_notices import AnnouncementsView, announcements


@router.get(
    "/official-announcements",
    response_model=AnnouncementsView,
    description="Checked monetary facts and dates; not an eligibility decision or a live portal status.",
)
def official_announcements():
    return announcements()


@router.get("/config")
def config():
    import re

    link = settings().max_app_url
    public_link = (
        link
        if re.fullmatch(r"https://max\.ru/[A-Za-z0-9_-]{1,128}\?startapp", link)
        else None
    )
    return {
        "demo": settings().app_env == "demo",
        "max_configured": bool(settings().max_bot_token),
        "title": "Опора АПК",
        "max_app_url": public_link,
    }


@router.post("/auth/demo", response_model=SessionView)
def demo_login(body: DemoInput, response: Response, db: Session = Depends(get_db)):
    if settings().app_env not in ("demo", "test"):
        raise HTTPException(404, "Не найдено")
    user_id = "demo:" + body.persona
    user = db.get(User, user_id)
    if not user:
        names = {
            "farmer": "Демо-фермер",
            "editor": "Демо-редактор",
            "second": "Второй демо-фермер",
        }
        user = User(
            id=user_id,
            name=names[body.persona],
            role="editor" if body.persona == "editor" else "farmer",
            demo=True,
        )
        db.add(user)
        db.flush()
    return create_session(db, user, response)


@router.post("/auth/max", response_model=SessionView)
def max_login(body: MaxInput, response: Response, db: Session = Depends(get_db)):
    if not settings().max_bot_token:
        raise HTTPException(503, "MAX ещё не подключён")
    try:
        identity = validate_launch(body.init_data, settings().max_bot_token)
    except (ValueError, KeyError, TypeError):
        raise HTTPException(401, "Недействительные данные запуска MAX")
    db.add(UsedLaunch(hash=identity["hash"]))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(401, "Данные уже использованы. Откройте приложение заново")
    user_id = "max:" + str(identity["id"])
    user = db.get(User, user_id)
    role = (
        "editor"
        if str(identity["id"])
        in {i.strip() for i in settings().max_admin_ids.split(",")}
        else "farmer"
    )
    if not user:
        user = User(id=user_id, name=identity["name"], role=role, demo=False)
        db.add(user)
    else:
        user.role = role
    db.flush()
    return create_session(db, user, response)


@router.get("/auth/me", response_model=SessionView)
def me(
    user: User = Depends(current_user), session: AuthSession = Depends(current_session)
):
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "demo": user.demo,
        },
        "csrf": session.csrf,
    }


@router.post("/auth/logout")
def logout(
    response: Response,
    session: AuthSession = Depends(current_session),
    db: Session = Depends(get_db),
):
    db.delete(session)
    db.commit()
    response.delete_cookie("opora_session", path="/")
    return {"ok": True}


@router.get("/profile", response_model=BusinessProfile)
def profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(Profile, user.id)
    return item.data if item else BusinessProfile()


@router.get("/profile/questions", response_model=list[ProfileQuestion])
def profile_questions(db: Session = Depends(get_db)):
    from .questions import additional_questions

    return additional_questions(v.data for v in visible_versions(db))


@router.put("/profile", response_model=BusinessProfile)
def save_profile(
    body: BusinessProfile,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    item = db.get(Profile, user.id)
    data = body.model_dump(mode="json")
    if item:
        item.data = data
        item.updated_at = utcnow()
    else:
        db.add(Profile(user_id=user.id, data=data))
    db.commit()
    return body


@router.get("/catalog", response_model=list[MeasureView])
def catalog(db: Session = Depends(get_db)):
    return [serialize_measure(db, v) for v in visible_versions(db)]


@router.get("/measures/{measure_id}", response_model=MeasureView)
def measure_detail(measure_id: str, db: Session = Depends(get_db)):
    version = current_version(db, measure_id)
    if not version or (
        settings().app_env == "production" and db.get(Measure, measure_id).synthetic
    ):
        raise HTTPException(404, "Мера не опубликована")
    return serialize_measure(db, version)


@router.post("/matches", response_model=MatchesView)
def matches(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile_ = db.get(Profile, user.id)
    if not profile_:
        raise HTTPException(400, "Сначала сохраните анкету")
    results = [
        {"measure": serialize_measure(db, v), **evaluate(v.data, profile_.data), "documents": evaluate_documents(v.data, profile_.data)}
        for v in visible_versions(db)
    ]
    rank = {"PASS": 0, "UNKNOWN": 1, "FAIL": 2}
    results.sort(
        key=lambda r: (
            rank[r["status"]],
            not any(s["availability"] == "open" for s in r["measure"]["rounds"]),
        )
    )
    saved = MatchesView(evaluation_id=str(uuid4()), results=results)
    snapshot = evaluation_snapshot(saved.model_dump(mode="json")["results"])
    last = db.scalar(
        select(Evaluation)
        .where(Evaluation.user_id == user.id)
        .order_by(Evaluation.created_at.desc())
        .limit(1)
    )
    if last and last.profile == profile_.data and last.results == snapshot:
        saved.evaluation_id = last.id
        return saved
    db.add(
        Evaluation(
            id=saved.evaluation_id,
            user_id=user.id,
            profile=deepcopy(profile_.data),
            results=snapshot,
        )
    )
    db.commit()
    return saved


@router.get("/preparation-plans", response_model=list[PlanView])
def plans(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [
        serialize_plan(db, p)
        for p in db.scalars(
            select(Plan).where(Plan.user_id == user.id).order_by(Plan.created_at.desc())
        ).all()
    ]


@router.post("/preparation-plans", response_model=PlanView)
def create_plan(
    body: PlanInput, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    round_ = db.get(SelectionRound, body.round_id)
    if not round_:
        raise HTTPException(404, "Отбор не найден")
    version = db.scalar(
        select(Version).where(Version.id == round_.version_id).with_for_update()
    )
    if version.state != "published" or (
        settings().app_env == "production"
        and db.get(Measure, version.measure_id).synthetic
    ):
        raise HTTPException(409, "Условия изменились. Откройте актуальную карточку")
    existing = db.scalar(
        select(Plan).where(Plan.user_id == user.id, Plan.round_id == round_.id)
    )
    if existing:
        return serialize_plan(db, existing)
    profile_row = db.get(Profile, user.id)
    profile_data = BusinessProfile.model_validate(
        profile_row.data if profile_row else {}
    ).model_dump(mode="json")
    assessed_at = utcnow()
    saved_round = next(
        r for r in serialize_measure(db, version)["rounds"] if r["id"] == round_.id
    )
    saved_round["availability"] = availability(
        round_, version.data, now=assessed_at, fresh_days=settings().source_fresh_days
    )
    assessment = PlanAssessment(
        engine_version="rules-20260928.1",
        assessed_at=assessed_at,
        profile=profile_data,
        version_id=version.id,
        version=version.number,
        legal_edition=version.data.get("legal_edition", ""),
        round=saved_round,
        availability=saved_round["availability"],
        **evaluate(version.data, profile_data)
    ).model_dump(mode="json")
    plan = Plan(
        id=str(uuid4()),
        user_id=user.id,
        version_id=version.id,
        round_id=round_.id,
        items=[{**d, "done": False} for d in evaluate_documents(version.data, profile_data)],
        assessment=assessment,
    )
    db.add(plan)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        plan = db.scalar(
            select(Plan).where(Plan.user_id == user.id, Plan.round_id == round_.id)
        )
        if not plan:
            raise
    return serialize_plan(db, plan)


@router.patch("/preparation-plans/{plan_id}/items/{item_id}", response_model=PlanView)
def check_item(
    plan_id: str,
    item_id: str,
    body: CheckInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    plan = db.scalar(
        select(Plan)
        .where(Plan.id == plan_id, Plan.user_id == user.id)
        .with_for_update()
    )
    if not plan:
        raise HTTPException(404, "План не найден")
    if plan.revision != body.revision:
        raise HTTPException(409, "План изменился в другой вкладке. Обновите страницу")
    if not any(i["id"] == item_id for i in plan.items):
        raise HTTPException(404, "Документ не найден")
    plan.items = [
        {**i, "done": body.done} if i["id"] == item_id else i for i in plan.items
    ]
    plan.revision += 1
    db.commit()
    return serialize_plan(db, plan)


@router.get("/admin/versions", response_model=list[MeasureView])
def admin_versions(_: User = Depends(editor), db: Session = Depends(get_db)):
    return [
        serialize_measure(db, v)
        for v in db.scalars(select(Version).order_by(Version.created_at.desc())).all()
    ]


@router.post("/admin/preview", response_model=PreviewView)
def preview_rules(body: PreviewInput, _: User = Depends(editor)):
    return evaluate(
        body.data.model_dump(mode="json"), body.profile.model_dump(mode="json")
    )


@router.post("/admin/measures", response_model=MeasureView)
def new_measure(
    body: NewMeasure, user: User = Depends(editor), db: Session = Depends(get_db)
):
    if settings().app_env == "production" and body.synthetic:
        raise HTTPException(400, "Демонстрационные данные запрещены")
    measure = Measure(
        id=str(uuid4()),
        title=body.title,
        category=body.category,
        synthetic=body.synthetic,
    )
    db.add(measure)
    db.flush()
    version = Version(
        id=str(uuid4()),
        measure_id=measure.id,
        number=1,
        state="draft",
        data=body.data.model_dump(mode="json"),
    )
    db.add(version)
    db.flush()
    add_rounds(db, version.id, body.rounds)
    audit(db, user.id, "create", version.id)
    db.commit()
    return serialize_measure(db, version)


@router.post("/admin/versions/{version_id}/clone", response_model=MeasureView)
def clone_version(
    version_id: str, user: User = Depends(editor), db: Session = Depends(get_db)
):
    old = db.get(Version, version_id)
    if not old:
        raise HTTPException(404, "Версия не найдена")
    db.scalar(select(Measure).where(Measure.id == old.measure_id).with_for_update())
    number = (
        db.scalar(
            select(func.max(Version.number)).where(Version.measure_id == old.measure_id)
        )
        + 1
    )
    data = deepcopy(old.data)
    data["verification_status"] = "unverified"
    data["verified_at"] = None
    new = Version(
        id=str(uuid4()),
        measure_id=old.measure_id,
        number=number,
        state="draft",
        data=data,
    )
    db.add(new)
    db.flush()
    rounds = serialize_measure(db, old)["rounds"]
    add_rounds(
        db,
        new.id,
        [
            RoundInput.model_validate(
                {k: v for k, v in r.items() if k not in ("id", "availability")}
            )
            for r in rounds
        ],
    )
    audit(db, user.id, "clone", new.id)
    db.commit()
    return serialize_measure(db, new)


@router.put("/admin/versions/{version_id}", response_model=MeasureView)
def update_draft(
    version_id: str,
    body: DraftInput,
    user: User = Depends(editor),
    db: Session = Depends(get_db),
):
    version = lock_version(db, version_id, body.revision)
    if version.state != "draft":
        raise HTTPException(
            409, "Изменять можно только черновик. Создайте новую версию"
        )
    version.data = body.data.model_dump(mode="json")
    version.revision += 1
    db.execute(delete(SelectionRound).where(SelectionRound.version_id == version.id))
    add_rounds(db, version.id, body.rounds)
    audit(db, user.id, "edit", version.id)
    db.commit()
    return serialize_measure(db, version)


@router.post("/admin/versions/{version_id}/{action}", response_model=MeasureView)
def transition(
    version_id: str,
    action: str,
    body: RevisionInput,
    user: User = Depends(editor),
    db: Session = Depends(get_db),
):

    found = db.get(Version, version_id)
    if not found:
        raise HTTPException(404, "Версия не найдена")
    db.scalar(select(Measure).where(Measure.id == found.measure_id).with_for_update())
    version = lock_version(db, version_id, body.revision)
    states = {
        "review": ("draft", "review"),
        "return": ("review", "draft"),
        "publish": ("review", "published"),
        "unpublish": ("published", "archived"),
    }
    if action not in states or version.state != states[action][0]:
        raise HTTPException(409, "Недопустимый переход состояния")
    if action == "publish":
        publication_checks(db, version)
        for old in db.scalars(
            select(Version).where(
                Version.measure_id == version.measure_id, Version.state == "published"
            )
        ):
            old.state = "archived"
            old.revision += 1
        db.flush()
    version.state = states[action][1]
    version.revision += 1
    audit(db, user.id, action, version.id)
    db.commit()
    return serialize_measure(db, version)


@router.post("/max/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    expected = settings().max_webhook_secret
    if not expected or not hmac.compare_digest(
        expected, request.headers.get("X-Max-Bot-Api-Secret", "")
    ):
        raise HTTPException(403, "Неверный секрет webhook")
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError()
        key, reply = prepare_event(payload, settings().max_app_url)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(400, "Некорректное событие")
    db.add(BotEvent(key=key, reply=reply, state="pending" if reply else "ignored"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"ok": True}
