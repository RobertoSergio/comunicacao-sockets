import argparse
import random
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


def format_number(value):
    return str(value)


def process_request(sock, data, client_address, loss_rate):
    message = data.decode("utf-8").strip()

    print(
        f"[RECEBIDO] {client_address[0]}:{client_address[1]} -> {message}"
    )

    if random.random() < loss_rate:
        print(
            f"[PERDIDO] {client_address[0]}:{client_address[1]} "
            f"-> nenhuma resposta enviada"
        )
        return

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

        response = f"RESULT:{sequence_number}:{format_number(result)}"

    except ZeroDivisionError as error:
        response = f"ERROR:{sequence_number}:{error}"

    except ValueError as error:
        if sequence_number is None:
            response = f"ERROR:-1:{error}"
        else:
            response = f"ERROR:{sequence_number}:{error}"

    except Exception:
        if sequence_number is None:
            response = "ERROR:-1:erro interno no servidor"
        else:
            response = f"ERROR:{sequence_number}:erro interno no servidor"

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

    args = parser.parse_args()

    if not 0.0 <= args.loss_rate <= 1.0:
        parser.error("--loss-rate deve estar entre 0.0 e 1.0")

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    try:
        sock.bind((args.host, args.port))

        print("=" * 50)
        print("Servidor UDP da calculadora")
        print("=" * 50)
        print(f"Endereço: {args.host}")
        print(f"Porta: {args.port}")
        print(f"Taxa de perda: {args.loss_rate:.0%}")
        print("Aguardando requisições...")
        print("Pressione Ctrl+C para encerrar.")
        print()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while True:
                try:
                    data, client_address = sock.recvfrom(BUFFER_SIZE)

                    executor.submit(
                        process_request,
                        sock,
                        data,
                        client_address,
                        args.loss_rate,
                    )

                except OSError as error:
                    print(f"[ERRO] Falha ao receber mensagem: {error}")

    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")

    except OSError as error:
        print(f"[ERRO] Não foi possível iniciar o servidor: {error}")

    finally:
        sock.close()


if __name__ == "__main__":
    main()