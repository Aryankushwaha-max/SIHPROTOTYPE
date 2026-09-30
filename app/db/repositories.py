from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Event, Well


class WellRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, query: str | None = None) -> list[Well]:
        stmt = select(Well).order_by(Well.name)
        if query:
            term = f"%{query}%"
            stmt = stmt.where(or_(Well.name.ilike(term), Well.well_id.ilike(term), Well.field.ilike(term)))
        return list(self.db.scalars(stmt))

    def get(self, well_id: str) -> Well | None:
        return self.db.scalar(select(Well).where(Well.well_id == well_id))


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def search(self, q: str | None = None, event_type: str | None = None, formation: str | None = None,
               severity: str | None = None, well_ids: list[str] | None = None) -> list[Event]:
        stmt = select(Event).order_by(Event.md_m)
        if q:
            term = f"%{q}%"
            stmt = stmt.where(or_(Event.summary.ilike(term), Event.mitigation.ilike(term), Event.well_id.ilike(term)))
        if event_type:
            stmt = stmt.where(Event.event_type == event_type)
        if formation:
            stmt = stmt.where(Event.formation.ilike(formation))
        if severity:
            stmt = stmt.where(Event.severity == severity)
        if well_ids:
            stmt = stmt.where(Event.well_id.in_(well_ids))
        return list(self.db.scalars(stmt))
