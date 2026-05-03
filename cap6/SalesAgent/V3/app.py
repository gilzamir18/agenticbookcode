import asyncio
from pathlib import Path
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput, AgentOutput
from agenticblocks.blocks.patterns.code_plan_executor import CodePlanExecutorBlock, CodePlanExecutorInput, CodePlanExecutorOutput
from utils import chat_history, estado_pedido, print_agent_response
from agenticblocks import as_tool
from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor
import utils


def debug(msg):
    print("+"*100)
    print(msg)
    print("+"*100)

_SYSTEM_CODE_GENERATOR = Path(__file__).resolve().parent.joinpath("SALES.md").read_text(encoding="utf-8")

class ObservableLLM(LLMAgentBlock):
    async def run(self, input: AgentInput) -> AgentOutput:
        #print("="*50)
        #print(input)
        #print("="*50)
        return await super().run(input)

@as_tool(name="get_user_input")
def get_user_input(prompt: str):
    print("Você: ", end="")
    user_input = input()
    chat_history.append(f"Você: {user_input}")
    history = "\n".join(chat_history[:-1])
    if history:
        return f"SOLICITAÇÃO ATUAL DO CLIENTE: {user_input}\n\nHISTÓRICO DA CONVERSA:\n{history}"
    return f"SOLICITAÇÃO ATUAL DO CLIENTE: {user_input}"

@as_tool(name="condition_block")
def test_end_of_loop(obj: CodePlanExecutorOutput) -> dict:  # noqa: ARG001
    agent_output = obj.execution_stdout or ""
    debug(obj.code_generated)
    if obj.execution_stderr and obj.execution_stderr.strip():
        print(f"[ERRO NO CÓDIGO GERADO]\n{obj.execution_stderr.strip()}")
    if agent_output.strip():
        print(agent_output, end="" if agent_output.endswith("\n") else "\n")
    else:
        print("Vendedor: Desculpe, não consegui processar sua solicitação. Pode repetir?")
    if "halt" in agent_output:
        print("Vendedor: Obrigado por comprar na TasteChat! Volte sempre!")
        return {
            'is_valid': True, 'feedback': ''
        }
    else:
        return {
            'is_valid': False, 'feedback': "\n".join(chat_history)
        }


async def main():
    agent = ObservableLLM(
        name="code_generator",
        model="ollama/ministral-3:14b",
        system_prompt=_SYSTEM_CODE_GENERATOR,
        max_iterations=3,
        litellm_kwargs={'temperature':0.3, 'num_ctx': 32000}
    )

    # Nota: É necessário ter o Docker rodando na máquina para este exemplo funcionar.
    code_planner = CodePlanExecutorBlock(
        executor_agent=agent,
        execution_mode="local",
        inject_module=[utils],
        max_entries=10
    )

    graph = WorkflowGraph()
    graph.add_block(get_user_input)
    graph.add_block(code_planner)
    graph.add_block(test_end_of_loop)
    graph.add_cycle(
        name="negociation_loop",
        sequence=["get_user_input", code_planner.name, "condition_block"],
        condition_block="condition_block",
        max_iterations=1000,
        augment_fn=lambda _orig, _it, _prod, feedback: feedback or ""
    )

    await WorkflowExecutor(graph, verbose=False).run(initial_input={"prompt": "início"})

if __name__ == "__main__":
    asyncio.run(main())
