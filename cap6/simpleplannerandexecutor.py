import asyncio
from agenticblocks import as_tool
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks.utils.parsers import extract_json_plan
from agenticblocks.blocks.patterns.plan_executor import PlanExecutorBlock, PlanExecutorInput

from utils import (
    mkdir, create_txt_file, append_content, remover_arquivo, remove_dir,
    validate_reply, build_chat_prompt,
)

@as_tool
def print_response(resp: str) -> None:
    print("Agent *_-_*: ", resp)
    return None

async def main():
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
            '  - "print_agent_response": args = {"response": "<msg>"}. Envia uma mensagem ao usuário. \n'
            '  - "reply": args = {"message": "<briefing para o executor>"}. SEMPRE o último passo.\n\n' 
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

    plan_executor_assistent = LLMAgentBlock(
        name="plan_executor_assistent",
        description="Assistente do executor de plano",
        system_prompt="Você ajuda na execução do plano, informando "
        "o usuário final sobre o progresso e os resultados da execução."
        "use a ferramenta print_response para responder ao usuário.",
        model="ollama/mistral-nemo:latest",
        tools=[print_response],
        max_iterations=2
    )

    plan_executor = PlanExecutorBlock(
        executor_agent=plan_executor_assistent,
        tools=[mkdir, create_txt_file, append_content, remover_arquivo, remove_dir],
        validate_reply=validate_reply,
        max_reply_retries=2
    )

    #A saida do planejador
    plan_output = await react_specialist.run(AgentInput(prompt="Gere o scaffolding de um app react simples."))
    #A saida em modo texto
    plan_str = plan_output.response 

    #Transforma o plano em um objeto JSON
    plan = extract_json_plan(plan_str)
    #Se falha, obtém um plano de fallback
    if plan is None:
        plan = {
            "thought": "fallback",
            "steps": [{"action": "reply", "args": {
                "message": "Desculpe, não consegui processar o pedido. Pode descrever novamente?"
            }}],
        }
    #Efetivamente executa o plano
    output = await plan_executor.run(PlanExecutorInput(plan=plan, history=""))
    print("FINAL RESPONSE: \n\n", output.response)

if __name__ == "__main__":
    asyncio.run(main())
