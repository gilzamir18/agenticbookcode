from collections import namedtuple
import time

# ── Estado de conversa ─────────────────────────────────────────────────────

chat_history = []

def print_agent_response(response: str) -> str:
    print(f"Vendedor: {response}")
    chat_history.append(f"Vendedor: {response}")
    return "ok"

def halt():
    print("/halt")


# ── Domínio ────────────────────────────────────────────────────────────────

Produto = namedtuple('Produto', ['id', 'nome', 'descricao', 'preco', 'quantidade_em_estoque',
                                 'negociavel', 'precoMin', 'condicaoNegociacao'])

produtos: dict[int, Produto] = {
    0: Produto(0, 'cheeseburger',
               'Cheeseburger com pão sem gergelim, queijo mussarela, ovo estrelado, cebola e alface',
               15.0, 10, False, 15.0, ""),
    1: Produto(1, 'suco de laranja',
               'Suco de laranja, copo de 250 ml sem açúcar.',
               8.0, 100, False, 8.0, ""),
    2: Produto(2, 'suco de polpa',
               '250 ml de suco de polpa. Opções disponíveis: abacaxi, goiaba, acerola e caju',
               6.0, 100, False, 6.0, ""),
    3: Produto(3, 'coxinha de frango',
               'Coxinha de frango',
               6.0, 10, False, 6.0, ""),
    4: Produto(4, 'pudim de leite',
               'Porção de 100g de pudim de leite',
               10.0, 10, True, 8.0,
               "Apenas para clientes que tenham comprado um cheeseburger e um suco de laranja."),
}

carrinho_ativo: dict[int, int] = {}
checkout_info: dict[str, str] = {}
estado_pedido: dict[str, bool] = {"fechado": False}


# ── DAO de Produtos ────────────────────────────────────────────────────────

def buscar_produto(nome: str) -> Produto | None:
    nome_up = nome.strip().upper()
    for p in produtos.values():
        if nome_up == p.nome.upper() or nome_up in p.nome.upper() or nome_up in p.descricao.upper():
            return p
    return None


def listar_produtos() -> list[Produto]:
    return list(produtos.values())


# ── DAO do Carrinho ────────────────────────────────────────────────────────

def qtd_no_carrinho(produto_id: int) -> int:
    return carrinho_ativo.get(produto_id, 0)


def itens_do_carrinho() -> dict[Produto, int]:
    return {produtos[pid]: qtd for pid, qtd in carrinho_ativo.items()}


def total_do_carrinho() -> float:
    return sum(produtos[pid].preco * qtd for pid, qtd in carrinho_ativo.items())


# ── Modelo de Negócio ──────────────────────────────────────────────────────

def adicionar_item(item: str, quantidade: int = 1) -> bool:
    p = buscar_produto(item)
    if p is None:
        return False
    disponivel = p.quantidade_em_estoque - qtd_no_carrinho(p.id)
    if quantidade > disponivel:
        return False
    carrinho_ativo[p.id] = qtd_no_carrinho(p.id) + quantidade
    return True


def remover_item(item: str, quantidade: int = 1) -> bool:
    p = buscar_produto(item)
    if p is None:
        return False
    no_carrinho = qtd_no_carrinho(p.id)
    if no_carrinho == 0:
        return False
    nova_qtd = no_carrinho - quantidade
    if nova_qtd <= 0:
        del carrinho_ativo[p.id]
    else:
        carrinho_ativo[p.id] = nova_qtd
    return True


def consultar_item(item: str) -> int:
    p = buscar_produto(item)
    if p is None:
        return 0
    return p.quantidade_em_estoque


def registrar_endereco(endereco: str) -> bool:
    if not endereco or not endereco.strip():
        return False
    checkout_info["endereco"] = endereco.strip()
    return True


def registrar_pagamento(forma: str) -> bool:
    if not forma or not forma.strip():
        return False
    checkout_info["pagamento"] = forma.strip()
    return True


def checkout_completo() -> bool:
    return "endereco" in checkout_info and "pagamento" in checkout_info


def fechar_pedido() -> int | None:
    """Fecha o pedido e retorna o número do pedido, ou None se não for possível fechar."""
    if not carrinho_ativo or not checkout_completo():
        return None
    numero_pedido = int(time.time() * 1000) % 1_000_000
    for pid, qtd in carrinho_ativo.items():
        p = produtos[pid]
        produtos[pid] = p._replace(quantidade_em_estoque=p.quantidade_em_estoque - qtd)
    carrinho_ativo.clear()
    checkout_info.pop("endereco")
    checkout_info.pop("pagamento")
    estado_pedido["fechado"] = True
    return numero_pedido


# ── Consultas de Apoio ─────────────────────────────────────────────────────

def get_cardapio() -> str:
    lines = ["Cardápio do TasteFast:"]
    for p in produtos.values():
        status = f"{p.quantidade_em_estoque} disponível(is)" if p.quantidade_em_estoque > 0 else "indisponível"
        lines.append(f"  - {p.nome} | R$ {p.preco:.2f} | {status}")
    return "\n".join(lines)


def ver_carrinho() -> str:
    if not carrinho_ativo:
        return "Carrinho vazio."
    lines = ["Seu carrinho:"]
    for p, qtd in itens_do_carrinho().items():
        subtotal = qtd * p.preco
        lines.append(f"  {qtd}x {p.nome} – R$ {p.preco:.2f} cada = R$ {subtotal:.2f}")
    lines.append(f"Total: R$ {total_do_carrinho():.2f}")
    return "\n".join(lines)


# ── Validador de resposta ──────────────────────────────────────────────────

def validate_reply(reply: str, observations: list) -> tuple[bool, str]:
    if not reply or not reply.strip():
        return False, "Resposta vazia."
    reply_low = reply.lower()
    itens_cardapio = {p.descricao.lower() for p in produtos.values()}
    suspeitos = ["salada", "tomate", "batata", "refrigerante", "pizza", "lasanha", "sushi", "sorvete"]
    invadidos = [s for s in suspeitos if s in reply_low]
    invasao = [s for s in invadidos if not any(s in item for item in itens_cardapio)]
    if invasao:
        return False, (
            f"A resposta menciona itens que NÃO estão no cardápio: {invasao}. "
            "Use APENAS os itens fornecidos nas observações."
        )
    return True, "ok"
