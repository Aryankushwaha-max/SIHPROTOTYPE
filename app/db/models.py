from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Well(Base):
    __tablename__ = "wells"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    well_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    field: Mapped[str] = mapped_column(String(120), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    total_depth_m: Mapped[float] = mapped_column(Float, default=0)
    spud_date: Mapped[str] = mapped_column(String(20), default="")
    source: Mapped[str] = mapped_column(String(40), default="prototype")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    events: Mapped[list["Event"]] = relationship(back_populates="well", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.well_id"), index=True)
    md_m: Mapped[float] = mapped_column(Float, index=True)
    formation: Mapped[str] = mapped_column(String(120), index=True)
    event_type: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    summary: Mapped[str] = mapped_column(String(500))
    impact: Mapped[str] = mapped_column(String(300), default="")
    mitigation: Mapped[str] = mapped_column(Text, default="")
    source_ref: Mapped[str] = mapped_column(String(160), default="Synthetic demonstration record")
    event_type_id: Mapped[str] = mapped_column(String(60), default="")
    report_date: Mapped[str] = mapped_column(String(20), default="")
    mud_weight_ppg: Mapped[float | None] = mapped_column(Float, nullable=True)
    npt_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_lost_bbl: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(40), default="synthetic")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    well: Mapped["Well"] = relationship(back_populates="events")
