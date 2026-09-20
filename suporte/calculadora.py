import math

OPERACOES = {"+", "-", "*", "/"}

def interpretar_requisicao(mensagem):
    partes = mensagem.split(":")

    if len(partes) != 5:
        raise ValueError(
            "formato inválido; esperado CALC:<n>:<operando1>:<op>:<operando2>"
        )

    if partes[0] != "CALC":
        raise ValueError("comando inválido; esperado CALC")

    try:
        numero = int(partes[1])
    except ValueError as error:
        raise ValueError("número de sequência inválido") from error

    try:
        operando1 = float(partes[2])
        operando2 = float(partes[4])
    except ValueError as error:
        raise ValueError("operando inválido") from error

    if not math.isfinite(operando1) or not math.isfinite(operando2):
        raise ValueError("operando inválido")

    operacao = partes[3]

    if operacao not in OPERACOES:
        raise ValueError("operação inválida; use +, -, * ou /")

    return numero, operando1, operacao, operando2

def calcular(operando1, operacao, operando2):
    if operacao == "+":
        return operando1 + operando2

    if operacao == "-":
        return operando1 - operando2

    if operacao == "*":
        return operando1 * operando2

    if operacao == "/":
        if operando2 == 0:
            raise ZeroDivisionError("divisão por zero")
        return operando1 / operando2

    raise ValueError("operação inválida")

def processar_requisicao(mensagem):
    numero = None

    try:
        partes = mensagem.split(":")

        if len(partes) >= 2:
            try:
                numero = int(partes[1])
            except ValueError:
                pass

        numero, operando1, operacao, operando2 = interpretar_requisicao(
            mensagem
        )

        resultado = calcular(
            operando1,
            operacao,
            operando2,
        )

        return f"RESULT:{numero}:{resultado}"

    except ZeroDivisionError as error:
        return f"ERROR:{numero}:{error}"

    except ValueError as error:
        numero = -1 if numero is None else numero
        return f"ERROR:{numero}:{error}"

    except Exception:
        numero = -1 if numero is None else numero
        return f"ERROR:{numero}:erro interno no servidor"