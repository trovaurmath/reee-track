# ADR-008 — Armazenamento estruturado e exclusão segura

## Status

Aceita em 13 de agosto de 2026.

## Contexto

A operação precisa localizar fisicamente cada equipamento, controlar a capacidade do depósito e
remover cadastros incorretos sem destruir o histórico obrigatório de rastreabilidade.

## Decisão

- posições são endereços estruturados por depósito, corredor, estante, prateleira e posição;
- a ocupação atual é uma projeção com no máximo uma posição por equipamento;
- entradas, transferências e saídas são movimentos append-only e também geram eventos do equipamento;
- posições ocupadas não podem ser excluídas; a exclusão apenas as torna inativas;
- equipamentos são excluídos por arquivamento lógico, com justificativa, ator, data, evento e auditoria;
- equipamentos armazenados devem registrar saída antes do arquivamento;
- alertas de permanência são calculados pela data da última entrada ou transferência.

## Consequências

O sistema preserva evidências e impede posições superlotadas. Consultas operacionais continuam
simples por usarem projeções atuais, enquanto auditorias conseguem reconstruir todas as mudanças.
A remoção física de registros deixa de fazer parte dos fluxos normais da aplicação.
