import asyncio
from pathlib import Path
from agenticblocks import as_tool
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks.utils.parsers import extract_json_plan
from agenticblocks.blocks.patterns.code_plan_executor import CodePlanExecutorBlock, CodePlanExecutorInput, CodePlanExecutorOutput
import sys, os

_SYSTEM_CODE_GENERATOR = Path(__file__).resolve().parent.joinpath("CODE_AGENT.md").read_text(encoding="utf-8")

async def main():
    react_specialist = LLMAgentBlock(
        name="react_specialist",
        model="ollama/mistral-nemo:latest",
        system_prompt= _SYSTEM_CODE_GENERATOR,
        tools=[],
        max_iterations=1,
        litellm_kwargs={"temperature": 0.0},
    )

    # Nota: É necessário ter o Docker rodando na máquina para este exemplo funcionar.
    code_planner = CodePlanExecutorBlock(
        executor_agent=react_specialist,
        execution_mode="local",
        inject_module=[os, sys],
        max_entries=10
    )

    executor_input = CodePlanExecutorInput(task="Gere o scaffolding de um app react simples.")
    plan_output = await code_planner.run(executor_input)

    print("FINAL RESPONSE: \n\n")
    print(plan_output)

if __name__ == "__main__":
    asyncio.run(main())
