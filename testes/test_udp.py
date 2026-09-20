import socket
import unittest

from udp.cliente import enviar_com_retentativas

class SocketSimulado:
    def __init__(self, falhas):
        self.falhas = falhas
        self.envios = 0

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendto(self, data, address):
        self.envios += 1

    def recvfrom(self, buffer_size):
        if self.falhas > 0:
            self.falhas -= 1
            raise socket.timeout()

        return (
            b"RESULT:7:15.0",
            (
                "127.0.0.1",
                6789,
            ),
        )

class TestRetentativasUDP(
    unittest.TestCase
):
    def test_retransmite_ate_receber_resposta(
        self,
    ):
        sock = SocketSimulado(
            falhas=2
        )

        (
            rtt,
            attempts,
            retransmissions,
            response,
        ) = enviar_com_retentativas(
            sock,
            "CALC:7:10:+:5",
            (
                "127.0.0.1",
                6789,
            ),
            7,
            0.01,
            5,
        )

        self.assertIsNotNone(
            rtt
        )

        self.assertEqual(
            attempts,
            3,
        )

        self.assertEqual(
            retransmissions,
            2,
        )

        self.assertEqual(
            response,
            "RESULT:7:15.0",
        )

        self.assertEqual(
            sock.envios,
            3,
        )

    def test_interrompe_apos_limite_de_tentativas(
        self,
    ):
        sock = SocketSimulado(
            falhas=10
        )

        (
            rtt,
            attempts,
            retransmissions,
            response,
        ) = enviar_com_retentativas(
            sock,
            "CALC:7:10:+:5",
            (
                "127.0.0.1",
                6789,
            ),
            7,
            0.01,
            4,
        )

        self.assertIsNone(
            rtt
        )

        self.assertEqual(
            attempts,
            4,
        )

        self.assertEqual(
            retransmissions,
            3,
        )

        self.assertIsNone(
            response
        )

        self.assertEqual(
            sock.envios,
            4,
        )

if __name__ == "__main__":
    unittest.main()