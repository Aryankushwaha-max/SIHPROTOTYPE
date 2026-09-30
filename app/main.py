from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import router
from app.core.config import settings
from app.db.base import Base
from app.db.models import Event, Well
from app.db.session import SessionLocal, engine, upgrade_prototype_schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    upgrade_prototype_schema()
    with SessionLocal() as db:
        data_dir = Path(__file__).parent / "data" / "reference"
        well_records = json.loads((data_dir / "wells.json").read_text(encoding="utf-8"))
        event_records = json.loads((data_dir / "events.json").read_text(encoding="utf-8"))
        # Remove only the six known synthetic rows shipped by the first prototype release.
        legacy_sample_ids = {"OIL-AX-014", "OIL-AX-018", "OIL-AX-021", "OIL-AX-025", "OIL-BR-006", "OIL-BR-011"}
        db.query(Event).filter(Event.well_id.in_(legacy_sample_ids)).delete(synchronize_session=False)
        db.query(Well).filter(Well.well_id.in_(legacy_sample_ids)).delete(synchronize_session=False)
        existing_wells = {row[0] for row in db.query(Well.well_id).all()}
        new_wells = []
        for record in well_records:
            if record["well_id"] in existing_wells:
                continue
            record["metadata_json"] = json.dumps(record.pop("metadata"), ensure_ascii=False)
            new_wells.append(Well(**record))
        db.add_all(new_wells)
        if new_wells:
            db.flush()
        existing_events = {row[0] for row in db.query(Event.event_id).all()}
        db.add_all(Event(**record) for record in event_records if record["event_id"] not in existing_events)
        db.commit()
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", description="Nearby wells decision support prototype", lifespan=lifespan)
app.include_router(router)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(static_dir / "index.html")
