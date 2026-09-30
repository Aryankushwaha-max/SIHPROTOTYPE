import csv
import json
import math
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.repositories import EventRepository, WellRepository
from app.db.session import get_db
from app.schemas.contracts import RiskSnapshot
from app.services.geospatial import distance_km
from app.services.ingestion import extract_text, propose_events
from app.services.risk import assess

router = APIRouter(prefix=settings.api_prefix)


def well_dict(w, distance=None):
    return {"well_id": w.well_id, "name": w.name, "field": w.field, "latitude": w.latitude,
            "longitude": w.longitude, "status": w.status, "total_depth_m": w.total_depth_m,
            "spud_date": w.spud_date, "source": w.source, "is_synthetic": w.is_synthetic,
            "distance_km": round(distance, 2) if distance is not None else None}


def event_dict(e):
    return {"event_id": e.event_id, "well_id": e.well_id, "md_m": e.md_m, "formation": e.formation,
            "event_type": e.event_type, "severity": e.severity, "summary": e.summary,
            "impact": e.impact, "mitigation": e.mitigation, "source_ref": e.source_ref,
            "event_type_id": e.event_type_id, "report_date": e.report_date,
            "mud_weight_ppg": e.mud_weight_ppg, "npt_hours": e.npt_hours,
            "volume_lost_bbl": e.volume_lost_bbl, "confidence": e.confidence,
            "source": e.source, "is_synthetic": e.is_synthetic, "raw_text": e.raw_text}


@router.get("/health")
def health():
    return {"status": "ok", "service": "ertmac-nwis", "environment": "prototype"}


@router.get("/wells")
def list_wells(lat: float | None = None, lon: float | None = None,
               radius_km: float = Query(default=10, gt=0, le=250), q: str | None = None,
               db: Session = Depends(get_db)):
    repo = WellRepository(db)
    wells = repo.list(q)
    if lat is None or lon is None:
        return [well_dict(w) for w in wells]
    found = []
    for w in wells:
        d = distance_km(lat, lon, w.latitude, w.longitude)
        if d <= radius_km:
            found.append(well_dict(w, d))
    return sorted(found, key=lambda item: item["distance_km"])


@router.get("/wells/{well_id:path}")
def get_well(well_id: str, db: Session = Depends(get_db)):
    well = WellRepository(db).get(well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    return {**well_dict(well), "metadata": json.loads(well.metadata_json or "{}"),
            "events": [event_dict(e) for e in EventRepository(db).search(well_ids=[well_id])]}


@router.get("/events")
def list_events(q: str | None = None, event_type: str | None = None, formation: str | None = None,
                severity: str | None = None, well_id: str | None = None,
                limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0),
                db: Session = Depends(get_db)):
    items = EventRepository(db).search(q=q, event_type=event_type, formation=formation, severity=severity,
                                       well_ids=[well_id] if well_id else None)
    return {"total": len(items), "items": [event_dict(e) for e in items[offset:offset + limit]]}


@router.get("/analytics/summary")
def summary(db: Session = Depends(get_db)):
    wells = WellRepository(db).list()
    events = EventRepository(db).search()
    distribution = {}
    for event in events:
        distribution[event.event_type] = distribution.get(event.event_type, 0) + 1
    return {"well_count": len(wells), "event_count": len(events),
            "real_wells": sum(not w.is_synthetic for w in wells),
            "synthetic_wells": sum(w.is_synthetic for w in wells),
            "high_severity_events": sum(e.severity in {"high", "critical"} for e in events),
            "event_distribution": distribution}


