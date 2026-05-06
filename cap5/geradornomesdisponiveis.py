import asyncio

from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor
from agenticblocks.blocks.llm.agent import LLMAgentBlock
from agenticblocks.tools.mcp_client import MCPClientBridge
from agenticblocks import as_tool

MODEL = "ollama/mistral-nemo:latest"

gerador = LLMAgentBlock(
    name="gerador",
    description="Gera 10 nomes de sites criativos para uma ideia.",
    system_prompt="""Gere exatamente 10 nomes criativos e únicos para um site, numerados de 1 a 10,
um por linha, sem espaços, sem acentos e sem caracteres especiais. Apenas a lista, sem explicações.""",
    model=MODEL,
    max_iterations=0,
)


@as_tool
def condicao_parada(content: str) -> dict:
    """Verifica se há pelo menos 5 nomes com domínios disponíveis."""
    nomes = [
        linha.lstrip("0123456789. )-").strip()
        for linha in content.splitlines()
        if linha.strip() and linha.strip()[0].isdigit()
    ]
    validos = [n for n in nomes if 3 <= len(n) <= 30 and " " not in n]
    if len(validos) >= 5:
        return {"is_valid": True, "feedback": ""}
    return {
        "is_valid": False,
        "feedback": f"Apenas {len(validos)} nome(s) disponível(is). Gere novas opções.",
    }


@as_tool
def executor(content: str) -> dict:
    """Salva os nomes com domínios disponíveis em nomes_disponiveis.txt."""
    open("nomes_disponiveis.txt", "w").write(content)
    print("[Executor] Nomes salvos em nomes_disponiveis.txt")
    return {"result": content}


async def main():
    ideia = input("Ideia para o site: ")

    bridge = MCPClientBridge(command="duckduckgo-mcp-server", args=[])
    mcp_tools = await bridge.connect()

    verificador = LLMAgentBlock(
        name="verificador",
        description="Filtra nomes com domínios disponíveis em .com, .com.br e .org via DuckDuckGo.",
        system_prompt="""Você recebe uma lista de nomes candidatos para um site.
Para cada nome, faça três buscas no DuckDuckGo:
  - "site:nome.com"
  - "site:nome.com.br"
  - "site:nome.org"
Se as três buscas não retornarem resultados, o domínio está disponível nos três TLDs.
Ao final, retorne APENAS os nomes disponíveis, numerados de 1 a N,
um por linha, sem espaços e sem caracteres especiais.""",
        model=MODEL,
        tools=mcp_tools,
        max_iterations=35,
        max_tool_calls=30,
        on_max_iterations="return_last",
    )

    graph = WorkflowGraph()
    graph.add_block(gerador)
    graph.add_block(verificador)
    graph.add_block(condicao_parada)
    graph.add_block(executor)

    graph.add_cycle(
        name="verificacao",
        sequence=["gerador", "verificador", "condicao_parada"],
        condition_block="condicao_parada",
        max_iterations=5,
    )
    graph.connect("verificacao", "executor")

    try:
        ctx = await WorkflowExecutor(graph).run(initial_input={"prompt": ideia})
    finally:
        await bridge.disconnect()

    cr = ctx.cycle_results["verificacao"]
    print(f"\nIterações: {cr.iterations} | Validado: {cr.validated}")
    print(cr.output.response)


if __name__ == "__main__":
    asyncio.run(main())
