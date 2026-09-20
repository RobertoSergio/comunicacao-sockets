import argparse
import os
import random
import socket
import sys
import time

ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    ROOT_DIR,
)

from proto import calculadora_pb2

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6790
REQUEST_COUNT = 20
BUFFER_SIZE = 4096
HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 1024 * 1024
RESULTS_FILE = os.path.join(
    ROOT_DIR,
    "resultados",
    "resultados_proto.md",
)

def generate_request(
    sequence_number,
):
    operand1 = random.randint(
        1,
        100,
    )

    operand2 = random.randint(
        1,
        100,
    )

    operation = random.choice(
        ["+", "-", "*", "/"]
    )

    if operation == "/":
        operand2 = random.randint(
            1,
            100,
        )

    return calculadora_pb2.Requisicao(
        numero=sequence_number,
        operando1=operand1,
        operacao=operation,
        operando2=operand2,
    )

def receive_message(connection):
    header = bytearray()

    while len(header) < HEADER_SIZE:
        data = connection.recv(
            HEADER_SIZE - len(header)
        )

        if not data:
            return None

        header.extend(data)

    message_size = int.from_bytes(
        header,
        byteorder="big",
    )

    if (
        message_size <= 0
        or message_size > MAX_MESSAGE_SIZE
    ):
        raise ValueError(
            "tamanho de mensagem inválido"
        )

    message = bytearray()

    while len(message) < message_size:
        data = connection.recv(
            min(
                BUFFER_SIZE,
                message_size - len(message),
            )
        )

        if not data:
            return None

        message.extend(data)

    return bytes(message)

def send_message(
    connection,
    message,
):
    data = message.SerializeToString()

    size = len(data).to_bytes(
        HEADER_SIZE,
        byteorder="big",
    )

    connection.sendall(
        size + data
    )

    return len(data)

def save_results(
    execution,
    seed,
    total_time,
    average_rtt,
    max_rtt,
    average_request_size,
    average_response_size,
    average_exchange_size,
    responses_received,
):
    os.makedirs(
        os.path.dirname(RESULTS_FILE),
        exist_ok=True,
    )

    with open(
        RESULTS_FILE,
        "a",
        encoding="utf-8",
    ) as file:

        if os.path.getsize(
            RESULTS_FILE
        ) == 0:
            file.write(
                "# Resultados TCP com Protocol Buffers\n\n"
            )

        file.write(
            f"## Execução {execution}\n\n"
        )

        file.write(
            f"- Seed: {seed}\n"
        )

        file.write(
            f"- Tempo total: "
            f"{total_time:.2f} ms\n"
        )

        file.write(
            f"- RTT médio: "
            f"{average_rtt:.2f} ms\n"
        )

        file.write(
            f"- RTT máximo: "
            f"{max_rtt:.2f} ms\n"
        )

        file.write(
            f"- Tamanho médio da requisição: "
            f"{average_request_size:.2f} bytes\n"
        )

        file.write(
            f"- Tamanho médio da resposta: "
            f"{average_response_size:.2f} bytes\n"
        )

        file.write(
            f"- Tamanho médio da troca: "
            f"{average_exchange_size:.2f} bytes\n"
        )

        file.write(
            f"- Respostas recebidas: "
            f"{responses_received}/"
            f"{REQUEST_COUNT}\n\n"
        )

def main():
    parser = argparse.ArgumentParser(
        description="Cliente TCP com Protocol Buffers"
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
    )

    parser.add_argument(
        "--execution",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(
            args.seed
        )

    total_start = time.perf_counter()

    rtts = []
    request_sizes = []
    response_sizes = []

    print("=" * 60)
    print(
        "Cliente TCP com Protocol Buffers"
    )
    print("=" * 60)
    print(
        f"Servidor: "
        f"{args.host}:{args.port}"
    )
    print(
        f"Requisições: "
        f"{REQUEST_COUNT}"
    )
    print(
        f"Execução: "
        f"{args.execution}"
    )
    print(
        f"Seed: "
        f"{args.seed if args.seed is not None else 'aleatória'}"
    )
    print()

    try:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as sock:

            sock.connect(
                (
                    args.host,
                    args.port,
                )
            )

            for sequence_number in range(
                REQUEST_COUNT
            ):
                request = generate_request(
                    sequence_number
                )

                start = time.perf_counter()

                request_size = send_message(
                    sock,
                    request,
                )

                data = receive_message(
                    sock
                )

                end = time.perf_counter()

                if data is None:
                    raise ConnectionResetError(
                        "Conexão encerrada pelo servidor."
                    )

                response = (
                    calculadora_pb2.Resposta()
                )

                response.ParseFromString(
                    data
                )

                if (
                    response.numero
                    != sequence_number
                ):
                    raise ValueError(
                        "número de sequência inesperado"
                    )

                rtt = (
                    end - start
                ) * 1000

                response_size = len(
                    data
                )

                rtts.append(
                    rtt
                )

                request_sizes.append(
                    request_size
                )

                response_sizes.append(
                    response_size
                )

                result = (
                    response.resultado
                    if response.sucesso
                    else response.erro
                )

                print(
                    f"[{sequence_number:02d}] "
                    f"{request.operando1} "
                    f"{request.operacao} "
                    f"{request.operando2} -> "
                    f"{result} | "
                    f"RTT: {rtt:.2f} ms | "
                    f"Requisição: "
                    f"{request_size} bytes | "
                    f"Resposta: "
                    f"{response_size} bytes"
                )

    except ConnectionRefusedError:
        print(
            f"[ERRO] Não foi possível conectar "
            f"ao servidor "
            f"{args.host}:{args.port}."
        )
        return 1

    except (
        ConnectionResetError,
        ValueError,
    ) as error:
        print(
            f"[ERRO] {error}"
        )
        return 1

    except OSError as error:
        print(
            f"[ERRO] Falha na comunicação: "
            f"{error}"
        )
        return 1

    total_time = (
        time.perf_counter()
        - total_start
    ) * 1000

    average_rtt = (
        sum(rtts) / len(rtts)
        if rtts
        else 0
    )

    max_rtt = (
        max(rtts)
        if rtts
        else 0
    )

    average_request_size = (
        sum(request_sizes)
        / len(request_sizes)
        if request_sizes
        else 0
    )

    average_response_size = (
        sum(response_sizes)
        / len(response_sizes)
        if response_sizes
        else 0
    )

    average_exchange_size = (
        average_request_size
        + average_response_size
    )

    responses_received = len(
        rtts
    )

    print()
    print("=" * 60)
    print("Resumo")
    print("=" * 60)
    print(
        f"Tempo total: "
        f"{total_time:.2f} ms"
    )
    print(
        f"RTT médio: "
        f"{average_rtt:.2f} ms"
    )
    print(
        f"RTT máximo: "
        f"{max_rtt:.2f} ms"
    )
    print(
        f"Tamanho médio da requisição: "
        f"{average_request_size:.2f} bytes"
    )
    print(
        f"Tamanho médio da resposta: "
        f"{average_response_size:.2f} bytes"
    )
    print(
        f"Tamanho médio da troca: "
        f"{average_exchange_size:.2f} bytes"
    )
    print(
        f"Respostas recebidas: "
        f"{responses_received}/"
        f"{REQUEST_COUNT}"
    )

    save_results(
        args.execution,
        args.seed,
        total_time,
        average_rtt,
        max_rtt,
        average_request_size,
        average_response_size,
        average_exchange_size,
        responses_received,
    )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())