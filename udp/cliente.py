import argparse
import os
import random
import socket
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6789
REQUEST_COUNT = 20
TIMEOUT = 0.5
MAX_ATTEMPTS = 5
RESULTS_FILE = "resultados/resultados_udp.md"

def generate_request(sequence_number):
    operand1 = random.randint(1, 100)
    operand2 = random.randint(1, 100)
    operation = random.choice(["+", "-", "*", "/"])

    if operation == "/":
        operand2 = random.randint(1, 100)

    return f"CALC:{sequence_number}:{operand1}:{operation}:{operand2}"

def save_results(
    loss_rate,
    execution,
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

    file_exists = os.path.exists(RESULTS_FILE)

    with open(
        RESULTS_FILE,
        "a",
        encoding="utf-8",
    ) as file:
        if not file_exists or os.path.getsize(RESULTS_FILE) == 0:
            file.write("# Resultados UDP\n\n")

        if execution == 1:
            file.write(
                f"## {loss_rate:.0%} de perda\n\n"
            )

        file.write(
            f"### Execução {execution}\n\n"
        )
        file.write(
            f"- Tempo total: {total_time:.2f} ms\n"
        )
        file.write(
            f"- RTT médio: {average_rtt:.2f} ms\n"
        )
        file.write(
            f"- RTT máximo: {max_rtt:.2f} ms\n"
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

    args = parser.parse_args()

    if not 0.0 <= args.loss_rate <= 1.0:
        parser.error(
            "--loss-rate deve estar entre 0.0 e 1.0"
        )

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    sock.settimeout(TIMEOUT)

    total_start = time.perf_counter()

    total_retransmissions = 0
    permanently_lost = 0
    rtts = []

    print("=" * 60)
    print("Cliente UDP da calculadora")
    print("=" * 60)
    print(f"Servidor: {args.host}:{args.port}")
    print(f"Requisições: {REQUEST_COUNT}")
    print(f"Taxa de perda: {args.loss_rate:.0%}")
    print(f"Execução: {args.execution}")
    print(
        f"Timeout: {TIMEOUT * 1000:.0f} ms"
    )
    print(
        f"Máximo de tentativas: {MAX_ATTEMPTS}"
    )
    print()

    try:
        for sequence_number in range(
            REQUEST_COUNT
        ):
            request = generate_request(
                sequence_number
            )

            attempts = 0
            received = False

            while (
                attempts < MAX_ATTEMPTS
                and not received
            ):
                attempts += 1

                try:
                    start = time.perf_counter()

                    sock.sendto(
                        request.encode("utf-8"),
                        (
                            args.host,
                            args.port,
                        ),
                    )

                    data, _ = sock.recvfrom(4096)

                    end = time.perf_counter()

                    response = (
                        data.decode("utf-8")
                        .strip()
                    )

                    parts = response.split(":")

                    if (
                        len(parts) < 2
                        or parts[1]
                        != str(sequence_number)
                    ):
                        continue

                    rtt = (
                        end - start
                    ) * 1000

                    rtts.append(rtt)

                    print(
                        f"[{sequence_number:02d}] "
                        f"{request} -> "
                        f"{response} | "
                        f"RTT: {rtt:.2f} ms | "
                        f"Tentativas: {attempts}"
                    )

                    received = True

                except (
                    socket.timeout,
                    ConnectionResetError,
                ):
                    if attempts < MAX_ATTEMPTS:
                        total_retransmissions += 1

                        print(
                            f"[{sequence_number:02d}] "
                            f"Timeout na tentativa "
                            f"{attempts}. "
                            f"Retransmitindo..."
                        )

            if not received:
                permanently_lost += 1

                print(
                    f"[{sequence_number:02d}] "
                    f"Requisição perdida após "
                    f"{MAX_ATTEMPTS} tentativas."
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

    finally:
        sock.close()

    total_time = (
        time.perf_counter() - total_start
    ) * 1000

    average_rtt = (
        sum(rtts) / len(rtts)
        if rtts
        else 0
    )

    max_rtt = max(rtts) if rtts else 0

    responses_received = len(rtts)

    print()
    print("=" * 60)
    print("Resumo")
    print("=" * 60)
    print(
        f"Tempo total: {total_time:.2f} ms"
    )
    print(
        f"RTT médio: {average_rtt:.2f} ms"
    )
    print(
        f"RTT máximo: {max_rtt:.2f} ms"
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
        total_time,
        average_rtt,
        max_rtt,
        total_retransmissions,
        permanently_lost,
        responses_received,
    )

if __name__ == "__main__":
    main()