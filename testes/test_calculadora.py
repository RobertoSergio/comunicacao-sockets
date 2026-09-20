import unittest

from suporte.calculadora import (
    calcular,
    interpretar_requisicao,
    processar_requisicao,
)

from suporte.mensagens import validar_resposta

class TestCalculadora(unittest.TestCase):
    def test_soma(self):
        self.assertEqual(
            calcular(10, "+", 5),
            15,
        )

    def test_subtracao(self):
        self.assertEqual(
            calcular(10, "-", 5),
            5,
        )

    def test_multiplicacao(self):
        self.assertEqual(
            calcular(3.5, "*", 2),
            7,
        )

    def test_divisao(self):
        self.assertEqual(
            calcular(8, "/", 2),
            4,
        )

    def test_divisao_por_zero(self):
        with self.assertRaisesRegex(
            ZeroDivisionError,
            "divisão por zero",
        ):
            calcular(8, "/", 0)

    def test_requisicao_valida(self):
        self.assertEqual(
            interpretar_requisicao(
                "CALC:2:3.5:*:2"
            ),
            (
                2,
                3.5,
                "*",
                2.0,
            ),
        )

    def test_requisicao_invalida(self):
        with self.assertRaises(
            ValueError
        ):
            interpretar_requisicao(
                "CALC:2:3.5:^:2"
            )

    def test_resposta_de_erro(self):
        response = processar_requisicao(
            "CALC:1:8:/:0"
        )

        self.assertEqual(
            response,
            "ERROR:1:divisão por zero",
        )

    def test_validacao_de_resposta(self):
        self.assertEqual(
            validar_resposta(
                "RESULT:4:15.0",
                4,
            ),
            (
                "RESULT",
                4,
                "15.0",
            ),
        )

    def test_resposta_com_sequencia_incorreta(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            validar_resposta(
                "RESULT:4:15.0",
                3,
            )

if __name__ == "__main__":
    unittest.main()