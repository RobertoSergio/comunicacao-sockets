import argparse
import os
import random
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from suporte.calculadora import processar_requisicao

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 6789
BUFFER_SIZE = 4096
MAX_WORKERS = 10

def process_request(sock, data, client_address, loss_rate):
    try:
        message = data.decode("utf-8").strip()
    except UnicodeDecodeError:
        response = "ERROR:-1:mensagem não está em UTF-8"
    else:
        print(
            f"[RECEBIDO] {client_address[0]}:{client_address[1]} -> {message}"
        )

        if random.random() < loss_rate:
            print(
                f"[PERDIDO] {client_address[0]}:{client_address[1]} "
                "-> nenhuma resposta enviada"
            )
            return

        response = processar_requisicao(message)

    try:
        sock.sendto(
            response.encode("utf-8"),
            client_address,
        )

        print(
            f"[ENVIADO] {client_address[0]}:{client_address[1]} "
            f"<- {response}"
        )
    except OSError as error:
        print(
            f"[ERRO] Não foi possível enviar resposta para "
            f"{client_address}: {error}"
        )

def main():
    parser = argparse.ArgumentParser(
        description="Servidor UDP da calculadora"
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
        "--seed",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    if not 0.0 <= args.loss_rate <= 1.0:
        parser.error(
            "--loss-rate deve estar entre 0.0 e 1.0"
        )

    if args.seed is not None:
        random.seed(args.seed)

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    try:
        sock.bind(
            (
                args.host,
                args.port,
            )
        )

        print("=" * 50)
        print("Servidor UDP da calculadora")
        print("=" * 50)
        print(f"Endereço: {args.host}")
        print(f"Porta: {args.port}")
        print(f"Taxa de perda: {args.loss_rate:.0%}")
        print(
            f"Seed: "
            f"{args.seed if args.seed is not None else 'aleatória'}"
        )
        print("Aguardando requisições...")
        print("Pressione Ctrl+C para encerrar.")
        print()

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            while True:
                data, client_address = sock.recvfrom(
                    BUFFER_SIZE
                )

                executor.submit(
                    process_request,
                    sock,
                    data,
                    client_address,
                    args.loss_rate,
                )

    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")

    except OSError as error:
        print(
            f"[ERRO] Não foi possível iniciar o servidor: "
            f"{error}"
        )
        return 1

    finally:
        sock.close()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())