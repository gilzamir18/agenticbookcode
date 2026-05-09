import asyncio

from agenticblocks import as_tool
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor
from agenticblocks.utils.parsers import extract_json_plan
from agenticblocks.blocks.patterns.plan_executor import PlanExecutorBlock, PlanExecutorInput
from utils import (
    mkdir, create_txt_file, append_content, remover_arquivo, remove_dir,
    validate_reply, build_chat_prompt,
)

# ── Estado da conversa ─────────────────────────────────────────────────────
chat_history = []

# ── Ferramentas de saída ao usuário ───────────────────────────────────────
@as_tool(name="print_agent_response", description="Envia a resposta final ao usuário.")
def print_agent_response(response: str) -> str:
    print(f"Agente: {response}")
    chat_history.append(f"Agente: {response}")
    return "ok"

# ── Bloco de turno: plan + execute ────────────────────────────────────────
def make_turn_block(planner_agent: LLMAgentBlock, plan_executor: PlanExecutorBlock):
    @as_tool(name="plan_and_execute_turn", description="Gera plano JSON e executa.")
    async def plan_and_execute_turn(user_message: str) -> str:
        if isinstance(user_message, dict):
            user_message = user_message.get("user_message") or str(user_message)
        user_message = str(user_message).strip()

        chat_history.append(f"Usuário: {user_message}")
        history_str = "\n".join(chat_history[-8:])

        planner_prompt = (
            f"HISTÓRICO RECENTE:\n{history_str}\n\n"
            f"MENSAGEM DO USUÁRIO: {user_message}\n\n"
            "Produza APENAS o JSON do plano. Sem texto antes ou depois."
        )

        plan_result = await planner_agent.run(AgentInput(prompt=planner_prompt))
        raw = getattr(plan_result, "response", str(plan_result))

        plan = extract_json_plan(raw)
        if plan is None:
            plan = {
                "thought": "fallback",
                "steps": [{"action": "reply", "args": {
                    "message": "Desculpe, não consegui processar o pedido. Pode descrever novamente?"
                }}],
            }

        output = await plan_executor.run(PlanExecutorInput(plan=plan, history=history_str))
        return output.response

    return plan_and_execute_turn


# ── Controle de fluxo do chat ──────────────────────────────────────────────
@as_tool(name="get_user_input")
def get_user_input() -> dict:
    print("Você: ", end="", flush=True)
    return {"user_message": input().strip()}


_ENCERRAMENTOS = {"sair", "tchau", "adeus", "até mais", "finalizar", "encerrar", "exit", "quit"}


@as_tool(name="check_done")
def check_done(last_message: str = "") -> dict:
    for line in reversed(chat_history):
        if line.startswith("Usuário:"):
            last_user = line[len("Usuário:"):].strip().lower()
            if last_user in _ENCERRAMENTOS:
                return {"is_valid": True, "feedback": "encerrado"}
            break
    return {"is_valid": False, "feedback": "continuar"}


# ── Main ───────────────────────────────────────────────────────────────────
async def main():
    executor_agent = LLMAgentBlock(
        name="executor_agent",
        model="ollama/mistral-nemo:latest",
        description="Redige a mensagem final ao usuário.",
        system_prompt=(
            "Você é um assistente especialista em React.\n"
            "Seu único trabalho é chamar a ferramenta 'print_agent_response' UMA vez "
            "com a mensagem final ao usuário.\n\n"
            "REGRAS:\n"
            "1. OBRIGATÓRIO: chame 'print_agent_response' exatamente UMA vez.\n"
            "2. Se arquivos foram criados com sucesso, informe o usuário de forma clara.\n"
            "3. Se houve erros, relate-os de forma amigável.\n"
            "4. Seja breve e objetivo em português brasileiro.\n"
        ),
        tools=[print_agent_response],
        max_tools_calls=1,
        max_iterations=1,
        litellm_kwargs={"temperature": 0.0},
    )

    react_specialist = LLMAgentBlock(
        name="react_specialist",
        model="ollama/mistral-nemo:latest",
        system_prompt=(
            "Você é o Planejador de projetos React. "
            "NÃO fala com o usuário. NÃO chama ferramentas. "
            "Sua ÚNICA saída é um JSON válido.\n\n"
            "Formato OBRIGATÓRIO (apenas JSON, nada mais):\n"
            "{\n"
            '  "thought": "raciocínio Logicamente, breve",\n'
            '  "steps": [ {"action": "<nome>", "args": { ... }} ]\n'
            "}\n\n"
            "AÇÕES DISPONÍVEIS:\n"
            '  - "mkdir":           args = {"dir": "<path>"}. Cria um diretório.\n'
            '  - "create_txt_file": args = {"path": "<path>", "ext": "<extensão>"}. Cria um arquivo vazio.\n'
            '  - "append_content":  args = {"file": "<path>", "content": "<texto>"}. Adiciona conteúdo ao arquivo.\n'
            '  - "remover_arquivo": args = {"file": "<path>"}. Remove o arquivo.\n'
            '  - "remove_dir":      args = {"path": "<path>"}. Remove o diretório.\n'
            '  - "print_agent_response": args = {"response": "<msg>"} Envia uma mensagem ao usuário. \n'
            '  - "reply":           args = {"message": "<briefing para o executor>"}. SEMPRE o último passo.\n\n' 
            "REGRAS:\n"
            "1. SEMPRE termine com um passo 'reply'.\n"
            "2. Somente aceite pedidos sobre React. Para qualquer outro assunto, "
            "gere apenas: reply com message 'Somente atendo pedidos sobre React!'.\n"
            "3. Saída: APENAS o JSON, sem ```, sem comentários, sem texto extra.\n"
        ),
        tools=[],
        max_iterations=1,
        litellm_kwargs={"temperature": 0.0},
    )

    plan_executor = PlanExecutorBlock(
        executor_agent=executor_agent,
        tools=[mkdir, create_txt_file, append_content, remover_arquivo, remove_dir],
        validator_fn=validate_reply,
        max_reply_retries=2,
        reply_prompt_template=(
            "BRIEFING DO PLANNER:\n{briefing}\n\n"
            "DADOS REAIS A USAR:\n{observations}\n\n"
            "HISTÓRICO RECENTE:\n{history}\n\n"
            "{extra_instruction}\n"
            "Agora chame a ferramenta 'print_agent_response' UMA vez com a mensagem final ao usuário."
        )
    )

    print("Bem-vindo à CoderBase, a maior software house autônoma do mundo!")
    print("Descreva o projeto React que deseja criar. Digite 'sair' para encerrar.\n")

    turn_block = make_turn_block(react_specialist, plan_executor)

    graph = WorkflowGraph()
    graph.add_block(get_user_input)
    graph.add_block(turn_block)
    graph.add_block(check_done)

    graph.add_cycle(
        name="chat_loop",
        sequence=["get_user_input", "plan_and_execute_turn", "check_done"],
        condition_block="check_done",
        max_iterations=1000,
        augment_fn=build_chat_prompt,
    )

    executor = WorkflowExecutor(graph, verbose=False)
    await executor.run(initial_input={"prompt": "início"})

if __name__ == "__main__":
    asyncio.run(main())
