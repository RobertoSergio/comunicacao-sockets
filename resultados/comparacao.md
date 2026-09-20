# Comparação dos resultados

## Resumo das execuções

| Protocolo | Perda configurada | Tempo total médio (s) | RTT médio (ms) | RTT máximo (ms) | Retransmissões médias | Perdas definitivas |
|---|---:|---:|---:|---:|---:|---:|
| UDP | 0% | 0,00776 | 0,337 | 2,30 | 0,00 | 0/20 |
| UDP | 10% | 1,70649 | 0,600 | 1,35 | 3,33 | 0/20 |
| UDP | 30% | 4,07405 | 0,653 | 1,22 | 8,00 | 0/20 |
| TCP | — | 0,00363 | 0,120 | 0,45 | 0 | 0/20 |
| TCP + Protobuf | — | 0,00456 | 0,140 | 0,40 | 0 | 0/20 |

Os valores de UDP correspondem à média de três execuções para cada taxa de perda, com 20 requisições por execução. TCP e TCP + Protobuf foram executados com 20 requisições.

## Tamanho médio das mensagens

| Formato | Requisição (bytes) | Resposta (bytes) | Total por troca (bytes) |
|---|---:|---:|---:|
| TCP textual | 14,40 | 20,30 | 34,70 |
| TCP + Protobuf | 22,90 | 12,90 | 35,80 |

No experimento realizado, a troca com Protobuf teve média de 35,80 bytes, enquanto a comunicação textual teve média de 34,70 bytes, uma diferença de 1,10 byte por troca, aproximadamente 3,17% a mais para o Protobuf.

## Comparação por cenário

| Cenário | Resultado observado |
|---|---|
| UDP sem perda | 20/20 respostas, sem retransmissões e tempo total médio de 0,00776 s |
| UDP com 10% de perda | 20/20 respostas, média de 3,33 retransmissões e tempo total médio de 1,70649 s |
| UDP com 30% de perda | 20/20 respostas, média de 8 retransmissões e tempo total médio de 4,07405 s |
| TCP textual | 20/20 respostas, tempo total de 0,00363 s e RTT médio de 0,120 ms |
| TCP + Protobuf | 20/20 respostas, tempo total de 0,00456 s e RTT médio de 0,140 ms |

## Observações

- No UDP, o aumento da taxa de perda provocou aumento no número de retransmissões e no tempo total das execuções.
- Mesmo com as perdas simuladas de 10% e 30%, nenhuma requisição foi perdida definitivamente nos testes, pois o cliente realizou retransmissões até receber uma resposta válida ou atingir o limite de tentativas.
- O TCP textual apresentou, nesta execução, tempo total e RTT médio menores que o TCP com Protobuf.
- Quanto ao tamanho das mensagens, o Protobuf não foi menor neste experimento: a média da troca foi de 35,80 bytes, contra 34,70 bytes no formato textual.
- Os resultados são específicos das execuções realizadas no ambiente de teste e não representam necessariamente o comportamento em outros ambientes ou condições de rede.
