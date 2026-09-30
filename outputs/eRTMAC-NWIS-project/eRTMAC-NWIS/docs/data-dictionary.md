# Prototype Data Dictionary

Bundled data includes public reference records and explicitly tagged synthetic controls/events. The canonical field names below are prototype contracts, not an approved Oil India Limited data standard.

## Well

| Field | Type / unit | Meaning |
|---|---|---|
| `well_id` | string | Stable identifier used to relate events and measurements |
| `name`, `field` | string | Display name and synthetic field name |
| `latitude`, `longitude` | decimal degrees | WGS84 surface location |
| `status` | string | Reference status; bundled wells are not asserted to be drilling today |
| `total_depth_m` | metres | Recorded total depth |
| `spud_date` | ISO date string | Demonstration spud date |
| `source` | string | `real_force2020`, `real_volve` or `synthetic` |
| `is_synthetic` | boolean | Explicit synthetic-data tag |
| `metadata_json` | JSON text | Source metadata such as trajectories, formations, casing and mud program |

## Operational event

| Field | Type / unit | Meaning |
|---|---|---|
| `event_id` | string | Unique event key |
| `well_id` | string | Parent well key |
| `md_m` | metres measured depth | Event depth; datum is unspecified in demo records |
| `formation` | string | Formation label |
| `event_type` | string | Hazard such as `mud_loss`, `kick`, `stuck_pipe`, `cementing`, `none` |
| `event_type_id` | string | Source taxonomy code such as `EVT_DIFF_STICKING` |
| `severity` | string | Source category (`none`, `low`, `medium`, `high`, `critical`) |
| `summary`, `impact`, `mitigation` | text | Synthetic event narrative, calculated impact and mitigation when available |
| `source_ref` | string | Provenance label identifying the upstream record |
| `source`, `is_synthetic` | string / boolean | Source label and explicit synthetic-data flag |
| `confidence` | 0–1 number | Copied from supplied extraction; not a calibrated probability |
| `raw_text` | text | Original synthetic report excerpt |

## Risk snapshot

The prototype accepts a measured depth in metres and optional mud-loss rate (m³/h), torque (kN·m), hookload change (kN), flow delta (percent), gas reading (unspecified demo units), and ECD (SG). Units and reference baselines must be established with OIL data owners before connecting operational sources. ECD is accepted as metadata for future rules but is not currently used to trigger a risk signal.

## Integration mapping checklist

For each source, map the OIL well key, coordinate reference system, depth datum, measured vs true vertical depth, unit conventions, timezone, event taxonomy, severity definitions, source document ID and page/section provenance. Preserve original source values and record normalization lineage. Reject or quarantine rows that fail identity or unit validation.

The supplied DDR extraction labels source reports with the generic well key `NO`; NWIS therefore serves those excerpts through text search without geospatial association. Source provenance and redistribution caveats are in `app/data/reference/README.md`.
