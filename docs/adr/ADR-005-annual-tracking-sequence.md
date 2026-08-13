# ADR-005 — Sequência anual do código de rastreabilidade

- Status: aceito
- Data: 2026-08-12

## Contexto

Cada equipamento precisa de um identificador curto, legível e estável para consulta, etiqueta e QR
Code. Cadastros simultâneos não podem receber o mesmo número.

## Decisão

Usar o formato `REEE-AAAA-XXXXXX`, reiniciando a parte sequencial a cada ano. O próximo valor é
obtido por uma única operação de `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` no PostgreSQL,
dentro da mesma transação que cria o equipamento e seus eventos.

## Consequências

O código é único e adequado a etiquetas físicas. A sequência pode apresentar lacunas após rollback
ou manutenção, o que é aceitável porque ela identifica itens e não representa contagem contábil.
