import pytest
from src.exemplos import soma, divide

@pytest.mark.parametrize("a,b,esperado", [
    (2, 3, 5),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_soma_parametrizado(a, b, esperado):
    assert soma(a, b) == esperado

def test_divide_sucesso():
    assert divide(10, 2) == 5
    assert divide(9, 3) == 3

def test_divide_zero_mensagem():
    with pytest.raises(ValueError) as exc:
        divide(10, 0)
    assert "Divisão por zero" in str(exc.value)
