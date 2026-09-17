import os
import subprocess
import sys
import time

ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
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

UDP_SERVER = os.path.join(ROOT_DIR, "udp", "servidor.py")
UDP_CLIENT = os.path.join(ROOT_DIR, "udp", "cliente.py")
TCP_SERVER = os.path.join(ROOT_DIR, "tcp", "servidor.py")
TCP_CLIENT = os.path.join(ROOT_DIR, "tcp", "cliente.py")

UDP_LOSS_RATES = [0.0, 0.1, 0.3]
UDP_EXECUTIONS = 3
TCP_EXECUTIONS = 1


def start_server(script, extra_args=None):
    command = [sys.executable, script]

    if extra_args:
        command.extend(extra_args)

    return subprocess.Popen(
        command,
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )


def stop_server(server):
    if server.poll() is None:
        server.terminate()

        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


def wait_for_server(server):
    time.sleep(1)

    if server.poll() is not None:
        raise RuntimeError(
            "O servidor foi encerrado inesperadamente."
        )


def run_client(script, extra_args=None):
    command = [sys.executable, script]

    if extra_args:
        command.extend(extra_args)

    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    print(result.stdout)

    if result.returncode != 0:
        print(result.stderr)

    return result.returncode


def prepare_results():
    os.makedirs(
        os.path.join(ROOT_DIR, "resultados"),
        exist_ok=True,
    )

    with open(
        UDP_RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write("# Resultados UDP\n\n")

    with open(
        TCP_RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write("# Resultados TCP\n\n")


def run_udp_experiments():
    for loss_rate in UDP_LOSS_RATES:
        print()
        print("=" * 70)
        print(
            f"UDP - Taxa de perda: {loss_rate:.0%}"
        )
        print("=" * 70)

        server = start_server(
            UDP_SERVER,
            [
                "--loss-rate",
                str(loss_rate),
            ],
        )

        try:
            wait_for_server(server)

            for execution in range(
                1,
                UDP_EXECUTIONS + 1,
            ):
                print()
                print(
                    f"Execução {execution}/"
                    f"{UDP_EXECUTIONS}"
                )

                return_code = run_client(
                    UDP_CLIENT,
                    [
                        "--loss-rate",
                        str(loss_rate),
                        "--execution",
                        str(execution),
                    ],
                )

                if return_code != 0:
                    print(
                        f"[ERRO] A execução "
                        f"{execution} do UDP terminou "
                        f"com código {return_code}."
                    )

        finally:
            stop_server(server)
            time.sleep(0.2)


def run_tcp_experiment():
    print()
    print("=" * 70)
    print("TCP")
    print("=" * 70)

    server = start_server(TCP_SERVER)

    try:
        wait_for_server(server)

        for execution in range(
            1,
            TCP_EXECUTIONS + 1,
        ):
            print()
            print(
                f"Execução {execution}/"
                f"{TCP_EXECUTIONS}"
            )

            return_code = run_client(
                TCP_CLIENT,
                [
                    "--execution",
                    str(execution),
                ],
            )

            if return_code != 0:
                print(
                    f"[ERRO] A execução "
                    f"{execution} do TCP terminou "
                    f"com código {return_code}."
                )

    finally:
        stop_server(server)


def main():
    print("=" * 70)
    print("EXPERIMENTOS UDP E TCP")
    print("=" * 70)
    print()
    print(
        "Serão realizadas 9 execuções UDP "
        "e 1 execução TCP."
    )

    prepare_results()

    run_udp_experiments()
    run_tcp_experiment()

    print()
    print("=" * 70)
    print("EXPERIMENTOS CONCLUÍDOS")
    print("=" * 70)


if __name__ == "__main__":
    main()