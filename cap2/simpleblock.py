from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
import asyncio

async def main():
    block = LLMAgentBlock(
        model="ollama/mistral-nemo:latest",
        system_prompt="Você apenas responde o que sabe!",
        max_iterations=0
    )
    output = await block.run("O que é um agente?")
    print(output)