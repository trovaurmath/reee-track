from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDefinition:
    code: str
    name: str


PERMISSIONS = (
    PermissionDefinition("system:admin", "Administrar o sistema"),
    PermissionDefinition("user:read", "Consultar usuários"),
    PermissionDefinition("user:create", "Criar usuários"),
    PermissionDefinition("user:update", "Alterar usuários"),
    PermissionDefinition("role:manage", "Gerenciar papéis e permissões"),
    PermissionDefinition("equipment:read", "Consultar equipamentos"),
    PermissionDefinition("equipment:create", "Cadastrar equipamentos"),
    PermissionDefinition("equipment:update", "Alterar equipamentos"),
    PermissionDefinition("equipment:delete", "Excluir equipamentos com preservação do histórico"),
    PermissionDefinition("triage:execute", "Executar triagem"),
    PermissionDefinition("triage:classify", "Classificar equipamentos"),
    PermissionDefinition("workflow:transition", "Executar transições de estado"),
    PermissionDefinition("storage:manage", "Gerenciar armazenamento"),
    PermissionDefinition("destination:manage", "Gerenciar destinações"),
    PermissionDefinition("destination:approve", "Aprovar destinações"),
    PermissionDefinition("shipment:manage", "Gerenciar remessas"),
    PermissionDefinition("report:read", "Consultar e exportar relatórios"),
    PermissionDefinition("audit:read", "Consultar auditoria"),
    PermissionDefinition("configuration:manage", "Gerenciar configurações"),
)

ROLE_DEFINITIONS: dict[str, dict[str, object]] = {
    "ADMINISTRADOR": {
        "name": "Administrador",
        "description": "Acesso integral ao sistema.",
        "permissions": {permission.code for permission in PERMISSIONS},
    },
    "GESTOR": {
        "name": "Gestor",
        "description": "Gestão operacional, relatórios e aprovações.",
        "permissions": {
            "user:read",
            "equipment:read",
            "equipment:create",
            "equipment:update",
            "equipment:delete",
            "triage:execute",
            "triage:classify",
            "workflow:transition",
            "storage:manage",
            "destination:manage",
            "destination:approve",
            "shipment:manage",
            "report:read",
            "audit:read",
        },
    },
    "TRIAGEM": {
        "name": "Triagem",
        "description": "Execução de triagem e avaliação técnica.",
        "permissions": {
            "equipment:read",
            "triage:execute",
            "triage:classify",
            "workflow:transition",
        },
    },
    "OPERADOR": {
        "name": "Operador",
        "description": "Cadastro e movimentação de equipamentos.",
        "permissions": {
            "equipment:read",
            "equipment:create",
            "equipment:update",
            "workflow:transition",
            "storage:manage",
        },
    },
    "AUDITOR": {
        "name": "Auditor",
        "description": "Consulta de equipamentos, histórico, auditoria e relatórios.",
        "permissions": {
            "equipment:read",
            "report:read",
            "audit:read",
        },
    },
}
