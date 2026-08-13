from dataclasses import dataclass

from app.core.exceptions import ApplicationError


@dataclass(frozen=True)
class StatusDefinition:
    code: str
    label: str
    stage: str
    terminal: bool = False


STATUS_DEFINITIONS = (
    StatusDefinition("RECOLHIDO", "Recolhido", "Entrada"),
    StatusDefinition("CADASTRADO", "Cadastrado", "Entrada"),
    StatusDefinition("AGUARDANDO_TRIAGEM", "Aguardando triagem", "Triagem"),
    StatusDefinition("EM_TRIAGEM", "Em triagem", "Triagem"),
    StatusDefinition("AGUARDANDO_AVALIACAO", "Aguardando avaliação", "Triagem"),
    StatusDefinition("AGUARDANDO_DESTINACAO", "Aguardando destinação", "Destinação"),
    StatusDefinition("ARMAZENADO", "Armazenado", "Armazenamento"),
    StatusDefinition("SEPARADO_REUTILIZACAO", "Separado para reutilização", "Reutilização"),
    StatusDefinition("PREPARANDO_REINTRODUCAO", "Preparando reintrodução", "Reutilização"),
    StatusDefinition("REINTRODUZIDO", "Reintroduzido", "Reutilização"),
    StatusDefinition("SEPARADO_LEILAO", "Separado para leilão", "Leilão"),
    StatusDefinition("EM_LEILAO", "Em leilão", "Leilão"),
    StatusDefinition("LEILOADO", "Leiloado", "Leilão"),
    StatusDefinition("AGUARDANDO_RECICLAGEM", "Aguardando reciclagem", "Reciclagem"),
    StatusDefinition("ENVIADO_RECICLAGEM", "Enviado para reciclagem", "Reciclagem"),
    StatusDefinition("RECICLADO", "Reciclado", "Reciclagem"),
    StatusDefinition("DESCARTADO", "Descartado", "Destinação"),
    StatusDefinition("FINALIZADO", "Finalizado", "Encerramento", terminal=True),
)

STATUS_BY_CODE = {definition.code: definition for definition in STATUS_DEFINITIONS}
EQUIPMENT_STATUSES = frozenset(STATUS_BY_CODE)

TRIAGE_STARTABLE_STATUSES = frozenset({"AGUARDANDO_TRIAGEM", "AGUARDANDO_AVALIACAO"})
TRIAGE_RESULT_STATUSES = frozenset(
    {
        "AGUARDANDO_AVALIACAO",
        "AGUARDANDO_DESTINACAO",
        "SEPARADO_REUTILIZACAO",
        "AGUARDANDO_RECICLAGEM",
    }
)

# Transições executadas exclusivamente pelos casos de uso da triagem.
TRIAGE_TRANSITIONS: dict[str, frozenset[str]] = {
    "AGUARDANDO_TRIAGEM": frozenset({"EM_TRIAGEM"}),
    "AGUARDANDO_AVALIACAO": frozenset({"EM_TRIAGEM"}),
    "EM_TRIAGEM": TRIAGE_RESULT_STATUSES | {"AGUARDANDO_TRIAGEM"},
}

# Transições operacionais da V0.4. Os módulos especializados de armazenamento e
# destinação passarão a anexar dados estruturados a essas mudanças nas V0.5/V0.6.
MANUAL_TRANSITIONS: dict[str, frozenset[str]] = {
    "AGUARDANDO_DESTINACAO": frozenset({"ARMAZENADO", "DESCARTADO"}),
    "ARMAZENADO": frozenset(
        {"AGUARDANDO_DESTINACAO", "SEPARADO_REUTILIZACAO", "AGUARDANDO_RECICLAGEM"}
    ),
    "SEPARADO_REUTILIZACAO": frozenset(
        {"PREPARANDO_REINTRODUCAO", "SEPARADO_LEILAO", "ARMAZENADO"}
    ),
    "PREPARANDO_REINTRODUCAO": frozenset({"REINTRODUZIDO"}),
    "REINTRODUZIDO": frozenset({"FINALIZADO"}),
    "SEPARADO_LEILAO": frozenset({"EM_LEILAO"}),
    "EM_LEILAO": frozenset({"LEILOADO", "SEPARADO_LEILAO"}),
    "LEILOADO": frozenset({"FINALIZADO"}),
    "AGUARDANDO_RECICLAGEM": frozenset({"ARMAZENADO", "ENVIADO_RECICLAGEM"}),
    "ENVIADO_RECICLAGEM": frozenset({"RECICLADO"}),
    "RECICLADO": frozenset({"FINALIZADO"}),
    "DESCARTADO": frozenset({"FINALIZADO"}),
    "FINALIZADO": frozenset(),
}

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    **TRIAGE_TRANSITIONS,
    **MANUAL_TRANSITIONS,
}


def ensure_known_status(status: str) -> str:
    normalized = status.strip().upper()
    if normalized not in EQUIPMENT_STATUSES:
        raise ApplicationError(f"Status de equipamento desconhecido: {normalized}")
    return normalized


def ensure_transition(previous_status: str, new_status: str) -> tuple[str, str]:
    previous = ensure_known_status(previous_status)
    new = ensure_known_status(new_status)
    if new not in ALLOWED_TRANSITIONS.get(previous, frozenset()):
        raise ApplicationError(f"Transição incompatível: {previous} → {new}")
    return previous, new


def ensure_manual_transition(previous_status: str, new_status: str) -> tuple[str, str]:
    previous = ensure_known_status(previous_status)
    new = ensure_known_status(new_status)
    if new not in MANUAL_TRANSITIONS.get(previous, frozenset()):
        raise ApplicationError(f"Transição manual incompatível: {previous} → {new}")
    return previous, new


def manual_transition_options(status: str) -> tuple[StatusDefinition, ...]:
    normalized = ensure_known_status(status)
    return tuple(
        STATUS_BY_CODE[code]
        for code in sorted(
            MANUAL_TRANSITIONS.get(normalized, frozenset()),
            key=lambda item: STATUS_BY_CODE[item].label,
        )
    )


def ensure_triage_result_status(status: str) -> str:
    normalized = ensure_known_status(status)
    if normalized not in TRIAGE_RESULT_STATUSES:
        raise ApplicationError("O status de destino não é válido para uma classificação de triagem")
    return normalized
