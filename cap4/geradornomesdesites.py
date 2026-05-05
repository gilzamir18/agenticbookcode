import asyncio
from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor
from agenticblocks.blocks.llm.agent import LLMAgentBlock
from agenticblocks import as_tool

MODEL = "ollama/mistral-nemo:latest"

gerador = LLMAgentBlock(
    name="gerador",
    description="Gera 5 nomes de sites para uma ideia.",
    system_prompt="""Gere exatamente 5 nomes criativos para um site, numerados de 1 a 5,
um por linha, sem espaços e sem caracteres especiais. Apenas a lista, sem explicações.""",
    model=MODEL,
    max_iterations=0,
)

critico = LLMAgentBlock(
    name="critico",
    description="Avalia e aprimora a lista de nomes.",
    system_prompt="""Você recebe uma lista de 5 nomes de sites. Melhore os nomes fracos
e retorne a lista final com exatamente 5 nomes, no mesmo formato numerado.""",
    model=MODEL,
    max_iterations=0,
)

@as_tool
def condicao_parada(content: str) -> dict:
    """Verifica se a lista tem 5 nomes válidos (3-30 chars, sem espaços)."""
    nomes = [
        linha.lstrip("0123456789. )-").strip()
        for linha in content.splitlines()
        if linha.strip() and linha.strip()[0].isdigit()
    ]
    if len(nomes) < 5:
        return {"is_valid": False, "feedback": f"Preciso de 5 nomes, recebi {len(nomes)}."}
    invalidos = [n for n in nomes[:5] if not (3 <= len(n) <= 30) or " " in n]
    if invalidos:
        return {"is_valid": False, "feedback": f"Nomes inválidos: {invalidos}. Sem espaços, entre 3 e 30 chars."}
    return {"is_valid": True, "feedback": ""}

@as_tool
def executor(content: str) -> dict:
    """Salva os nomes aprovados em nomes_de_sites.txt."""
    open("nomes_de_sites.txt", "w").write(content)
    print("[Executor] Nomes salvos em nomes_de_sites.txt")
    return {"result": content}

async def main():
    ideia = input("Ideia para o site: ")

    graph = WorkflowGraph()
    graph.add_block(gerador)
    graph.add_block(critico)
    graph.add_block(condicao_parada)
    graph.add_block(executor)

    graph.add_cycle(
        name="reflexao",
        sequence=["gerador", "critico", "condicao_parada"],
        condition_block="condicao_parada",
        max_iterations=5,
    )
    graph.connect("reflexao", "executor")

    ctx = await WorkflowExecutor(graph).run(initial_input={"prompt": ideia})

    cr = ctx.cycle_results["reflexao"]
    print(f"\nIterações: {cr.iterations} | Validado: {cr.validated}")
    print(cr.output.response)

if __name__ == "__main__":
    asyncio.run(main())
