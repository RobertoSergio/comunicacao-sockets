import argparse
import os
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

def handle_client(conn, client_address):
    print(
        f"[CONECTADO] "
        f"{client_address[0]}:{client_address[1]}"
    )

    buffer = b""

    with conn:
        while True:
            try:
                data = conn.recv(
                    BUFFER_SIZE
                )

                if not data:
                    break

                buffer += data

                while b"\n" in buffer:
                    (
                        message_data,
                        _,
                        buffer,
                    ) = buffer.partition(b"\n")

                    message = (
                        message_data
                        .decode("utf-8")
                        .strip()
                    )

                    if not message:
                        continue

                    print(
                        f"[RECEBIDO] "
                        f"{client_address[0]}:"
                        f"{client_address[1]} -> "
                        f"{message}"
                    )

                    response = processar_requisicao(
                        message
                    )

                    conn.sendall(
                        (
                            response + "\n"
                        ).encode("utf-8")
                    )

                    print(
                        f"[ENVIADO] "
                        f"{client_address[0]}:"
                        f"{client_address[1]} <- "
                        f"{response}"
                    )

            except UnicodeDecodeError:
                try:
                    conn.sendall(
                        b"ERROR:-1:mensagem nao esta em UTF-8\n"
                    )
                except OSError:
                    pass

                break

            except ConnectionResetError:
                print(
                    f"[DESCONECTADO] "
                    f"{client_address[0]}:"
                    f"{client_address[1]}"
                )
                break

            except OSError as error:
                print(
                    f"[ERRO] Comunicação com "
                    f"{client_address}: {error}"
                )
                break

    print(
        f"[ENCERRADO] "
        f"{client_address[0]}:"
        f"{client_address[1]}"
    )

def main():
    parser = argparse.ArgumentParser(
        description="Servidor TCP da calculadora"
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

    args = parser.parse_args()

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    try:
        server.bind(
            (
                args.host,
                args.port,
            )
        )

        server.listen()

        print("=" * 50)
        print("Servidor TCP da calculadora")
        print("=" * 50)
        print(f"Endereço: {args.host}")
        print(f"Porta: {args.port}")
        print("Aguardando conexões...")
        print("Pressione Ctrl+C para encerrar.")
        print()

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            while True:
                conn, client_address = (
                    server.accept()
                )

                executor.submit(
                    handle_client,
                    conn,
                    client_address,
                )

    except KeyboardInterrupt:
        print(
            "\nServidor encerrado pelo usuário."
        )

    except OSError as error:
        print(
            f"[ERRO] Não foi possível iniciar "
            f"o servidor: {error}"
        )
        return 1

    finally:
        server.close()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())