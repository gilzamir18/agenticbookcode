import asyncio

from agenticblocks import as_tool
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput
from agenticblocks.utils.parsers import extract_json_plan


# ── Main ───────────────────────────────────────────────────────────────────
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

    plan = await react_specialist.run(AgentInput(prompt="Gere o scaffolding de um app react simples."))
    print(plan.response)


if __name__ == "__main__":
    asyncio.run(main())
