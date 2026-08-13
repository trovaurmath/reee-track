# ADR-007 — Rastreabilidade operacional e transições manuais

## Status

Aceita em 12/08/2026.

## Contexto

Os eventos de cadastro e triagem já eram append-only, mas a equipe não possuía uma visão global do
histórico nem um caso de uso seguro para registrar ocorrências e avançar etapas posteriores à
classificação. Alterar diretamente `current_status` comprometeria a rastreabilidade.

## Decisão

- manter `equipment_events` como livro append-only e `equipments.current_status` como projeção atual;
- executar projeção, evento e auditoria na mesma transação;
- separar transições manuais das transições internas do caso de uso de triagem;
- expor ao frontend apenas os próximos estados compatíveis com a situação atual;
- registrar notas operacionais como eventos sem alterar o estado;
- consolidar eventos de todos os equipamentos em um feed paginado e pesquisável.

## Consequências

O histórico permanece íntegro e as operações ficam explícitas para auditoria. A V0.5 poderá anexar
entidades estruturadas de armazenamento aos eventos sem alterar o contrato central de
rastreabilidade. Eventos existentes continuam válidos e nenhuma migration adicional é necessária.
