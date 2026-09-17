import argparse
import socket
from concurrent.futures import ThreadPoolExecutor

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 6789
BUFFER_SIZE = 4096
MAX_WORKERS = 10


def parse_request(message):
    parts = message.split(":")

    if len(parts) != 5:
        raise ValueError(
            "formato inválido; esperado CALC:<n>:<operando1>:<op>:<operando2>"
        )

    if parts[0] != "CALC":
        raise ValueError("comando inválido; esperado CALC")

    try:
        sequence_number = int(parts[1])
    except ValueError:
        raise ValueError("número de sequência inválido")

    try:
        operand1 = float(parts[2])
        operand2 = float(parts[4])
    except ValueError:
        raise ValueError("operando inválido")

    operation = parts[3]

    if operation not in {"+", "-", "*", "/"}:
        raise ValueError("operação inválida; use +, -, * ou /")

    return sequence_number, operand1, operation, operand2


def calculate(operand1, operation, operand2):
    if operation == "+":
        return operand1 + operand2

    if operation == "-":
        return operand1 - operand2

    if operation == "*":
        return operand1 * operand2

    if operation == "/":
        if operand2 == 0:
            raise ZeroDivisionError("divisão por zero")
        return operand1 / operand2

    raise ValueError("operação inválida")


def process_request(message):
    sequence_number = None

    try:
        parts = message.split(":")

        if len(parts) >= 2:
            try:
                sequence_number = int(parts[1])
            except ValueError:
                pass

        sequence_number, operand1, operation, operand2 = parse_request(message)
        result = calculate(operand1, operation, operand2)

        return f"RESULT:{sequence_number}:{result}"

    except ZeroDivisionError as error:
        return f"ERROR:{sequence_number}:{error}"

    except ValueError as error:
        if sequence_number is None:
            return f"ERROR:-1:{error}"

        return f"ERROR:{sequence_number}:{error}"

    except Exception:
        if sequence_number is None:
            return "ERROR:-1:erro interno no servidor"

        return f"ERROR:{sequence_number}:erro interno no servidor"


def handle_client(conn, client_address):
    print(
        f"[CONECTADO] {client_address[0]}:{client_address[1]}"
    )

    with conn:
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)

                if not data:
                    break

                message = data.decode("utf-8").strip()

                print(
                    f"[RECEBIDO] {client_address[0]}:{client_address[1]} "
                    f"-> {message}"
                )

                response = process_request(message)

                conn.sendall(response.encode("utf-8"))

                print(
                    f"[ENVIADO] {client_address[0]}:{client_address[1]} "
                    f"<- {response}"
                )

            except ConnectionResetError:
                print(
                    f"[DESCONECTADO] {client_address[0]}:{client_address[1]}"
                )
                break

            except OSError as error:
                print(
                    f"[ERRO] Comunicação com "
                    f"{client_address}: {error}"
                )
                break

    print(
        f"[ENCERRADO] {client_address[0]}:{client_address[1]}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Servidor TCP da calculadora"
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)

    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((args.host, args.port))
        server.listen()

        print("=" * 50)
        print("Servidor TCP da calculadora")
        print("=" * 50)
        print(f"Endereço: {args.host}")
        print(f"Porta: {args.port}")
        print("Aguardando conexões...")
        print("Pressione Ctrl+C para encerrar.")
        print()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while True:
                try:
                    conn, client_address = server.accept()

                    executor.submit(
                        handle_client,
                        conn,
                        client_address
                    )

                except OSError as error:
                    print(
                        f"[ERRO] Falha ao aceitar conexão: {error}"
                    )

    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")

    except OSError as error:
        print(
            f"[ERRO] Não foi possível iniciar o servidor: {error}"
        )

    finally:
        server.close()


if __name__ == "__main__":
    main()