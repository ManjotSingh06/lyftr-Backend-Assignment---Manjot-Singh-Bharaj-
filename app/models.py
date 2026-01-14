from sqlalchemy import MetaData, Table, Column, String, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, field_validator
from typing import Optional
from .config import settings
import re

# SQLAlchemy setup
engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

metadata = MetaData()

messages_table = Table(
    "messages",
    metadata,
    Column("message_id", String, primary_key=True),
    Column("from_msisdn", String, nullable=False),
    Column("to_msisdn", String, nullable=False),
    Column("ts", String, nullable=False),
    Column("text", Text),
    Column("created_at", String, nullable=False),
)

# Pydantic models
class MessageIn(BaseModel):
    message_id: str
    from_: str  # 'from' is a keyword, so 'from_'
    to: str
    ts: str
    text: Optional[str] = None

    @field_validator("message_id")
    @classmethod
    def validate_message_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("message_id must be non-empty")
        return v

    @field_validator("from_", "to")
    @classmethod
    def validate_e164(cls, v: str) -> str:
        # E.164 format: starts with +, followed by digits only
        if not re.match(r"^\+\d+$", v):
            raise ValueError("must be in E.164 format (e.g., +919876543210)")
        return v

    @field_validator("ts")
    @classmethod
    def validate_ts(cls, v: str) -> str:
        # ISO-8601 UTC string with Z suffix
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", v):
            raise ValueError("ts must be ISO-8601 UTC string with Z suffix (e.g., 2025-01-15T10:00:00Z)")
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 4096:
            raise ValueError("text must be max 4096 characters")
        return v

    class Config:
        allow_population_by_field_name = True

class MessageOut(BaseModel):
    message_id: str
    from_: str
    to: str
    ts: str
    text: Optional[str] = None
    created_at: str

# DB init
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
