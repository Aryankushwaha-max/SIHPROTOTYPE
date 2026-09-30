from datetime import datetime, timezone

from app.db.repositories import EventRepository
from app.schemas.contracts import RiskAssessment, RiskSignal, RiskSnapshot


DISCLAIMER = "Heuristic prototype indicator only. Not a validated predictive model or operational instruction. Confirm with approved procedures and the drilling team."


def assess(snapshot: RiskSnapshot, events: EventRepository, related_well_ids: list[str] | None = None) -> RiskAssessment:
    relevant_wells = list(dict.fromkeys([snapshot.well_id, *(related_well_ids or [])]))
    nearby = [e for e in events.search(well_ids=relevant_wells) if abs(e.md_m - snapshot.md_m) <= 250]
    signals: list[RiskSignal] = []

    def add(kind: str, severity: str, score: int, reason: str, related: list[str] | None = None):
        signals.append(RiskSignal(risk_type=kind, severity=severity, score=score, reason=reason, related_events=related or []))

    matches = [e.event_id for e in nearby if e.event_type == "mud_loss"]
    if snapshot.mud_loss_rate_m3h is not None and snapshot.mud_loss_rate_m3h > 0:
        add("mud_loss", "high" if snapshot.mud_loss_rate_m3h >= 10 else "medium", 85 if snapshot.mud_loss_rate_m3h >= 10 else 58,
            f"Reported loss rate: {snapshot.mud_loss_rate_m3h:g} m³/h.", matches)
    if snapshot.torque_knm is not None and snapshot.torque_knm >= 25:
        add("torque_spike", "high" if snapshot.torque_knm >= 35 else "medium", 78 if snapshot.torque_knm >= 35 else 54,
            f"Torque ({snapshot.torque_knm:g} kN·m) exceeds the prototype review threshold.",
            [e.event_id for e in nearby if e.event_type in {"torque_spike", "stuck_pipe"}])
    if snapshot.hookload_change_kn is not None and snapshot.hookload_change_kn >= 50:
        add("stuck_pipe", "high" if snapshot.hookload_change_kn >= 100 else "medium", 75 if snapshot.hookload_change_kn >= 100 else 52,
            f"Hookload increase ({snapshot.hookload_change_kn:g} kN) merits review against well context.",
            [e.event_id for e in nearby if e.event_type == "stuck_pipe"])
    if snapshot.flow_delta_pct is not None and snapshot.flow_delta_pct >= 5:
        add("kick_flow_anomaly", "high", 88, f"Flow delta ({snapshot.flow_delta_pct:g}%) exceeds the prototype screening threshold.",
            [e.event_id for e in nearby if e.event_type in {"kick", "overpressure"}])
    if snapshot.gas_units is not None and snapshot.gas_units >= 100:
        add("gas_anomaly", "medium", 60, f"Gas reading ({snapshot.gas_units:g} units) exceeds the prototype screening threshold.",
            [e.event_id for e in nearby if e.event_type in {"kick", "overpressure"}])
    level = "high" if any(s.severity == "high" for s in signals) else "watch" if signals else "normal"
    return RiskAssessment(well_id=snapshot.well_id, md_m=snapshot.md_m,
        assessed_at=datetime.now(timezone.utc).isoformat(), model="transparent-rules-v1",
        overall_level=level, signals=signals, disclaimer=DISCLAIMER)
