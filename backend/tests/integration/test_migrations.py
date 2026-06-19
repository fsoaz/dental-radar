from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


def test_all_tables_exist(migrated_engine):
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())
    expected = {
        "clinic",
        "location",
        "signal",
        "score",
        "enrichment",
        "scoring_config",
        "app_user",
        "alembic_version",
    }
    assert expected.issubset(tables)


def test_scoring_config_v1_seeded(migrated_engine):
    with Session(migrated_engine) as session:
        result = session.execute(
            text("SELECT version, active, weights FROM scoring_config WHERE active = true")
        ).one()
        version, active, weights = result
        assert version == 1
        assert active is True
        assert weights == {
            "HIRING": 25,
            "ADVERTISING": 30,
            "WEBSITE_QUALITY": 15,
            "MULTI_LOCATION": 40,
            "HIGH_TICKET": 20,
        }

        active_count = session.execute(
            text("SELECT COUNT(*) FROM scoring_config WHERE active = true")
        ).scalar_one()
        assert active_count == 1
