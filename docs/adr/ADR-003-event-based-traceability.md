# ADR-003 — Rastreabilidade baseada em eventos

- Status: aceito
- Data: 2026-08-12

## Contexto

Substituir apenas o estado atual destruiria a capacidade de reconstruir o percurso de um equipamento.

## Decisão

Cada fato relevante gerará um evento append-only. O equipamento manterá também uma projeção do estado
atual para consultas eficientes. Isso não constitui Event Sourcing integral.

## Consequências

O histórico poderá ser reconstruído e auditado. Atualização da projeção e inserção do evento precisarão
ocorrer na mesma transação.

