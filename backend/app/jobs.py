import asyncio
from datetime import timedelta
from sqlalchemy import select
from .config import settings
from .db import SessionLocal, utcnow
from .max_adapter import MaxClient
from .models import BotEvent


async def deliver_once():
    if not settings().max_bot_token:
        return 0
    delivered = 0
    with SessionLocal() as db:
        events = db.scalars(
            select(BotEvent)
            .where(BotEvent.state == "pending", BotEvent.next_attempt <= utcnow())
            .order_by(BotEvent.next_attempt)
            .limit(10)
            .with_for_update(skip_locked=True)
        ).all()
        for event in events:
            event.attempts += 1
            try:
                await MaxClient(settings()).send(**event.reply)
                event.state = "sent"
                delivered += 1
            except Exception:

                event.state = "failed" if event.attempts >= 5 else "pending"
                event.next_attempt = utcnow() + timedelta(
                    seconds=min(600, 15 * 2**event.attempts)
                )
        db.commit()
    return delivered


async def run():
    while True:
        await deliver_once()
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run())
