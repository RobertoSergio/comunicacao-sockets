import os
import socket
import subprocess
import sys
import time

ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UDP_RESULTS_FILE = os.path.join(
    ROOT_DIR,
    "resultados",
    "resultados_udp.md",
)

TCP_RESULTS_FILE = os.path.join(
    ROOT_DIR,
    "resultados",
    "resultados_tcp.md",
)

PROTO_RESULTS_FILE = os.path.join(
    ROOT_DIR,
    "resultados",
    "resultados_proto.md",
)

UDP_SERVER = os.path.join(
    ROOT_DIR,
    "udp",
    "servidor.py",
)

UDP_CLIENT = os.path.join(
    ROOT_DIR,
    "udp",
    "cliente.py",
)

TCP_SERVER = os.path.join(
    ROOT_DIR,
    "tcp",
    "servidor.py",
)

TCP_CLIENT = os.path.join(
    ROOT_DIR,
    "tcp",
    "cliente.py",
)

PROTO_SERVER = os.path.join(
    ROOT_DIR,
    "proto_tcp",
    "servidor.py",
)

PROTO_CLIENT = os.path.join(
    ROOT_DIR,
    "proto_tcp",
    "cliente.py",
)

UDP_LOSS_RATES = [
    0.0,
    0.1,
    0.3,
]

UDP_EXECUTIONS = 3
TCP_EXECUTIONS = 1
PROTO_EXECUTIONS = 1
SEED = 2026

def porta_livre():
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:

        sock.bind(
            (
                "127.0.0.1",
                0,
            )
        )

        return sock.getsockname()[1]

def iniciar_servidor(
    script,
    argumentos,
):
    return subprocess.Popen(
        [
            sys.executable,
            script,
            *argumentos,
        ],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )

def encerrar_servidor(
    server,
):
    if server.poll() is None:
        server.terminate()

        try:
            server.wait(
                timeout=3
            )
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

def aguardar_tcp(
    server,
    host,
    port,
):
    limite = time.time() + 5

    while time.time() < limite:
        if server.poll() is not None:
            raise RuntimeError(
                "O servidor foi encerrado antes de ficar disponível."
            )

        try:
            with socket.create_connection(
                (
                    host,
                    port,
                ),
                timeout=0.2,
            ):
                return

        except OSError:
            time.sleep(0.05)

    raise TimeoutError(
        "O servidor TCP não ficou disponível "
        "no tempo esperado."
    )

def aguardar_udp(
    server,
):
    time.sleep(0.2)

    if server.poll() is not None:
        raise RuntimeError(
            "O servidor UDP foi encerrado "
            "antes de iniciar."
        )

def executar_cliente(
    script,
    argumentos,
):
    result = subprocess.run(
        [
            sys.executable,
            script,
            *argumentos,
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )

    print(
        result.stdout
    )

    if result.returncode != 0:
        print(
            result.stderr
        )

        raise RuntimeError(
            f"O cliente "
            f"{os.path.basename(script)} "
            f"terminou com código "
            f"{result.returncode}."
        )

def preparar_resultados():
    os.makedirs(
        os.path.join(
            ROOT_DIR,
            "resultados",
        ),
        exist_ok=True,
    )

    with open(
        UDP_RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "# Resultados UDP\n\n"
        )

    with open(
        TCP_RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "# Resultados TCP\n\n"
        )

    with open(
        PROTO_RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            "# Resultados TCP com Protocol Buffers\n\n"
        )

def executar_udp():
    for loss_rate in UDP_LOSS_RATES:
        print()
        print("=" * 70)
        print(
            f"UDP - Taxa de perda: "
            f"{loss_rate:.0%}"
        )
        print("=" * 70)

        port = porta_livre()

        server = iniciar_servidor(
            UDP_SERVER,
            [
                "--port",
                str(port),
                "--loss-rate",
                str(loss_rate),
            ],
        )

        try:
            aguardar_udp(
                server
            )

            for execution in range(
                1,
                UDP_EXECUTIONS + 1,
            ):
                print()
                print(
                    f"Execução "
                    f"{execution}/"
                    f"{UDP_EXECUTIONS}"
                )

                executar_cliente(
                    UDP_CLIENT,
                    [
                        "--port",
                        str(port),
                        "--loss-rate",
                        str(loss_rate),
                        "--execution",
                        str(execution),
                        "--seed",
                        str(SEED),
                    ],
                )

        finally:
            encerrar_servidor(
                server
            )

def executar_tcp():
    print()
    print("=" * 70)
    print("TCP")
    print("=" * 70)

    port = porta_livre()

    server = iniciar_servidor(
        TCP_SERVER,
        [
            "--port",
            str(port),
        ],
    )

    try:
        aguardar_tcp(
            server,
            "127.0.0.1",
            port,
        )

        for execution in range(
            1,
            TCP_EXECUTIONS + 1,
        ):
            print()
            print(
                f"Execução "
                f"{execution}/"
                f"{TCP_EXECUTIONS}"
            )

            executar_cliente(
                TCP_CLIENT,
                [
                    "--port",
                    str(port),
                    "--execution",
                    str(execution),
                    "--seed",
                    str(SEED),
                ],
            )

    finally:
        encerrar_servidor(
            server
        )

def executar_protobuf():
    print()
    print("=" * 70)
    print(
        "TCP COM PROTOCOL BUFFERS"
    )
    print("=" * 70)

    port = porta_livre()

    server = iniciar_servidor(
        PROTO_SERVER,
        [
            "--port",
            str(port),
        ],
    )

    try:
        aguardar_tcp(
            server,
            "127.0.0.1",
            port,
        )

        for execution in range(
            1,
            PROTO_EXECUTIONS + 1,
        ):
            print()
            print(
                f"Execução "
                f"{execution}/"
                f"{PROTO_EXECUTIONS}"
            )

            executar_cliente(
                PROTO_CLIENT,
                [
                    "--port",
                    str(port),
                    "--execution",
                    str(execution),
                    "--seed",
                    str(SEED),
                ],
            )

    finally:
        encerrar_servidor(
            server
        )

def main():
    print("=" * 70)
    print(
        "EXPERIMENTOS UDP, TCP E PROTOCOL BUFFERS"
    )
    print("=" * 70)
    print()
    print(
        "Serão realizadas 9 execuções UDP, "
        "1 execução TCP e 1 execução "
        "com Protocol Buffers."
    )
    print(
        f"Seed do conjunto de requisições: "
        f"{SEED}"
    )

    preparar_resultados()

    executar_udp()
    executar_tcp()
    executar_protobuf()

    print()
    print(
        "Experimentos concluídos com sucesso."
    )

if __name__ == "__main__":
    main()