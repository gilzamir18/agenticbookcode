import asyncio
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks import as_tool

LINES_PER_AGENT = 50

async def supervisor_agent(texto: str) -> str:
    """
    Recebe um texto grande e o divide em N agentes,
    de modo que cada agente processe no máximo LINES_PER_AGENT linhas.
    Os agentes resumem o texto que recebem e depois o supervisor
    junta os resumos em um texto final.
    """
    lines = texto.splitlines()
    inputs = []
    resumos = []

    summarizer = LLMAgentBlock(
                name=f'summarizer',
                description="Você deve resumir o texto recebido.",
                system_prompt="""Resuma o seguinte texto em no máximo 30 linhas.""",
                model='ollama/mistral-nemo:latest',
                max_iteration=0,
            )

    tasks = []
    for i, line in enumerate(lines):
        inputs.append(line)
        if (i + 1) % LINES_PER_AGENT == 0 and i > 0:
            # Enviar o bloco de 100 linhas para um agente processar
            # e obter o resumo
            agent = LLMAgentBlock(
                name=f'agente_{i//LINES_PER_AGENT}',
                description="Agente que processa um bloco de texto.",
                system_prompt="""Resuma o seguinte texto em no máximo 10 linhas.""",
                model='ollama/mistral-nemo:latest',
                max_iteration=0,
            )
            task = asyncio.create_task(agent.run(AgentInput(prompt="\n".join(inputs))))
            tasks.append(task)
            inputs = []

    n = len(tasks)
    c = 0
    print("Progresso: ", 0, "%", end="")
    for task in tasks:
        resumo = await task
        c += 1
        print("\rProgresso: ", (float(c)/n) * 100, "%", end="")
        resumos.append(resumo.response)

    if len(inputs) > 0:
        agent = LLMAgentBlock(
                name=f'agente_{i//LINES_PER_AGENT}',
                description="Agente que processa um bloco de texto.",
                system_prompt="""Resuma o seguinte texto em no máximo 10 linhas.""",
                model='ollama/mistral-nemo:latest',
                max_iteration=0,
            )
        resumo = await agent.run(AgentInput(prompt="\n".join(inputs)))
        resumos.append(resumo.response)

    result = await summarizer.run(AgentInput(prompt="\n".join(resumos)))

    return result.response

async def main():
    reader = open("supervisor_input.txt", "r")
    texto = reader.read()
    resultado = await supervisor_agent(texto)
    print("*"*100)
    print(resultado)

if __name__ == "__main__":
    asyncio.run(main())
