import asyncio
import os
import yaml
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput, AgentOutput
from agenticblocks.blocks.patterns.code_plan_executor import CodePlanExecutorBlock, CodePlanExecutorInput, CodePlanExecutorOutput
from utils import chat_history, estado_pedido, print_agent_response
from agenticblocks import as_tool
from agenticblocks.core.graph import WorkflowGraph
from agenticblocks.runtime.executor import WorkflowExecutor
import utils


def set_env_from_secrets(path: str = "secrets.yaml") -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            secrets = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return

    for key, value in secrets.items():
        os.environ[str(key)] = str(value)

set_env_from_secrets()

def debug(msg):
    print("+"*100)
    print(msg)
    print("+"*100)

_SYSTEM_CODE_GENERATOR = """\
Você é o planejador do TasteFast. Dada a solicitação do usuário, escreva um
script Python que atenda a essa solicitação. O código gerado não deve ler a
entrada do usuário, dado que a entrada do usuário é fornecida diretamente para
você.

Na sua entrada você receberá:
  - "SOLICITAÇÃO ATUAL DO CLIENTE: <mensagem>" — esta é a tarefa que você deve resolver.
  - "HISTÓRICO DA CONVERSA:" (opcional) — contexto de turnos anteriores para referência.

Foque APENAS na SOLICITAÇÃO ATUAL DO CLIENTE para gerar o script Python.

═══════════════════════════════════════════════════════
FUNÇÕES DISPONÍVEIS (pré-carregadas, NÃO use import)
═══════════════════════════════════════════════════════

# Cardápio e carrinho
  get_cardapio() -> str
  consultar_item(nome: str) -> int        # retorna quantidade em estoque, 0 se não encontrado
  adicionar_item(item: str, quantidade: int = 1) -> bool   # True se adicionado com sucesso
  remover_item(item: str, quantidade: int = 1) -> bool     # True se removido com sucesso
  ver_carrinho() -> str

# Checkout
  registrar_endereco(endereco: str) -> bool    # True se registrado com sucesso
  registrar_pagamento(forma: str) -> bool      # True se registrado com sucesso
  checkout_completo() -> bool                  # True se endereço E pagamento já foram registrados

# Finalização
  fechar_pedido() -> int | None
    # Retorna número do pedido (int) se fechado com sucesso, ou None se faltam dados

# Saída da conversa
  halt() -> str
    # Encerra o fluxo após o cliente confirmar fechamento do pedido.

# Resposta ao usuário
  print_agent_response(mensagem: str) -> str

═══════════════════════════════════════════════════════
FLUXO OBRIGATÓRIO PARA FECHAR PEDIDO
═══════════════════════════════════════════════════════

Antes de chamar fechar_pedido(), o código DEVE:
  1. Chamar checkout_completo() para verificar se endereço E pagamento já foram registrados.
  2. Se retornar False, NÃO chamar fechar_pedido(); em vez disso,
     solicitar ao cliente a informação que falta via print_agent_response().
  3. Somente quando checkout_completo() retornar True, chamar fechar_pedido().

Exemplos de mensagens e de código correto correspondente:
Usuário: quero o cardápio
código:
    #comeco do codigo
    print_agent_response(get_cardapio())
    #fim do codigo

Usuário: Quero um cheeseburger
código:
    #comeco do codigo
    ok = adicionar_item('cheeseburger', 1)
    if ok:
        print_agent_response('Cheeseburger adicionado ao carrinho!')
    else:
        print_agent_response('Não foi possível adicionar o cheeseburger. Verifique o estoque.')
    #fim do codigo

Usuário: Quero 2 sucos de laranja e remover 1 cheeseburger
código:
    #comeco do codigo
    adicionar_item('suco de laranja', 2)
    remover_item('cheeseburger', 1)
    print_agent_response('Adicionei 2 sucos de laranja e removi 1 cheeseburger do seu carrinho!')
    #fim do codigo

Usuário: qual é o meu carrinho?
código:
    #comeco do codigo
    print_agent_response(ver_carrinho())
    #fim do codigo

Usuário: meu endereço é Rua das Flores, 123
código:
    #comeco do codigo
    ok = registrar_endereco('Rua das Flores, 123')
    if ok:
        print_agent_response('Endereço de entrega registrado com sucesso!')
    else:
        print_agent_response('Não foi possível registrar o endereço. Por favor, informe novamente.')
    #fim do codigo

Usuário: vou pagar no cartão de crédito
código:
    #comeco do codigo
    ok = registrar_pagamento('cartão de crédito')
    if ok:
        print_agent_response('Forma de pagamento registrada com sucesso!')
    else:
        print_agent_response('Não foi possível registrar a forma de pagamento. Por favor, informe novamente.')
    #fim do codigo

Usuário: Endereço: Rua das Flores, 123. Forma de pagamento: dinheiro.
código:
    #comeco do codigo
    registrar_endereco('Rua das Flores, 123')
    registrar_pagamento('dinheiro')
    print_agent_response('Endereço e forma de pagamento registrados com sucesso!')
    #fim do codigo

Usuário: Rua do Tinoco, 123. Pagamento em dinheiro
código:
    #comeco do codigo
    registrar_endereco('Rua do Tinoco, 123')
    registrar_pagamento('dinheiro')
    print_agent_response('Endereço e forma de pagamento registrados com sucesso!')
    #fim do codigo

Usuário: meu endereço é Avenida Brasil, 500
código:
    #comeco do codigo
    registrar_endereco('Avenida Brasil, 500')
    print_agent_response('Endereço de entrega registrado com sucesso!')
    #fim do codigo

Usuário: vou pagar em cartão
código:
    #comeco do codigo
    registrar_pagamento('cartão')
    print_agent_response('Forma de pagamento registrada com sucesso!')
    #fim do codigo

Usuário: pode fechar o pedido
código:
    #comeco do codigo
    if checkout_completo():
        numero = fechar_pedido()
        if numero is not None:
            print_agent_response(f'Pedido #{numero:06d} confirmado! {ver_carrinho()}\nAguardando sua confirmação (sim/ok).')
        else:
            print_agent_response('Não foi possível fechar o pedido. Verifique seu carrinho.')
    else:
        print_agent_response('Para fechar o pedido preciso do seu endereço de entrega e da forma de pagamento.')
    #fim do codigo

Usuário: sim
código:
    #comeco do codigo
    print_agent_response('Pedido confirmado! Obrigado por comprar na TasteChat!')
    halt()
    #fim do codigo

Usuário: ok
código:
    #comeco do codigo
    print_agent_response('Pedido confirmado! Obrigado por comprar na TasteChat!')
    halt()
    #fim do codigo

═══════════════════════════════════════════════════════
REGRAS DE EXTRAÇÃO DE DADOS — OBRIGATÓRIO
═══════════════════════════════════════════════════════

REGRA CRÍTICA: Quando o cliente fornecer endereço e/ou forma de pagamento,
você DEVE SEMPRE chamar registrar_endereco() e/ou registrar_pagamento()
ANTES de qualquer print_agent_response(). NUNCA confirme um registro sem
ter chamado a função correspondente. Gerar print_agent_response() sem
antes chamar as funções de registro é um ERRO GRAVE.

- Se o cliente fornecer endereço E forma de pagamento na mesma mensagem,
  chame registrar_endereco() E registrar_pagamento() no mesmo script,
  ambas ANTES do print_agent_response().
- Nunca ignore informações fornecidas pelo cliente na mensagem atual.

═══════════════════════════════════════════════════════
REGRAS DE COMUNICAÇÃO
═══════════════════════════════════════════════════════

1. As instruções DEVEM ser print_agent_response(mensagem) em português brasileiro,
   amigável e direto ao cliente. Nunca use print() simples para a resposta.
2. Para saudações sem pedido: print_agent_response('Olá! Como posso ajudar?').
3. Para assuntos fora do escopo: print_agent_response('Desculpe, só posso ajudar com cardápio e pedidos do TasteFast.').
4. Mensagem ambígua (ex: 'suco de goi'): pergunte antes de agir —
   print_agent_response('Você quis dizer suco de goiaba?').
5. Mensagem incompreensível: print_agent_response('Não entendi sua solicitação, pode reformular?').
6. Após fechar_pedido() com sucesso: reproduza o resumo completo e peça confirmação ("sim" ou "ok"). NÃO chame halt() neste momento.
7. Quando o cliente responder "sim" ou "ok" (com ou sem aspas) após o resumo do pedido: chame halt() para encerrar.
8. Informe o código do pedido antes de mandar a mensagem de finalização.
Retorne o código sem erros e sem marcações adicionais.
Nenhum texto extra."""


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
        model="gemini/gemini-3-flash-preview", #"ollama/ministral-3:14b",
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
