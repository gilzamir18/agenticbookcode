"""
Sistema Multi-Agente Todos-para-Todos (All-to-All)
===================================================

Todos os agentes compartilham um quadro (blackboard) comum.
Cada agente lê o quadro inteiro e acrescenta sua contribuição.
Um moderador decide quando a discussão está completa.

Fluxo de comunicação:

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Historiador │◄───►│  Cientista  │◄───►│   Filósofo  │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  QUADRO COMPARTILHADO│  ← blackboard
                    └──────────┬──────────┘
                               ▼
                        ┌─────────────┐
                        │  Moderador  │  ← decide quando encerrar
                        └─────────────┘
"""

import asyncio
from agenticblocks.blocks.llm.agent import LLMAgentBlock, AgentInput

MODEL = "ollama/mistral-nemo:latest"
MAX_RODADAS = 3


def formatar_quadro(quadro: list[str]) -> str:
    return "\n".join(f"[{i+1}] {msg}" for i, msg in enumerate(quadro))


async def main():
    historiador = LLMAgentBlock(
        name="historiador",
        system_prompt=(
            "Você é um historiador. Leia o quadro compartilhado e contribua "
            "com 2-3 frases sobre a perspectiva histórica do tema. "
            "Responda SOMENTE com sua contribuição, sem prefácio."
        ),
        model=MODEL,
        max_iteration=0,
    )

    cientista = LLMAgentBlock(
        name="cientista",
        system_prompt=(
            "Você é um cientista. Leia o quadro compartilhado e contribua "
            "com 2-3 frases sobre a perspectiva científica do tema. "
            "Responda SOMENTE com sua contribuição, sem prefácio."
        ),
        model=MODEL,
        max_iteration=0,
    )

    filosofo = LLMAgentBlock(
        name="filósofo",
        system_prompt=(
            "Você é um filósofo. Leia o quadro compartilhado e contribua "
            "com 2-3 frases sobre a perspectiva filosófica do tema. "
            "Responda SOMENTE com sua contribuição, sem prefácio."
        ),
        model=MODEL,
        max_iteration=0,
    )

    moderador = LLMAgentBlock(
        name="moderador",
        system_prompt=(
            "Você é o moderador da discussão. Avalie o quadro compartilhado. "
            "Se houver contribuições de pelo menos três perspectivas distintas, "
            "responda com 'ENCERRAR' seguido de um resumo de 3 linhas. "
            "Caso contrário, responda apenas 'CONTINUAR'."
        ),
        model=MODEL,
        max_iteration=0,
    )

    agentes = [historiador, cientista, filosofo]
    nomes = ["Historiador", "Cientista", "Filósofo"]

    tema = "O impacto da inteligência artificial na sociedade humana."
    quadro: list[str] = [f"TEMA: {tema}"]

    print("=" * 60)
    print("DISCUSSÃO TODOS-PARA-TODOS")
    print("=" * 60)
    print(f"Tema: {tema}\n")

    for rodada in range(1, MAX_RODADAS + 1):
        print(f"--- Rodada {rodada} ---")

        # Todos os agentes leem o quadro e contribuem em paralelo
        contexto = f"Quadro compartilhado:\n{formatar_quadro(quadro)}"
        respostas = await asyncio.gather(
            *[agente.run(AgentInput(prompt=contexto)) for agente in agentes]
        )

        # Cada contribuição é adicionada ao quadro, visível a todos
        for nome, resposta in zip(nomes, respostas):
            contribuicao = f"[{nome}] {resposta.response}"
            quadro.append(contribuicao)
            print(f"{nome}: {resposta.response}\n")

        # O moderador avalia se a discussão está completa
        avaliacao = await moderador.run(
            AgentInput(prompt=f"Quadro compartilhado:\n{formatar_quadro(quadro)}")
        )
        print(f"Moderador: {avaliacao.response}\n")

        if "ENCERRAR" in avaliacao.response.upper():
            break

    print("=" * 60)
    print("DISCUSSÃO ENCERRADA")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
