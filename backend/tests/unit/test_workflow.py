import pytest

from app.core.exceptions import ApplicationError
from app.modules.equipment.workflow import (
    ensure_manual_transition,
    ensure_transition,
    manual_transition_options,
)


def test_triage_transition_is_allowed() -> None:
    assert ensure_transition("AGUARDANDO_TRIAGEM", "EM_TRIAGEM") == (
        "AGUARDANDO_TRIAGEM",
        "EM_TRIAGEM",
    )


def test_incompatible_transition_is_blocked() -> None:
    with pytest.raises(ApplicationError, match="Transição incompatível"):
        ensure_transition("RECICLADO", "AGUARDANDO_TRIAGEM")


def test_manual_workflow_exposes_only_valid_next_statuses() -> None:
    assert {item.code for item in manual_transition_options("SEPARADO_REUTILIZACAO")} == {
        "ARMAZENADO",
        "PREPARANDO_REINTRODUCAO",
        "SEPARADO_LEILAO",
    }
    assert ensure_manual_transition(
        "SEPARADO_REUTILIZACAO", "PREPARANDO_REINTRODUCAO"
    ) == ("SEPARADO_REUTILIZACAO", "PREPARANDO_REINTRODUCAO")


def test_triage_transition_cannot_be_executed_manually() -> None:
    with pytest.raises(ApplicationError, match="Transição manual incompatível"):
        ensure_manual_transition("AGUARDANDO_TRIAGEM", "EM_TRIAGEM")
