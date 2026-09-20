def validar_resposta(mensagem, numero_esperado):
    partes = mensagem.split(":", 2)

    if len(partes) < 3:
        raise ValueError("resposta inválida")

    tipo, numero, conteudo = partes

    if tipo not in {"RESULT", "ERROR"}:
        raise ValueError("tipo de resposta inválido")

    try:
        numero = int(numero)
    except ValueError as error:
        raise ValueError("número de sequência inválido") from error

    if numero != numero_esperado:
        raise ValueError("número de sequência inesperado")

    if not conteudo:
        raise ValueError("resposta sem conteúdo")

    return tipo, numero, conteudo