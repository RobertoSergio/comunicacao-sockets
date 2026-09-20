import argparse
import os
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

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
from suporte.calculadora import calcular

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 6790
BUFFER_SIZE = 4096
MAX_WORKERS = 10
HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 1024 * 1024

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

def process_client(
    connection,
    client_address,
):
    print(
        f"[CONECTADO] "
        f"{client_address[0]}:"
        f"{client_address[1]}"
    )

    with connection:
        while True:
            try:
                data = receive_message(
                    connection
                )

                if data is None:
                    break

                request = (
                    calculadora_pb2.Requisicao()
                )

                request.ParseFromString(
                    data
                )

                print(
                    f"[RECEBIDO] "
                    f"{client_address[0]}:"
                    f"{client_address[1]} "
                    f"-> número={request.numero}, "
                    f"operação={request.operacao}"
                )

                response = (
                    calculadora_pb2.Resposta(
                        numero=request.numero
                    )
                )

                try:
                    response.resultado = calcular(
                        request.operando1,
                        request.operacao,
                        request.operando2,
                    )

                    response.sucesso = True

                except (
                    ZeroDivisionError,
                    ValueError,
                ) as error:

                    response.sucesso = False
                    response.erro = str(error)

                send_message(
                    connection,
                    response,
                )

                print(
                    f"[ENVIADO] "
                    f"{client_address[0]}:"
                    f"{client_address[1]} "
                    f"<- número={response.numero}, "
                    f"sucesso={response.sucesso}"
                )

            except ValueError as error:
                print(
                    f"[ERRO] Mensagem inválida "
                    f"de {client_address}: {error}"
                )
                break

            except (
                ConnectionResetError,
                BrokenPipeError,
            ):
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
        description="Servidor TCP com Protocol Buffers"
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

        print("=" * 60)
        print(
            "Servidor TCP com Protocol Buffers"
        )
        print("=" * 60)
        print(
            f"Endereço: {args.host}"
        )
        print(
            f"Porta: {args.port}"
        )
        print(
            "Aguardando conexões..."
        )
        print(
            "Pressione Ctrl+C para encerrar."
        )
        print()

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            while True:
                connection, client_address = (
                    server.accept()
                )

                executor.submit(
                    process_client,
                    connection,
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