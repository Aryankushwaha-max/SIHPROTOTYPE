from pydantic import BaseModel, Field


class RiskSnapshot(BaseModel):
    well_id: str = Field(min_length=1, max_length=32)
    md_m: float = Field(ge=0)
    radius_km: float = Field(default=10, gt=0, le=250)
    formation: str | None = None
    mud_loss_rate_m3h: float | None = Field(default=None, ge=0)
    torque_knm: float | None = Field(default=None, ge=0)
    hookload_change_kn: float | None = None
    flow_delta_pct: float | None = None
    gas_units: float | None = Field(default=None, ge=0)
    ecd_sg: float | None = Field(default=None, ge=0)


class RiskSignal(BaseModel):
    risk_type: str
    severity: str
    score: int
    reason: str
    related_events: list[str] = []


class RiskAssessment(BaseModel):
    well_id: str
    md_m: float
    assessed_at: str
    model: str
    overall_level: str
    signals: list[RiskSignal]
    disclaimer: str
