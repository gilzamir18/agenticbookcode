import asyncio
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks import as_tool
import math
from agenticblocks import as_tool

MODEL = "ollama/mistral-nemo:latest"

@as_tool
def sqrt(s: float) -> float:
    return math.sqrt(sqrt)

@as_tool
def soma(a: float, b: float) -> float:
    return a+b

def prod(a: float, b: float) -> float:
    return a * b

def div(a: float, b: float) -> float:
    return a/b

def pot(a: float, b: float) -> float:
    return a**b

async def main():

    calculador = LLMAgentBlock(
        name="calculador",
        description="Calcula o que o usuário pede.",
        system_prompt="""O usuário pode pedir a alguma operação matemática.
        Combine as ferramentas para realizar esta operação.""",
        model=MODEL,
        tools=[sqrt, soma],
        debug=True,
        max_iterations=4
    )

    resultado = await calculador.run(AgentInput(prompt="Calcule a soma de 1+1"))
    print(resultado)

if __name__ == "__main__":
    asyncio.run(main())

