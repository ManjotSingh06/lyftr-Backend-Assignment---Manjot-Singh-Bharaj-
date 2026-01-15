from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from .models import async_session, messages_table

async def insert_message(message_id: str, from_: str, to: str, ts: str, text: Optional[str]) -> bool:
    async with async_session() as session:  # type: ignore
        stmt = messages_table.insert().values(
            message_id=message_id,
            from_msisdn=from_,
            to_msisdn=to,
            ts=ts,
            text=text,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        try:
            await session.execute(stmt)
            await session.commit()
            return True
        except IntegrityError:
            await session.rollback()
            return False

async def get_messages(limit: int, offset: int, from_: Optional[str], since: Optional[str], q: Optional[str]) -> Tuple[List[Dict[str, Any]], int]:
    async with async_session() as session:  # type: ignore
        base = select(messages_table).order_by(messages_table.c.ts.asc(), messages_table.c.message_id.asc())
        where_clauses = []
        if from_:
            where_clauses.append(messages_table.c.from_msisdn == from_)
        if since:
            where_clauses.append(messages_table.c.ts >= since)
        if q:
            where_clauses.append(
                func.lower(func.coalesce(messages_table.c.text, "")).like(f"%{q.lower()}%")
            )
        if where_clauses:
            base = base.where(*where_clauses)

        # total
        total_stmt = select(func.count()).select_from(messages_table)
        if where_clauses:
            total_stmt = total_stmt.where(*where_clauses)
        total = await session.scalar(total_stmt) or 0

        stmt = base.limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = result.fetchall()
        messages = [
            {
                "message_id": r.message_id,
                "from": r.from_msisdn,
                "to": r.to_msisdn,
                "ts": r.ts,
                "text": r.text,
            }
            for r in rows
        ]
        return messages, total

async def get_stats():
    async with async_session() as session:  # type: ignore
        total_messages = await session.scalar(select(func.count(messages_table.c.message_id))) or 0
        senders_count = await session.scalar(select(func.count(func.distinct(messages_table.c.from_msisdn)))) or 0
        subq = select(messages_table.c.from_msisdn, func.count(messages_table.c.message_id).label("count")).group_by(messages_table.c.from_msisdn).order_by(text("count DESC")).limit(10)
        result = await session.execute(subq)
        messages_per_sender = [{"from": r[0], "count": r[1]} for r in result.fetchall()]
        first_ts = await session.scalar(select(func.min(messages_table.c.ts)))
        last_ts = await session.scalar(select(func.max(messages_table.c.ts)))
        return {
            "total_messages": total_messages,
            "senders_count": senders_count,
            "messages_per_sender": messages_per_sender,
            "first_message_ts": first_ts if total_messages > 0 else None,
            "last_message_ts": last_ts if total_messages > 0 else None,
        }
