from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def upgrade_prototype_schema():
    """Add fields used by the reference dataset to existing local prototype databases."""
    additions = {
        "wells": {
            "source": "VARCHAR(40) NOT NULL DEFAULT 'prototype'",
            "is_synthetic": "BOOLEAN NOT NULL DEFAULT TRUE",
            "metadata_json": "TEXT NOT NULL DEFAULT '{}'",
        },
        "events": {
            "event_type_id": "VARCHAR(60) NOT NULL DEFAULT ''",
            "report_date": "VARCHAR(20) NOT NULL DEFAULT ''",
            "mud_weight_ppg": "FLOAT",
            "npt_hours": "FLOAT",
            "volume_lost_bbl": "FLOAT",
            "confidence": "FLOAT NOT NULL DEFAULT 0.0",
            "source": "VARCHAR(40) NOT NULL DEFAULT 'synthetic'",
            "is_synthetic": "BOOLEAN NOT NULL DEFAULT TRUE",
            "raw_text": "TEXT NOT NULL DEFAULT ''",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in additions.items():
            if not inspector.has_table(table):
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}'))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
