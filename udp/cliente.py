import argparse
import os
import random
import socket
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from suporte.mensagens import validar_resposta

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6789
REQUEST_COUNT = 20
TIMEOUT = 0.5
MAX_ATTEMPTS = 5
BUFFER_SIZE = 4096
RESULTS_FILE = os.path.join(
    ROOT_DIR,
    "resultados",
    "resultados_udp.md",
)

def generate_request(sequence_number):
    operand1 = random.randint(1, 100)
    operand2 = random.randint(1, 100)
    operation = random.choice(
        ["+", "-", "*", "/"]
    )

    if operation == "/":
        operand2 = random.randint(1, 100)

    return (
        f"CALC:{sequence_number}:"
        f"{operand1}:{operation}:{operand2}"
    )

def enviar_com_retentativas(
    sock,
    request,
    address,
    sequence_number,
    timeout,
    max_attempts,
):
    sock.settimeout(timeout)

    retransmissions = 0

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            start = time.perf_counter()

            sock.sendto(
                request.encode("utf-8"),
                address,
            )

            data, _ = sock.recvfrom(
                BUFFER_SIZE
            )

            end = time.perf_counter()

            response = data.decode(
                "utf-8"
            ).strip()

            validar_resposta(
                response,
                sequence_number,
            )

            return (
                (end - start) * 1000,
                attempt,
                retransmissions,
                response,
            )

        except socket.timeout:
            if attempt < max_attempts:
                retransmissions += 1

        except (
            ConnectionResetError,
            ValueError,
        ):
            if attempt < max_attempts:
                retransmissions += 1

    return (
        None,
        max_attempts,
        retransmissions,
        None,
    )

def save_results(
    loss_rate,
    execution,
    seed,
    total_time,
    average_rtt,
    max_rtt,
    total_retransmissions,
    permanently_lost,
    responses_received,
):
    os.makedirs(
        os.path.dirname(RESULTS_FILE),
        exist_ok=True,
    )

    needs_header = (
        not os.path.exists(RESULTS_FILE)
        or os.path.getsize(RESULTS_FILE) == 0
    )

    with open(
        RESULTS_FILE,
        "a",
        encoding="utf-8",
    ) as file:

        if needs_header:
            file.write(
                "# Resultados UDP\n\n"
            )

        file.write(
            f"## {loss_rate:.0%} de perda\n\n"
        )

        file.write(
            f"### Execução {execution}\n\n"
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
            f"- Retransmissões: "
            f"{total_retransmissions}\n"
        )

        file.write(
            f"- Perdidas permanentemente: "
            f"{permanently_lost}\n"
        )

        file.write(
            f"- Respostas recebidas: "
            f"{responses_received}/{REQUEST_COUNT}\n\n"
        )

def main():
    parser = argparse.ArgumentParser(
        description="Cliente UDP da calculadora"
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
        "--loss-rate",
        type=float,
        default=0.0,
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

    parser.add_argument(
        "--timeout",
        type=float,
        default=TIMEOUT,
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=MAX_ATTEMPTS,
    )

    args = parser.parse_args()

    if not 0.0 <= args.loss_rate <= 1.0:
        parser.error(
            "--loss-rate deve estar entre 0.0 e 1.0"
        )

    if args.timeout <= 0:
        parser.error(
            "--timeout deve ser maior que zero"
        )

    if args.max_attempts <= 0:
        parser.error(
            "--max-attempts deve ser maior que zero"
        )

    if args.seed is not None:
        random.seed(args.seed)

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    total_start = time.perf_counter()
    total_retransmissions = 0
    permanently_lost = 0
    rtts = []

    print("=" * 60)
    print("Cliente UDP da calculadora")
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
        f"Taxa de perda: "
        f"{args.loss_rate:.0%}"
    )
    print(
        f"Execução: "
        f"{args.execution}"
    )
    print(
        f"Seed: "
        f"{args.seed if args.seed is not None else 'aleatória'}"
    )
    print(
        f"Timeout: "
        f"{args.timeout * 1000:.0f} ms"
    )
    print(
        f"Máximo de tentativas: "
        f"{args.max_attempts}"
    )
    print()

    try:
        for sequence_number in range(
            REQUEST_COUNT
        ):
            request = generate_request(
                sequence_number
            )

            (
                rtt,
                attempts,
                retransmissions,
                response,
            ) = enviar_com_retentativas(
                sock,
                request,
                (
                    args.host,
                    args.port,
                ),
                sequence_number,
                args.timeout,
                args.max_attempts,
            )

            total_retransmissions += (
                retransmissions
            )

            if response is not None:
                rtts.append(rtt)

                print(
                    f"[{sequence_number:02d}] "
                    f"{request} -> {response} | "
                    f"RTT: {rtt:.2f} ms | "
                    f"Tentativas: {attempts}"
                )
            else:
                permanently_lost += 1

                print(
                    f"[{sequence_number:02d}] "
                    f"Requisição perdida após "
                    f"{args.max_attempts} tentativas."
                )

    except KeyboardInterrupt:
        print(
            "\nCliente encerrado pelo usuário."
        )

    except OSError as error:
        print(
            f"[ERRO] Falha na comunicação: "
            f"{error}"
        )
        return 1

    finally:
        sock.close()

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

    responses_received = len(rtts)

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
        f"Retransmissões: "
        f"{total_retransmissions}"
    )
    print(
        f"Perdidas permanentemente: "
        f"{permanently_lost}"
    )
    print(
        f"Respostas recebidas: "
        f"{responses_received}/{REQUEST_COUNT}"
    )

    save_results(
        args.loss_rate,
        args.execution,
        args.seed,
        total_time,
        average_rtt,
        max_rtt,
        total_retransmissions,
        permanently_lost,
        responses_received,
    )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())