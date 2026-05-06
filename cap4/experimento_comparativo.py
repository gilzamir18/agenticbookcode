"""
Experimento: Analista de Dados COM reflexão vs SEM reflexão.

Métricas coletadas por pergunta:
  - sucesso     : SQL executou sem erro?
  - iteracoes   : quantas tentativas o ciclo usou (sempre 1 sem reflexão)
  - tempo_s     : tempo de execução em segundos
"""
import asyncio
import sqlite3
import re
import time
from dataclasses import dataclass, field

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

PERGUNTAS = [
    "Quais os 3 produtos mais vendidos em março de 2024?",
    "Qual o faturamento total por produto?",
    "Qual o produto mais caro vendido em fevereiro de 2024?",
    "Quantas vendas foram realizadas em março de 2024?",
    "Qual a média de valor unitário de todos os produtos?",
]


# ---------------------------------------------------------------------------
# Banco compartilhado (somente leitura durante os testes)
# ---------------------------------------------------------------------------
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


DB = _criar_banco()


# ---------------------------------------------------------------------------
# Fábrica de blocos (nova instância por execução para evitar estado residual)
# ---------------------------------------------------------------------------
def _gerador() -> LLMAgentBlock:
    return LLMAgentBlock(
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


def _verificador_tool():
    @as_tool
    def verificador_sql(content: str) -> dict:
        """Executa a consulta SQL no banco e retorna o resultado ou o erro."""
        match = re.search(r"(SELECT\b.*?)(?:;|\Z)", content, re.IGNORECASE | re.DOTALL)
        consulta = match.group(1).strip() if match else content.strip()
        try:
            cursor = DB.execute(consulta)
            colunas = [d[0] for d in cursor.description]
            linhas = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            return {"is_valid": True, "feedback": str(linhas)}
        except sqlite3.OperationalError as e:
            return {"is_valid": False, "feedback": f"OperationalError: {e}"}
    return verificador_sql


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------
@dataclass
class Resultado:
    pergunta: str
    sucesso: bool
    iteracoes: int
    tempo_s: float
    sql: str
    saida: str


async def rodar_com_reflexao(pergunta: str) -> Resultado:
    gerador = _gerador()
    verificador = _verificador_tool()

    graph = WorkflowGraph()
    graph.add_block(gerador)
    graph.add_block(verificador)
    graph.add_cycle(
        name="autocorrecao_sql",
        sequence=["gerador_sql", "verificador_sql"],
        condition_block="verificador_sql",
        max_iterations=5,
    )

    t0 = time.perf_counter()
    ctx = await WorkflowExecutor(graph).run(initial_input={"prompt": pergunta})
    tempo = time.perf_counter() - t0

    cr = ctx.cycle_results["autocorrecao_sql"]
    saida_verificador = ctx.get_output("verificador_sql")
    feedback = saida_verificador.result.get("feedback", "")

    return Resultado(
        pergunta=pergunta,
        sucesso=cr.validated,
        iteracoes=cr.iterations,
        tempo_s=tempo,
        sql=cr.output.response,
        saida=feedback,
    )


async def rodar_sem_reflexao(pergunta: str) -> Resultado:
    gerador = _gerador()
    verificador = _verificador_tool()

    graph = WorkflowGraph()
    graph.add_sequence(gerador, verificador)

    t0 = time.perf_counter()
    ctx = await WorkflowExecutor(graph).run(initial_input={"prompt": pergunta})
    tempo = time.perf_counter() - t0

    saida_verificador = ctx.get_output("verificador_sql")
    saida_gerador = ctx.get_output("gerador_sql")
    sucesso = saida_verificador.result.get("is_valid", False)
    feedback = saida_verificador.result.get("feedback", "")

    return Resultado(
        pergunta=pergunta,
        sucesso=sucesso,
        iteracoes=1,
        tempo_s=tempo,
        sql=saida_gerador.response,
        saida=feedback,
    )


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------
def _linha(label: str, valor: str, largura: int = 58) -> str:
    return f"  {label:<20}{valor}"


def imprimir_relatorio(
    resultados_com: list[Resultado],
    resultados_sem: list[Resultado],
) -> None:
    sep = "=" * 70
    print(f"\n{sep}")
    print("  EXPERIMENTO: COM Reflexão  vs  SEM Reflexão")
    print(sep)

    total_com_ok = sum(r.sucesso for r in resultados_com)
    total_sem_ok = sum(r.sucesso for r in resultados_sem)
    media_iter_com = sum(r.iteracoes for r in resultados_com) / len(resultados_com)
    media_tempo_com = sum(r.tempo_s for r in resultados_com) / len(resultados_com)
    media_tempo_sem = sum(r.tempo_s for r in resultados_sem) / len(resultados_sem)

    print(f"\n{'Pergunta':<4} {'Método':<16} {'Sucesso':<9} {'Iter':<6} {'Tempo (s)'}")
    print("-" * 70)
    for i, (rc, rs) in enumerate(zip(resultados_com, resultados_sem), 1):
        ok_c = "✓" if rc.sucesso else "✗"
        ok_s = "✓" if rs.sucesso else "✗"
        print(f"  {i:<3}  {'COM reflexão':<16} {ok_c:<9} {rc.iteracoes:<6} {rc.tempo_s:.2f}s")
        print(f"  {i:<3}  {'SEM reflexão':<16} {ok_s:<9} {'1':<6} {rs.tempo_s:.2f}s")
        print()

    print("=" * 70)
    print("  RESUMO GERAL")
    print("=" * 70)
    print(f"  {'':20} {'COM reflexão':>18}   {'SEM reflexão':>18}")
    print(f"  {'Taxa de sucesso':20} {total_com_ok}/{len(resultados_com):>15}   {total_sem_ok}/{len(resultados_sem):>15}")
    print(f"  {'Iter. média':20} {media_iter_com:>18.2f}   {'1.00':>18}")
    print(f"  {'Tempo médio (s)':20} {media_tempo_com:>18.2f}   {media_tempo_sem:>18.2f}")
    print("=" * 70)

    print("\n  DETALHES POR PERGUNTA")
    print("-" * 70)
    for i, (rc, rs) in enumerate(zip(resultados_com, resultados_sem), 1):
        print(f"\n  [{i}] {rc.pergunta}")
        print(f"      COM reflexão → sucesso={rc.sucesso}, iter={rc.iteracoes}, {rc.tempo_s:.2f}s")
        print(f"           SQL: {rc.sql[:80].strip()!r}")
        print(f"        Saída: {rc.saida[:80]!r}")
        print(f"      SEM reflexão → sucesso={rs.sucesso}, {rs.tempo_s:.2f}s")
        print(f"           SQL: {rs.sql[:80].strip()!r}")
        print(f"        Saída: {rs.saida[:80]!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    print("Iniciando experimento comparativo...")
    print(f"Perguntas: {len(PERGUNTAS)}  |  Modelo: {MODEL}\n")

    resultados_com: list[Resultado] = []
    resultados_sem: list[Resultado] = []

    for i, pergunta in enumerate(PERGUNTAS, 1):
        print(f"[{i}/{len(PERGUNTAS)}] {pergunta}")

        print("  → COM reflexão...", end=" ", flush=True)
        rc = await rodar_com_reflexao(pergunta)
        resultados_com.append(rc)
        print(f"sucesso={rc.sucesso}, iter={rc.iteracoes}, {rc.tempo_s:.1f}s")

        print("  → SEM reflexão...", end=" ", flush=True)
        rs = await rodar_sem_reflexao(pergunta)
        resultados_sem.append(rs)
        print(f"sucesso={rs.sucesso}, {rs.tempo_s:.1f}s")

    imprimir_relatorio(resultados_com, resultados_sem)


if __name__ == "__main__":
    asyncio.run(main())
