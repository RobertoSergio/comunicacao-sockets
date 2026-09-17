import argparse
import random
import socket
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6789
REQUEST_COUNT = 20


def generate_request(sequence_number):
    operand1 = random.randint(1, 100)
    operand2 = random.randint(1, 100)
    operation = random.choice(["+", "-", "*", "/"])

    if operation == "/":
        operand2 = random.randint(1, 100)

    return f"CALC:{sequence_number}:{operand1}:{operation}:{operand2}"


def main():
    parser = argparse.ArgumentParser(
        description="Cliente TCP da calculadora"
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)

    args = parser.parse_args()

    total_start = time.perf_counter()
    rtts = []

    print("=" * 60)
    print("Cliente TCP da calculadora")
    print("=" * 60)
    print(f"Servidor: {args.host}:{args.port}")
    print(f"Requisições: {REQUEST_COUNT}")
    print()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((args.host, args.port))

            for sequence_number in range(REQUEST_COUNT):
                request = generate_request(sequence_number)

                start = time.perf_counter()

                sock.sendall(request.encode("utf-8"))

                data = sock.recv(4096)

                end = time.perf_counter()

                response = data.decode("utf-8").strip()

                parts = response.split(":")

                if len(parts) < 2 or parts[1] != str(sequence_number):
                    print(
                        f"[{sequence_number:02d}] "
                        f"Resposta inválida: {response}"
                    )
                    continue

                rtt = (end - start) * 1000
                rtts.append(rtt)

                print(
                    f"[{sequence_number:02d}] "
                    f"{request} -> {response} | "
                    f"RTT: {rtt:.2f} ms"
                )

    except ConnectionRefusedError:
        print(
            f"[ERRO] Não foi possível conectar ao servidor "
            f"{args.host}:{args.port}."
        )

    except ConnectionResetError:
        print("[ERRO] A conexão foi encerrada pelo servidor.")

    except OSError as error:
        print(f"[ERRO] Falha na comunicação: {error}")

    total_time = (time.perf_counter() - total_start) * 1000
    average_rtt = sum(rtts) / len(rtts) if rtts else 0
    max_rtt = max(rtts) if rtts else 0

    print()
    print("=" * 60)
    print("Resumo")
    print("=" * 60)
    print(f"Tempo total: {total_time:.2f} ms")
    print(f"RTT médio: {average_rtt:.2f} ms")
    print(f"RTT máximo: {max_rtt:.2f} ms")
    print(f"Respostas recebidas: {len(rtts)}/{REQUEST_COUNT}")


if __name__ == "__main__":
    main()