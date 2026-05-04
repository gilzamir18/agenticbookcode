import asyncio
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput

async def main():
    redator = LLMAgentBlock(
        name='redator',
        description="colunista de cinema do jornal.",
        system_prompt="""Você deve escrever no máximo 30 linhas sobre filmes de romance vencedores do Oscar.""",
        model='ollama/mistral-nemo:latest',
        max_iteration=0
    )

    revisor = LLMAgentBlock(
        name="revisor",
        description="revisor de redações sobre filmes de romance",
        system_prompt="""Revise a redação de entrada, não escreva mais de 30 linhas, verifique se redação de entrada menciona filmes famosos, como Titanic. Caso não cite, faça mudanças mencionando estes filmes.""",
        model="ollama/mistral-nemo:latest",
        max_iteration=0,
    )

    pedido = "Escreva uma redação sobre filmes de romance que já ganharam Oscar."
    out1 = await redator.run(AgentInput(prompt=pedido))
    print("RESULTADO 01: ")
    print(out1.response)
    out2 = await revisor.run(AgentInput(prompt=out1.response))
    print("RESULTADO 02: ")
    print(out2.response)

if __name__ == "__main__":
    asyncio.run(main())