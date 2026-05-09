import os
import shutil

from agenticblocks import as_tool

_BASE_DIR = os.path.realpath(os.getcwd())


def is_safe_path(path: str) -> bool:
    resolved = os.path.realpath(os.path.abspath(path))
    return resolved == _BASE_DIR or resolved.startswith(_BASE_DIR + os.sep)


@as_tool(name="mkdir", description="Cria um diretório no caminho especificado.")
def mkdir(dir: str) -> bool:
    if not is_safe_path(dir):
        return False
    try:
        os.makedirs(dir, exist_ok=True)
        return True
    except Exception:
        return False


@as_tool(name="create_txt_file", description="Cria um arquivo vazio com a extensão especificada.")
def create_txt_file(path: str, ext: str) -> str:
    full_path = path if path.endswith(f".{ext}") else f"{path}.{ext}"
    if not is_safe_path(full_path):
        return "Operação negada: caminho fora do diretório de trabalho."
    try:
        os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
        open(full_path, "w", encoding="utf-8").close()
        return f"Arquivo criado: {full_path}"
    except Exception as e:
        return f"Erro ao criar arquivo: {e}"


@as_tool(name="append_content", description="Adiciona conteúdo ao final de um arquivo.")
def append_content(file: str, content: str) -> str:
    if not is_safe_path(file):
        return "Operação negada: caminho fora do diretório de trabalho."
    try:
        with open(file, "a", encoding="utf-8") as f:
            f.write(content)
        return f"Conteúdo adicionado em: {file}"
    except Exception as e:
        return f"Erro ao escrever no arquivo: {e}"


@as_tool(name="remover_arquivo", description="Remove um arquivo.")
def remover_arquivo(file: str) -> str:
    if not is_safe_path(file):
        return "Operação negada: caminho fora do diretório de trabalho."
    try:
        os.remove(file)
        return f"Arquivo removido: {file}"
    except Exception as e:
        return f"Erro ao remover arquivo: {e}"


@as_tool(name="remove_dir", description="Remove um diretório e todo o seu conteúdo.")
def remove_dir(path: str) -> str:
    if not is_safe_path(path):
        return "Operação negada: caminho fora do diretório de trabalho."
    try:
        shutil.rmtree(path)
        return f"Diretório removido: {path}"
    except Exception as e:
        return f"Erro ao remover diretório: {e}"


def validate_reply(reply: str, observations: list) -> tuple[bool, str]:  # noqa: ARG001
    if not reply or not reply.strip():
        return False, "Resposta vazia."
    return True, "ok"


def build_chat_prompt(orig, iteration, producer, feedback):
    return feedback or ""
