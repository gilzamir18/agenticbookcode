import asyncio
from agenticblocks.core.function_block import as_tool
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor

LINES_PER_AGENT = 50

@as_tool
async def supervisor(texto: str) -> str:
    """Divide o texto em blocos de LINES_PER_AGENT linhas e resume cada um em paralelo."""
    agent = LLMAgentBlock(
        name='agente',
        system_prompt="Resuma o seguinte texto em no máximo 10 linhas.",
        model='ollama/mistral-nemo:latest',
        max_iteration=0
    )
    lines = texto.splitlines()
    chunks = ["\n".join(lines[i:i+LINES_PER_AGENT]) for i in range(0, len(lines), LINES_PER_AGENT)]
    
    # Executa todos os agentes em paralelo
    resumos = await asyncio.gather(*[agent.run(AgentInput(prompt=c)) for c in chunks])
    return "\n".join(r.response for r in resumos)

async def main():
    graph = WorkflowGraph()
    
    # 1. Adicionamos o bloco de processamento paralelo
    supervisor_node = graph.add_block(supervisor)
    # 2. Adicionamos o bloco do supervisor
    agregador_node = graph.add_block(LLMAgentBlock(
        name='agregador',
        system_prompt="Resuma o seguinte texto em no máximo 30 linhas.",
        model='ollama/mistral-nemo:latest',
        max_iteration=0
    ))
    # 3. Conectamos os dois (a saída de texto do primeiro vira o prompt do segundo)
    graph.connect(supervisor_node, agregador_node)

    with open("supervisor_input.txt", "r") as reader:
        texto = reader.read()

    # O "initial_input" alimenta o bloco que não tem entradas (chunker_node)
    executor = WorkflowExecutor(graph)
    ctx = await executor.run(initial_input={"texto": texto})
    
    print("*"*100)
    print(ctx.get_output("agregador").response)

if __name__ == "__main__":
    asyncio.run(main())
