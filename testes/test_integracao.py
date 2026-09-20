import os
import socket
import subprocess
import sys
import threading
import time
import unittest

ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

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

def iniciar(
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
        stderr=subprocess.DEVNULL,
    )

def encerrar(process):
    if process.poll() is None:
        process.terminate()

        try:
            process.wait(
                timeout=2
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

def esperar_tcp(
    port,
    process,
):
    limite = time.time() + 3

    while time.time() < limite:
        if process.poll() is not None:
            raise RuntimeError(
                "Servidor encerrou antes de ficar disponível"
            )

        try:
            with socket.create_connection(
                (
                    "127.0.0.1",
                    port,
                ),
                timeout=0.1,
            ):
                return

        except OSError:
            time.sleep(0.05)

    raise TimeoutError(
        "Servidor TCP não ficou disponível"
    )

def esperar_udp(
    port,
    process,
):
    limite = time.time() + 3

    while time.time() < limite:
        if process.poll() is not None:
            raise RuntimeError(
                "Servidor encerrou antes de ficar disponível"
            )

        try:
            with socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            ) as sock:

                sock.settimeout(
                    0.1
                )

                sock.sendto(
                    b"CALC:999:1:+:1",
                    (
                        "127.0.0.1",
                        port,
                    ),
                )

                data, _ = sock.recvfrom(
                    1024
                )

                if data.startswith(
                    b"RESULT:999:"
                ):
                    return

        except OSError:
            time.sleep(0.05)

    raise TimeoutError(
        "Servidor UDP não ficou disponível"
    )

class TestServidores(
    unittest.TestCase
):
    def test_udp_atende_clientes_simultaneos(
        self,
    ):
        porta = porta_livre()

        server = iniciar(
            os.path.join(
                ROOT_DIR,
                "udp",
                "servidor.py",
            ),
            [
                "--port",
                str(porta),
            ],
        )

        try:
            esperar_udp(
                porta,
                server,
            )

            resultados = []

            def requisitar(numero):
                with socket.socket(
                    socket.AF_INET,
                    socket.SOCK_DGRAM,
                ) as sock:

                    sock.settimeout(
                        2
                    )

                    mensagem = (
                        f"CALC:{numero}:10:+:5"
                        .encode()
                    )

                    sock.sendto(
                        mensagem,
                        (
                            "127.0.0.1",
                            porta,
                        ),
                    )

                    data, _ = sock.recvfrom(
                        1024
                    )

                    resultados.append(
                        data.decode()
                    )

            threads = [
                threading.Thread(
                    target=requisitar,
                    args=(i,),
                )
                for i in range(5)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join(
                    timeout=2
                )

            self.assertEqual(
                len(resultados),
                5,
            )

            self.assertTrue(
                all(
                    item.startswith(
                        "RESULT:"
                    )
                    for item in resultados
                )
            )

        finally:
            encerrar(server)

    def test_tcp_atende_clientes_simultaneos(
        self,
    ):
        porta = porta_livre()

        server = iniciar(
            os.path.join(
                ROOT_DIR,
                "tcp",
                "servidor.py",
            ),
            [
                "--port",
                str(porta),
            ],
        )

        try:
            esperar_tcp(
                porta,
                server,
            )

            resultados = []

            def requisitar(numero):
                with socket.create_connection(
                    (
                        "127.0.0.1",
                        porta,
                    ),
                    timeout=2,
                ) as sock:

                    mensagem = (
                        f"CALC:{numero}:10:+:5\n"
                        .encode()
                    )

                    sock.sendall(
                        mensagem
                    )

                    data = sock.recv(
                        1024
                    )

                    resultados.append(
                        data.decode().strip()
                    )

            threads = [
                threading.Thread(
                    target=requisitar,
                    args=(i,),
                )
                for i in range(5)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join(
                    timeout=2
                )

            self.assertEqual(
                len(resultados),
                5,
            )

            self.assertTrue(
                all(
                    item.startswith(
                        "RESULT:"
                    )
                    for item in resultados
                )
            )

        finally:
            encerrar(server)

    def test_protobuf_atende_clientes_simultaneos(
        self,
    ):
        from proto import calculadora_pb2

        porta = porta_livre()

        server = iniciar(
            os.path.join(
                ROOT_DIR,
                "proto_tcp",
                "servidor.py",
            ),
            [
                "--port",
                str(porta),
            ],
        )

        try:
            esperar_tcp(
                porta,
                server,
            )

            resultados = []

            def receber_exato(
                sock,
                tamanho,
            ):
                partes = bytearray()

                while len(partes) < tamanho:
                    data = sock.recv(
                        tamanho
                        - len(partes)
                    )

                    if not data:
                        raise ConnectionResetError(
                            "Conexão encerrada"
                        )

                    partes.extend(
                        data
                    )

                return bytes(partes)

            def enviar(numero):
                request = (
                    calculadora_pb2.Requisicao(
                        numero=numero,
                        operando1=10,
                        operacao="+",
                        operando2=5,
                    )
                )

                payload = (
                    request.SerializeToString()
                )

                frame = (
                    len(payload)
                    .to_bytes(4, "big")
                    + payload
                )

                with socket.create_connection(
                    (
                        "127.0.0.1",
                        porta,
                    ),
                    timeout=2,
                ) as sock:

                    sock.sendall(
                        frame
                    )

                    header = receber_exato(
                        sock,
                        4,
                    )

                    size = int.from_bytes(
                        header,
                        "big",
                    )

                    data = receber_exato(
                        sock,
                        size,
                    )

                    response = (
                        calculadora_pb2.Resposta()
                    )

                    response.ParseFromString(
                        data
                    )

                    resultados.append(
                        response
                    )

            threads = [
                threading.Thread(
                    target=enviar,
                    args=(i,),
                )
                for i in range(5)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join(
                    timeout=2
                )

            self.assertEqual(
                len(resultados),
                5,
            )

            self.assertTrue(
                all(
                    response.sucesso
                    for response in resultados
                )
            )

            self.assertTrue(
                all(
                    response.resultado == 15
                    for response in resultados
                )
            )

        finally:
            encerrar(server)

if __name__ == "__main__":
    unittest.main()