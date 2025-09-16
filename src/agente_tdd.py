import os
import argparse
from pathlib import Path
from dotenv import load_dotenv



load_dotenv()  # carrega .env

PROVIDER = (os.getenv("PROVIDER") or "mock").strip().lower()

# --------- PROMPT COMUM ----------
from langchain.prompts import PromptTemplate
BASE_PROMPT = PromptTemplate(
    input_variables=["codigo"],
    template=(
        "Você é um agente de TDD. Gere testes unitários em pytest para o código abaixo.\n"
        "Regras:\n"
        "- A primeira linha deve ser 'import pytest'\n"
        "- Use funções 'def test_*'\n"
        "- Inclua casos de sucesso e também de falha/exceção quando fizer sentido\n"
        "- O retorno deve ser apenas o conteúdo do arquivo de testes, sem explicações\n"
        "- Use @pytest.mark.parametrize para cobrir múltiplos cenários de soma.\n"
        "- Para a função divide, crie um teste que valide a mensagem da exceção (ValueError).\n"
        "- Não inclua explicações, apenas o código do arquivo de teste.\n\n"
        "CÓDIGO:\n{codigo}\n"
    )
)


def gerar_testes_mock(_: str) -> str:
    return """import pytest
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
"""


def gerar_testes_llm(codigo: str) -> str:
    # Decide cliente conforme PROVIDER
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY não definido no .env ou ambiente.")
        llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0)

    elif PROVIDER == "azure":
        from langchain_openai import AzureChatOpenAI
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        if not (api_key and endpoint and deployment):
            raise RuntimeError("Vars do Azure faltando: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT.")
        llm = AzureChatOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            api_version="2024-06-01",
            temperature=0,
        )
    else:
        # fallback seguro
        return gerar_testes_mock(codigo)

    chain = BASE_PROMPT | llm
    resp = chain.invoke({"codigo": codigo})
    return getattr(resp, "content", str(resp))



def main():
    parser = argparse.ArgumentParser(description="Gera testes pytest a partir de um arquivo Python.")
    parser.add_argument("--file", "-f", default="src/exemplos.py", help="Arquivo Python de entrada")
    args = parser.parse_args()

    codigo_path = Path(args.file)
    if not codigo_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {codigo_path}")

    codigo = codigo_path.read_text(encoding="utf-8")

    if PROVIDER in {"openai", "azure"}:
        conteudo = gerar_testes_llm(codigo)
    else:
        conteudo = gerar_testes_mock(codigo)

    out_name = f"test_{codigo_path.stem}.py"
    Path("src").mkdir(exist_ok=True)
    Path(f"src/{out_name}").write_text(conteudo, encoding="utf-8")
    print(f"✅ Modo: {PROVIDER} | Arquivo gerado: src/{out_name}")

if __name__ == "__main__":
    main()
