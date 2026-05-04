"""
Sistema Multi-Agente de Três Níveis
======================================

Fluxo de dados:

       TEXTO DE ENTRADA
            │
    ┌───────┴────────┐
    │    NÍVEL 1     │  ← vários "extratores" em PARALELO
    │  (extratores)  │    cada um lê um trecho e lista ideias-chave
    └───────┬────────┘
            │
    ┌───────┴────────┐
    │    NÍVEL 2     │  ← vários "analisadores" em PARALELO
    │ (analisadores) │    cada um recebe um grupo de extrações e aprofunda
    └───────┬────────┘
            │
    ┌───────┴────────┐
    │    NÍVEL 3     │  ← um único "supervisor" produz a síntese final
    │  (supervisor)  │
    └───────┬────────┘
            │
       SÍNTESE FINAL
"""

import asyncio
from agenticblocks.core.function_block import as_tool
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor

LINHAS_POR_EXTRATOR  = 30   # Nível 1: chunks pequenos de texto
EXTRACOES_POR_GRUPO  = 2    # Nível 2: quantas extrações cada analisador recebe

SEP = "\n\n— bloco —\n\n"   # separador entre resultados de agentes


# ═══════════════════════════════════════════════════════════
#  NÍVEL 1 — Extratores (paralelos, chunks de texto)
# ═══════════════════════════════════════════════════════════

@as_tool
async def extratores(texto: str) -> str:
    """
    Divide o texto em blocos de LINHAS_POR_EXTRATOR linhas.
    Um agente extrator processa cada bloco em paralelo.
    Retorna as extrações concatenadas para o Nível 2.
    """
    agente = LLMAgentBlock(
        name="extrator",
        system_prompt=(
            "Leia o trecho a seguir e liste as 3 ideias mais importantes, "
            "em frases curtas e diretas."
        ),
        model="ollama/granite4:latest",
        max_iteration=0,
    )

    linhas = texto.splitlines()
    blocos = [
        "\n".join(linhas[i : i + LINHAS_POR_EXTRATOR])
        for i in range(0, len(linhas), LINHAS_POR_EXTRATOR)
        if any(l.strip() for l in linhas[i : i + LINHAS_POR_EXTRATOR])
    ]

    print(f"[Nível 1] {len(blocos)} extratores iniciados em paralelo...")
    resultados = await asyncio.gather(
        *[agente.run(AgentInput(prompt=bloco)) for bloco in blocos]
    )
    print(f"[Nível 1] Concluído.\n")

    return SEP.join(r.response for r in resultados)


# ═══════════════════════════════════════════════════════════
#  NÍVEL 2 — Analisadores (paralelos, grupos de extrações)
# ═══════════════════════════════════════════════════════════

@as_tool
async def analisadores(texto: str) -> str:
    """
    Recebe as extrações do Nível 1 (separadas por SEP).
    Agrupa EXTRACOES_POR_GRUPO extrações e analisa cada grupo em paralelo.
    Retorna as análises concatenadas para o Nível 3.
    """
    agente = LLMAgentBlock(
        name="analisador",
        system_prompt=(
            "Você recebeu extratos de ideias coletadas de um texto filosófico. "
            "Identifique os temas em comum entre eles e elabore uma análise coesa "
            "de no máximo 8 linhas."
        ),
        model="ollama/granite4:latest",
        max_iteration=0,
    )

    extracoes = [bloco.strip() for bloco in texto.split("— bloco —") if bloco.strip()]
    grupos = [
        "\n\n".join(extracoes[i : i + EXTRACOES_POR_GRUPO])
        for i in range(0, len(extracoes), EXTRACOES_POR_GRUPO)
    ]

    print(f"[Nível 2] {len(grupos)} analisadores iniciados em paralelo...")
    resultados = await asyncio.gather(
        *[agente.run(AgentInput(prompt=grupo)) for grupo in grupos]
    )
    print(f"[Nível 2] Concluído.\n")

    return SEP.join(r.response for r in resultados)


# ═══════════════════════════════════════════════════════════
#  NÍVEL 3 — Supervisor (síntese final)
# ═══════════════════════════════════════════════════════════

supervisor = LLMAgentBlock(
    name="supervisor",
    system_prompt=(
        "Você é um crítico e historiador das ideias. "
        "Recebeu análises parciais produzidas por vários agentes que estudaram "
        "um texto sobre os grandes pensadores da humanidade. "
        "Escreva uma síntese final de no máximo 15 linhas, destacando as teses "
        "centrais do texto e os pensadores mencionados."
    ),
    model="ollama/mistral-nemo:latest",
    max_iteration=0,
)


# ═══════════════════════════════════════════════════════════
#  GRAFO — conecta os três níveis em sequência
# ═══════════════════════════════════════════════════════════

def construir_grafo() -> WorkflowGraph:
    grafo = WorkflowGraph()
    n1 = grafo.add_block(extratores)    # Nível 1
    n2 = grafo.add_block(analisadores)  # Nível 2
    n3 = grafo.add_block(supervisor)    # Nível 3
    grafo.connect(n1, n2)               # N1 → N2
    grafo.connect(n2, n3)               # N2 → N3
    return grafo


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════

async def main():
    caminho_texto =  "supervisor_input.txt"
    
    with open(caminho_texto, encoding="utf-8") as f:
        texto = f.read()

    grafo = construir_grafo()
    executor = WorkflowExecutor(grafo)

    print("Iniciando sistema multi-agente de três níveis...\n")
    ctx = await executor.run(initial_input={"texto": texto})

    print("=" * 70)
    print("SÍNTESE FINAL — Supervisor (Nível 3)")
    print("=" * 70)
    print(ctx.get_output("supervisor").response)


if __name__ == "__main__":
    asyncio.run(main())