@router.get("/ddrs")
def search_ddrs(q: str = Query(min_length=2, max_length=120),
                hazard: str | None = None, limit: int = Query(default=20, ge=1, le=100)):
    """Search source DDR excerpts independently from geo-linked well events."""
    path = Path(__file__).parents[1] / "data" / "reference" / "volve_ddrs.jsonl"
    query = q.casefold()
    found = []
    for line in path.open(encoding="utf-8"):
        report = json.loads(line)
        if query not in report["text"].casefold() and query not in report.get("event_id", "").casefold():
            continue
        if hazard and report.get("hazard") != hazard:
            continue
        found.append({**report, "attribution_status": "source well key is unresolved in supplied extract; not geospatially assigned"})
        if len(found) >= limit:
            break
    return {"query": q, "count": len(found), "items": found,
            "source_records": "1,686 searchable Volve DDR excerpts; supplied source labels well_id as NO"}


@router.get("/telemetry")
def get_reference_telemetry(limit: int = Query(default=700, ge=50, le=2000)):
    """Return a decimated read-only reference trace from Volve well 15/9-F-9A."""
    path = Path(__file__).parents[1] / "data" / "reference" / "volve_telemetry.csv"
    depth_key = "Measured Depth m"
    fields = {"depth_m": depth_key, "rop_m_h": "Rate of Penetration m/h",
              "rotary_rpm": "Average Rotary Speed rpm", "torque_knm": "Averaged TRQ kN.m",
              "hookload_kkgf": "Corrected Total Hookload kkgf", "wob_kkgf": "Weight on Bit kkgf",
              "mud_flow_l_min": "Mud Flow In L/min", "spp_kpa": "Average Standpipe Pressure kPa",
              "mud_density_g_cm3": "Mud Density Out g/cm3", "gas_pct": "Gas (avg) %"}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        total = 0
        # Keep one uniformly spaced point set and exact samples close to the archived 619 m incident.
        raw = list(reader)
        total = len(raw)
        stride = max(1, len(raw) // limit)
        selected = raw[::stride]
        for row in raw:
            try:
                depth_value = float(row[depth_key])
            except (KeyError, TypeError, ValueError):
                continue
            if math.isfinite(depth_value) and abs(depth_value - 619.0) < 0.15:
                selected.append(row)
        seen = set()
        for row in selected:
            depth = row.get(depth_key)
            if not depth:
                continue
            try:
                parsed_depth = float(depth)
            except ValueError:
                continue
            if not math.isfinite(parsed_depth) or parsed_depth in seen:
                continue
            seen.add(parsed_depth)
            point = {}
            for key, source_key in fields.items():
                value = row.get(source_key)
                try:
                    parsed = float(value) if value not in (None, "") else None
                    point[key] = round(parsed, 4) if parsed is not None and math.isfinite(parsed) else None
                except ValueError:
                    point[key] = None
            rows.append(point)
    rows.sort(key=lambda point: point["depth_m"] or 0)
    return {"well_id": "15/9-F-9A", "source": "real_volve", "is_live": False,
            "source_records": total, "points": rows,
            "incident_reference": {"depth_m": 619.0, "hazard": "stuck_pipe", "well_id_attribution": "from supplied backtest report; DDR archive event key is generic NO"},
            "notice": "Historical public reference telemetry only. The archived backtest is not validation of this prototype."}


@router.post("/risks/assess")
def assess_risk(snapshot: RiskSnapshot, db: Session = Depends(get_db)):
    well_repo = WellRepository(db)
    well = well_repo.get(snapshot.well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found")
    offsets = [other.well_id for other in well_repo.list()
               if other.well_id != well.well_id and
               distance_km(well.latitude, well.longitude, other.latitude, other.longitude) <= snapshot.radius_km]
    return assess(snapshot, EventRepository(db), offsets).model_dump()


@router.post("/documents/ingest")
async def ingest_document(file: UploadFile = File(...)):
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the configured upload limit")
    try:
        extracted = extract_text(file.filename or "upload.txt", content)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"filename": file.filename, "characters_extracted": len(extracted), "text_preview": extracted[:5000],
            "candidates": propose_events(extracted),
            "notice": "Candidates are unverified and are not stored as authoritative events. OCR for scanned PDFs requires an approved integration."}
