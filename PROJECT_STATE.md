# Estado do projeto

## Versão atual

`0.5.0`

## Última funcionalidade implementada

Gestão completa do inventário e armazenamento temporário estruturado. A interface oferece ações de
adicionar, editar e excluir equipamentos e posições. A exclusão de equipamento é um arquivamento
lógico com justificativa, evento e auditoria. Posições controlam capacidade e podem receber entradas,
transferências e saídas; permanência igual ou superior a 30 dias aparece como alerta operacional.

## Arquivos principais

- `backend/app/modules/storage/`: regras, API, persistência e seed do armazenamento;
- `backend/migrations/versions/20260813_0004_structured_storage.py`: esquema da V0.5;
- `backend/app/modules/equipment/service.py`: edição e arquivamento seguro;
- `frontend/src/features/storage/StoragePage.tsx`: mapa, ocupação e movimentações;
- `frontend/src/features/equipment/EquipmentFormPage.tsx`: criação e edição compartilhadas;
- `frontend/src/features/equipment/EquipmentListPage.tsx`: ações rápidas de editar e excluir;
- `docs/adr/ADR-008-structured-storage-and-safe-delete.md`: decisão arquitetural da V0.5.

## Migrations executadas

- `20260812_0001`: usuários, papéis, permissões, sessões e auditoria;
- `20260812_0002`: catálogos, sequência anual, equipamentos, recolhimentos e eventos;
- `20260812_0003`: critérios, classificações, triagens e respostas;
- `20260813_0004`: arquivamento de equipamentos, posições, ocupações e movimentações.

## Validações executadas

- Ruff: aprovado;
- backend: 27 testes aprovados;
- frontend: 2 testes, TypeScript e build de produção aprovados;
- CRUD, capacidade, entrada, transferência, saída e exclusão segura cobertos por integração;
- migração PostgreSQL, Docker e validação visual executados na entrega da V0.5.

## Decisões arquiteturais

- eventos de rastreabilidade e movimentos físicos são append-only;
- ocupação atual é uma projeção transacional do último movimento;
- capacidade é validada antes de entrada ou transferência;
- posições ocupadas não podem ser desativadas;
- exclusão de equipamento é arquivamento lógico e exige justificativa;
- equipamento armazenado deve registrar saída antes de ser arquivado;
- todas as mutações relevantes registram auditoria e respeitam RBAC;
- permanecem válidas as decisões das versões anteriores em `docs/adr/`.

## Bugs conhecidos e limites

- nenhum bug funcional conhecido após a validação automatizada da V0.5;
- o alerta de permanência usa 30 dias como padrão e pode ser parametrizado pela API;
- o bundle frontend gera aviso de otimização por tamanho, sem impedir a execução;
- rate limiting e bloqueio de tentativas inválidas pertencem à V0.9.

## Tarefas pendentes

- destinação, empresas recicladoras, documentos e remessas;
- KPIs e relatórios gerenciais;
- importação e exportação;
- auditoria e segurança ampliadas.

## Próximo passo

Iniciar a V0.6 com empresas destinatárias, documentos, lotes e remessas, aprovações e comprovantes
de destinação final.
