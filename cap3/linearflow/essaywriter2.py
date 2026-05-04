import asyncio
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput

async def main():
    redator_chefe = LLMAgentBlock(
        name='redator_chefe',
        description="Redator Chefe do Jornal.",
        system_prompt="""
        O editor irá te pedir para você escrever sobre um tema.
        Identifique o tema e liste resumidamente os critérios exigidos
        pelo editor. Exemplo de entrada/saída:
        Entrada: 
            "escreva uma página ou 30 linhas sobre os efeitos da inflação 
            no poder de compra do trabalhador. O texto deve ser
            bem estruturado e focar no dia do trabalhador".
        Saída: 
            "Tema: efeitos da inflação no poder de compra do trabalhador,
             Requisitos:
                - no máximo uma página ou 30 linhas,
                - texto bem estruturado (introdução, desenvolvimento, conclusão),
                - focar no dia do trabalhador.
        """,
        model='ollama/mistral-nemo:latest',
        max_iteration=0
    )

    escritor = LLMAgentBlock(
        name="escritor",
        description="colunista de cinema do jornal.",
        system_prompt="""Escreva sobre o tema respeitando os requisitos.""",
        model="ollama/mistral-nemo:latest",
        max_iteration=0,
    )

    revisor = LLMAgentBlock(
        name="revisor",
        description="colunista de cinema do jornal.",
        system_prompt="""Verifique se o texto de entrada obedece
        às diretrizes do jornal:
            - escrever de forma imparcial;
            - não usar palavrões;
            - todo o texto em português e gramaticamente correto;
            - se o texto cobre os tópicos relevantes mais atuais sobre o tema.
        Faça correções e produza o texto final (e somente o texto final, sem caracteres extras) 
        corridigo. Não escreva nenhuma nota extra.""",
        model="ollama/mistral-nemo:latest",
        max_iteration=0,
    )

    pedido = "Escreva uma matéria relembrando o bug do milênio. Seja suscinto, no máximo 3 parágrafos."
    out1 = await redator_chefe.run(AgentInput(prompt=pedido))
    print("RESULTADO 01: ")
    print(out1.response)
    out2 = await escritor.run(AgentInput(prompt=out1.response))
    print("RESULTADO 02: ")
    print(out2.response)
    out3 = await revisor.run(AgentInput(prompt=out2.response))
    print("RESULTADO 03: ")
    print(out3.response)
if __name__ == "__main__":
    asyncio.run(main())
