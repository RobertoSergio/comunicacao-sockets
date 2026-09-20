# Comunicação com Sockets: UDP vs. TCP

Projeto desenvolvido para a disciplina de Sistemas Distribuídos, com o objetivo de implementar e comparar comunicação cliente-servidor utilizando UDP, TCP e Protocol Buffers.

## Estrutura do projeto

```text
comunicacao-sockets/
├── proto/
│   ├── calculadora.proto
│   └── calculadora_pb2.py
├── proto_tcp/
│   ├── cliente.py
│   └── servidor.py
├── udp/
│   ├── cliente.py
│   └── servidor.py
├── tcp/
│   ├── cliente.py
│   └── servidor.py
├── resultados/
│   ├── resultados_udp.md
│   ├── resultados_tcp.md
│   └── resultados_proto.md
├── testes/
│   ├── testes.py
│   ├── test_calculadora.py
│   ├── test_integracao.py
│   └── test_udp.py
├── README.md
├── requirements.txt
└── .gitignore
```

## Requisitos

- Python 3.14 ou superior
- Protocol Buffers (`protoc`)
- Biblioteca Python `protobuf`

## Instalação

Clone o repositório:

```powershell
git clone https://github.com/RobertoSergio/comunicacao-sockets.git
cd comunicacao-sockets
```

Crie o ambiente virtual:

```powershell
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

## Protocol Buffers

O arquivo de definição está em:

```text
proto/calculadora.proto
```

Para gerar o código Python:

```powershell
protoc --python_out=proto proto/calculadora.proto
```

Esse comando gera o arquivo:

```text
proto/calculadora_pb2.py
```

## Protocolo de comunicação

As implementações UDP e TCP utilizam mensagens textuais.

### Requisição

```text
CALC:<n>:<operando1>:<op>:<operando2>
```

Exemplo:

```text
CALC:0:10:+:5
```

### Resposta

```text
RESULT:<n>:<resultado>
```

Exemplo:

```text
RESULT:0:15.0
```

### Erro

```text
ERROR:<n>:<mensagem de erro>
```

Exemplo:

```text
ERROR:1:divisão por zero
```

São suportadas as operações:

```text
+
-
*
/
```

Os operandos podem ser números inteiros ou decimais.

## UDP

O servidor UDP permite definir a taxa de perda simulada.

Para executar o servidor sem perda:

```powershell
python udp/servidor.py --port 6789 --loss-rate 0.0
```

Exemplo com 30% de perda:

```powershell
python udp/servidor.py --port 6789 --loss-rate 0.3
```

Em outro terminal, execute o cliente:

```powershell
python udp/cliente.py --port 6789 --loss-rate 0.0 --execution 1 --seed 2026
```

O cliente realiza 20 requisições, mede o RTT e utiliza timeout de 500 ms e até 5 tentativas por requisição.

Os resultados são armazenados em:

```text
resultados/resultados_udp.md
```

## TCP

Inicie o servidor:

```powershell
python tcp/servidor.py --port 6789
```

Em outro terminal, execute o cliente:

```powershell
python tcp/cliente.py --port 6789 --execution 1 --seed 2026
```

O cliente realiza 20 requisições e registra o RTT e o tamanho das mensagens.

Os resultados são armazenados em:

```text
resultados/resultados_tcp.md
```

## TCP com Protocol Buffers

O servidor utiliza Protocol Buffers para serializar as mensagens.

Inicie o servidor:

```powershell
python proto_tcp/servidor.py --port 6790
```

Em outro terminal, execute o cliente:

```powershell
python proto_tcp/cliente.py --port 6790 --execution 1 --seed 2026
```

Os resultados são armazenados em:

```text
resultados/resultados_proto.md
```

## Execução dos experimentos

Para executar automaticamente todos os experimentos:

```powershell
python testes/testes.py
```

O script realiza:

- 3 execuções UDP com 0% de perda;
- 3 execuções UDP com 10% de perda;
- 3 execuções UDP com 30% de perda;
- 1 execução TCP;
- 1 execução TCP com Protocol Buffers.

Cada execução UDP utiliza 20 requisições.

A seed utilizada para gerar o conjunto de requisições é:

```text
2026
```

Os resultados são salvos automaticamente na pasta:

```text
resultados/
```

## Testes automatizados

Para executar os testes:

```powershell
python -m unittest discover -s testes -p "test_*.py" -v
```

Os testes verificam as operações da calculadora, a validação das mensagens, as retransmissões UDP e o atendimento simultâneo dos servidores.

## Resultados

Os resultados experimentais são separados por implementação:

```text
resultados/resultados_udp.md
resultados/resultados_tcp.md
resultados/resultados_proto.md
```

### UDP

São registrados:

- tempo total;
- RTT médio;
- RTT máximo;
- número de retransmissões;
- número de perdas permanentes;
- quantidade de respostas recebidas.

### TCP

São registrados:

- tempo total;
- RTT médio;
- RTT máximo;
- tamanho médio das requisições;
- tamanho médio das respostas;
- quantidade de respostas recebidas.

### Protocol Buffers

São registrados:

- tempo total;
- RTT médio;
- RTT máximo;
- tamanho médio das requisições;
- tamanho médio das respostas;
- tamanho médio da troca;
- quantidade de respostas recebidas.

## Comparação

A comparação entre UDP e TCP considera principalmente o comportamento diante da perda de mensagens.

No UDP, a aplicação implementa timeout e retransmissão para lidar com respostas que não chegam. A taxa de perda simulada é alterada durante os experimentos para observar seu impacto no tempo total e na quantidade de retransmissões.

No TCP, a aplicação não implementa retransmissões próprias. A confiabilidade da comunicação é fornecida pelo próprio protocolo.

A implementação com Protocol Buffers utiliza TCP, mas substitui a representação textual das mensagens por uma representação binária.

## Tecnologias utilizadas

- Python
- Sockets
- UDP
- TCP
- Protocol Buffers
- `unittest`