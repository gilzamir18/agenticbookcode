import asyncio
import sqlite3
import re

from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor
from agenticblocks.blocks.llm.agent import LLMAgentBlock
from agenticblocks import as_tool

MODEL = "ollama/mistral-nemo:latest"

SCHEMA = """
Tabela: pedidos
Colunas:
  - id             INTEGER  (chave primária)
  - produto_nome   TEXT     (nome do produto)
  - quantidade     INTEGER  (quantidade vendida em unidades)
  - valor_unitario REAL     (preço unitário em reais)
  - created_at     TEXT     (data da venda, formato YYYY-MM-DD)
"""


def _criar_banco() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("""
        CREATE TABLE pedidos (
            id             INTEGER PRIMARY KEY,
            produto_nome   TEXT    NOT NULL,
            quantidade     INTEGER NOT NULL,
            valor_unitario REAL    NOT NULL,
            created_at     TEXT    NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO pedidos VALUES (?, ?, ?, ?, ?)",
        [
            (1, "Teclado",  10, 150.0, "2024-03-05"),
            (2, "Monitor",   3, 900.0, "2024-03-12"),
            (3, "Teclado",   7, 150.0, "2024-03-20"),
            (4, "Mouse",    15,  80.0, "2024-03-08"),
            (5, "Monitor",   2, 900.0, "2024-03-25"),
            (6, "Headset",   5, 200.0, "2024-02-14"),
        ],
    )
    conn.commit()
    return conn


_DB = _criar_banco()

# Bloco 1: Gerador de SQL (idêntico ao original)
gerador_sql = LLMAgentBlock(
    name="gerador_sql",
    description="Traduz perguntas em linguagem natural para consultas SQL.",
    system_prompt=(
        "Você é um analista de dados especialista em SQL.\n"
        "Responda APENAS com a consulta SQL — sem markdown, sem explicações.\n\n"
        f"Esquema do banco de dados:\n{SCHEMA}"
    ),
    model=MODEL,
    max_iterations=0,
)


# Bloco 2: Verificador SQL (mesma lógica, mas sem retorno de feedback ao gerador)
@as_tool
def verificador_sql(content: str) -> dict:
    """Executa a consulta SQL no banco e retorna o resultado ou o erro."""
    match = re.search(r"(SELECT\b.*?)(?:;|\Z)", content, re.IGNORECASE | re.DOTALL)
    consulta = match.group(1).strip() if match else content.strip()
    try:
        cursor = _DB.execute(consulta)
        colunas = [d[0] for d in cursor.description]
        linhas = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        return {"is_valid": True, "feedback": str(linhas)}
    except sqlite3.OperationalError as e:
        return {"is_valid": False, "feedback": f"OperationalError: {e}"}


async def main():
    pergunta = "Quais os 3 produtos mais vendidos em março de 2024?"

    # Fluxo linear sem ciclo de reflexão: gerador → verificador (1 única tentativa)
    graph = WorkflowGraph()
    graph.add_sequence(gerador_sql, verificador_sql)

    ctx = await WorkflowExecutor(graph).run(initial_input={"prompt": pergunta})

    saida_verificador = ctx.get_output("verificador_sql")
    saida_gerador = ctx.get_output("gerador_sql")
    sucesso = saida_verificador.result.get("is_valid", False)

    print(f"\n{'='*60}")
    print(f"Iterações: 1  |  SQL aprovado: {sucesso}")
    print(f"\nSQL gerado:\n{saida_gerador.response}")

    if sucesso:
        print(f"\nResultado da consulta:\n{saida_verificador.result['feedback']}")
    else:
        print(f"\nErro: {saida_verificador.result['feedback']}")


if __name__ == "__main__":
    asyncio.run(main())
