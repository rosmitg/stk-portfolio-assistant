import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.portfolio import Base


class Brief(Base):
    """Read-only mapping of the existing ``briefs`` table.

    Briefs are produced by the Watchman pipeline (which shares this database)
    and written with a varchar(64) ``user_id`` matching STK's ``holdings``.
    STK only reads from this table — there are no migrations here; the table
    already exists.
    """

    __tablename__ = "briefs"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_briefs_user_id_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    headline: Mapped[str] = mapped_column(String, nullable=False)
    portfolio_health: Mapped[int] = mapped_column(Integer, nullable=False)
    sections: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    alerts: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
