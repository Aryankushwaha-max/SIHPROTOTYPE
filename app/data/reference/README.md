# Bundled reference dataset

This folder contains a purpose-curated subset derived from the user-supplied `SIH_2026_PLANNS.zip` reference archive. It does not include the archive's `.git` directory, cached models, generated backtest logs, or unrelated artifacts.

| File | Contents | Source and caveats |
|---|---|---|
| `wells.json` | 159 well metadata records: 118 FORCE 2020 wells, one Volve well, and 40 synthetic controls | Derived from `NLP/nlp_task_ddr/results/module1_outputs/wells_metadata.json`. The 40 control coordinates are synthetic. |
| `events.json` | 200 explicitly synthetic structured event records | Derived from `NLP/nlp_task_ddr/results/module1_outputs/events.jsonl`; 185 hazard records and 15 routine/no-hazard records. Text and model confidence are preserved with source IDs. |
| `volve_ddrs.jsonl` | 1,686 non-empty historical DDR text excerpts | Derived from real Volve-labeled rows in the supplied `events.jsonl`. The upstream extraction uses the generic well ID `NO`; the app searches these reports separately and does not map them to wells. Empty/`nan` excerpts are omitted. |
| `volve_telemetry.csv` | Full supplied Volve F-9A telemetry CSV | Derived from `datasets/Volve Real-Time Drilling Data/Norway-NA-15_47_9-F-9 A depth.csv`; served as a decimated historical chart, never a live stream. |

## Attribution and use

The supplied project documentation identifies Volve / Equinor data and FORCE 2020 / Norwegian Petroleum Directorate data (Zenodo record 4351156), and links the Volve DDR Alpaca dataset to `bengsoon/volve_alpaca`. Refer to the upstream documentation and data providers for original attribution and terms. The supplied archive does not contain a clear standalone license covering every bundled data file; confirm redistribution terms before publishing this repository or using it outside the project team.

The app keeps `source`, `is_synthetic`, `source_ref`, and extraction confidence fields visible. The bundled synthetic controls and events are for demonstrations and must never be interpreted as OIL well history.
