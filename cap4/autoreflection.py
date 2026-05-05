import asyncio
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
import time
from agenticblocks import as_tool

@as_tool
async def refletidor(text: str) -> str:
    agente_reflexivo = LLMAgentBlock(
        name="agente_reflexivo",
        description="Agente auto-reflexivo.",
        system_prompt="""Reflita sobre o texto fornecido. Produza no máximo 10 linhas.""",
        model="ollama/mistral-nemo:latest",
        max_iterations=0
    )
    result = await agente_reflexivo.run(AgentInput(prompt=text))
    resp = result.response
    print("+" * 100)
    print("REFLETIDOR OUTPUT: ")
    print(resp)
    print("+" * 100)
    return resp

async def main():
    agente_principal = LLMAgentBlock(
        name="agente_reflexivo",
        description="Agente auto-reflexivo.",
        system_prompt="""Você receberá uma ideia incial, use o
        refletidor para refletir sobre o tema e retorne o resultado.
        Nunca retorne o seu próprio resultado, sempre retorne o que 
        for produzido pelo refletidor.""",
        model="ollama/mistral-nemo:latest",
        tools=[refletidor],
        debug=True,
        max_tool_calls=1,
        max_iterations=1
    )

    inicio = time.perf_counter()
    resposta = await agente_principal.run(AgentInput(prompt="Reflita sobre a condição humana sem trabalho."))
    duracao = time.perf_counter() - inicio

    print("#" * 200)
    print(resposta.response)
    print("#" * 200)
    print(f"Tempo de execução: {duracao:.4f}s")

if __name__ == "__main__":
    asyncio.run(main())

