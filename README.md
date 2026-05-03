# Inteligência Artificial Agêntica: Teoria e Prática

Código-fonte oficial do livro **"Inteligência Artificial Agêntica: Teoria e Prática"**, de **Gilzamir Gomes**.

## Sobre o livro

Este repositório contém todos os exemplos, projetos e exercícios desenvolvidos ao longo do livro. O material abrange desde os conceitos fundamentais de agentes de IA até aplicações práticas com modelos de linguagem modernos (LLMs), cobrindo arquiteturas agênticas, padrões de design e boas práticas de desenvolvimento.

## Estrutura do repositório

```
agenticbookcode/
├── cap2/                         # Capítulo 2 — Primeiros agentes com LLMs
│   ├── EmailCheckerV1.py
│   ├── EmailCheckerV2.py
│   └── EmailCheckerV3.py
├── cap3/                         # Capítulo 3 — Agente de pesquisa
│   └── ResearchAgent/
├── cap4/                         # Capítulo 4 — Agente de vendas
│   └── SalesAgent/
│       ├── V1/
│       ├── V2/
│       └── V3/
├── cap5/                         # Capítulo 5 — Agente de vendas autônomo
│   └── AutonomousSalesAgent/
└── cap6/                         # Capítulo 6 — (em desenvolvimento)
```

## Pré-requisitos

- Python 3.10 ou superior
- Conta e chave de API na [Anthropic](https://console.anthropic.com/) (para os exemplos com Claude)
- Dependências listadas em cada capítulo (veja os `README.md` internos)

## Configuração do ambiente

1. Clone o repositório:
   ```bash
   git clone https://github.com/gilzamir/agenticbookcode.git
   cd agenticbookcode
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

3. Instale as dependências do capítulo desejado:
   ```bash
   pip install -r capN/requirements.txt
   ```

4. Configure as variáveis de ambiente copiando o arquivo de exemplo:
   ```bash
   cp .env.example .env
   # edite .env e preencha suas chaves de API
   ```

## Variáveis de ambiente

Nunca versione suas chaves de API. Use sempre um arquivo `.env` local (já incluído no `.gitignore`):

| Variável | Descrição |
|----------|-----------|
| `ANTHROPIC_API_KEY` | Chave de API da Anthropic (Claude) |
| `OPENAI_API_KEY` | Chave de API da OpenAI (se aplicável) |

## Autor

**Gilzamir Gomes**

## Licença

O código-fonte deste repositório é disponibilizado para fins educacionais, acompanhando o livro. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
