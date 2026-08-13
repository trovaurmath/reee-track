from app.core.database import SessionLocal
from app.modules.equipment.repository import next_sequence_value


def test_sequence_is_scoped_by_namespace_and_year(database) -> None:
    del database
    with SessionLocal() as session:
        first = next_sequence_value(session, "UNIT_TEST", 2030)
        second = next_sequence_value(session, "UNIT_TEST", 2030)
        another_year = next_sequence_value(session, "UNIT_TEST", 2031)
        session.rollback()

    assert (first, second, another_year) == (1, 2, 1)

