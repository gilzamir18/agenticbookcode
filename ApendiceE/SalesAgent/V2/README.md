# SalesAgent v2 — TasteChat

Agente conversacional de atendimento para uma lanchonete fictícia chamada **TasteFast**. O cliente interage em linguagem natural para consultar o cardápio, montar o carrinho, informar endereço e forma de pagamento, e fechar o pedido — tudo via chat no terminal.

## Como funciona

A aplicação usa a biblioteca **agenticblocks** para orquestrar dois agentes LLM em pipeline:

```
Entrada do usuário
      │
      ▼
┌─────────────┐      Código Python (plano de ações)    ┌─────────────────┐
│  Planner    │ ──────────────────────────────────────► │  Code Plan      │
│  Agent      │                                         │  Executor       │
└─────────────┘                                         └────────┬────────┘
                                                                 │ dados reais
                                                                 ▼
                                                        ┌─────────────────┐
                                                        │ Executor Agent  │
                                                        │ (voz do chat)   │
                                                        └────────┬────────┘
                                                                 │
                                                                 ▼
                                                          Resposta ao cliente
```

- **Planner Agent**: recebe a mensagem do usuário e gera um script Python com as ações a executar (ex.: `get_cardapio()`, `adicionar_item()`, `fechar_pedido()`).
- **Code Plan Executor**: executa o script Python gerado pelo Planner chamando as ferramentas de `utils.py` e coleta os resultados.
- **Executor Agent**: recebe o briefing do Planner + os dados reais e redige a resposta final ao cliente.

### Ferramentas disponíveis

| Ferramenta             | Descrição                                                   |
|------------------------|-------------------------------------------------------------|
| `get_cardapio`         | Lista todos os itens e preços                               |
| `consultar_item`       | Verifica disponibilidade e preço de um item                 |
| `adicionar_item`       | Adiciona item ao carrinho                                   |
| `remover_item`         | Remove item do carrinho                                     |
| `ver_carrinho`         | Exibe o carrinho atual com totais                           |
| `registrar_endereco`   | Registra o endereço de entrega                              |
| `registrar_pagamento`  | Registra a forma de pagamento (pix/cartão/dinheiro)         |
| `fechar_pedido`        | Finaliza o pedido (exige endereço e pagamento cadastrados)  |

---

## Pré-requisitos

- Python 3.11+
- [agenticblocks](https://github.com/gilzamir18/agenticblocks) instalado
- [LiteLLM](https://docs.litellm.ai/) (instalado como dependência do agenticblocks)
- [Ollama](https://ollama.com) (se for usar modelo local)

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/gilzamir18/SalesAgentv2.git
cd SalesAgentv2
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv .venv
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

**Windows (cmd):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

```bash
pip install agenticblocks.io litellm
```

---

## Executando a aplicação

```bash
python app.py
```

Por padrão, o projeto usa o modelo **`ollama/mistral-nemo:latest`** rodando localmente via [Ollama](https://ollama.com).

Antes de executar, certifique-se de que o servidor Ollama está ativo:

```bash
ollama serve
```

E que o modelo está disponível:

```bash
ollama pull mistral-nemo:latest
```

---

## Usando um modelo comercial (ex.: Google Gemini)

Para trocar o modelo local por um modelo comercial, altere o parâmetro `model` nos agentes em [app.py](app.py).

### 1. Alterar o modelo em `app.py`

```python
# Antes
model="ollama/mistral-nemo:latest"

# Depois — Gemini via LiteLLM
model="gemini/gemini-2.0-flash"
```

> O LiteLLM suporta vários provedores. Consulte a [lista completa de modelos](https://docs.litellm.ai/docs/providers).

### 2. Configurar a API Key

**Linux / macOS:**

```bash
export GEMINI_API_KEY="sua-chave-aqui"
python app.py
```

**Windows (cmd):**
```cmd
set GEMINI_API_KEY=sua-chave-aqui
python app.py
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "sua-chave-aqui"
python app.py
```

### 3. Provedores suportados pelo LiteLLM

| Provedor         | Variável de ambiente  | Prefixo do modelo             |
|------------------|-----------------------|-------------------------------|
| Google Gemini    | `GEMINI_API_KEY`      | `gemini/...`                  |
| OpenAI           | `OPENAI_API_KEY`      | `gpt-4o`, `gpt-4o-mini`       |
| Anthropic Claude | `ANTHROPIC_API_KEY`   | `claude-opus-4-7`, etc.       |
| Groq             | `GROQ_API_KEY`        | `groq/llama-3.1-8b-instant`   |
| Ollama (local)   | *(sem chave)*         | `ollama/<nome-do-modelo>`     |

---

## Estrutura do projeto

```
SalesAgentv2/
├── app.py        # Orquestração dos agentes e loop de chat
├── utils.py      # Ferramentas do domínio (cardápio, carrinho, pedido)
└── .env.example  # Exemplo de variáveis de ambiente (copie para .env)
```

---

## Licença

Distribuído para fins educacionais e de demonstração.
