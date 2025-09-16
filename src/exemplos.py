def soma(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Divisão por zero não permitida")
    return a / b
