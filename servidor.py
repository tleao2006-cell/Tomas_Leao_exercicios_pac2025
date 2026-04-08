import socket
import threading
import re
import logging
from datetime import datetime
import os

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DE DIRETORIAS E LOGS
# ─────────────────────────────────────────────
DIRETORIO_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_LOGS = os.path.join(DIRETORIO_BASE, "logs")
os.makedirs(PASTA_LOGS, exist_ok=True)

CAMINHO_LOG_GDPR      = os.path.join(PASTA_LOGS, "logs_gdpr.txt")
CAMINHO_LOG_AUDITORIA = os.path.join(PASTA_LOGS, "auditoria_scores.txt")
CAMINHO_LOG_SERVIDOR  = os.path.join(PASTA_LOGS, "servidor.log")

# Logger principal do servidor (consola + ficheiro)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(CAMINHO_LOG_SERVIDOR, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("servidor")

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DO SERVIDOR
# ─────────────────────────────────────────────
HOST  = "127.0.0.1"
PORTA = 12340

# clientes: {socket: {"nome": str, "ip": str, "identidade": str}}
clientes: dict = {}
lock_clientes = threading.Lock()

# score de risco por identidade
reputacao: dict = {}
LIMITE_BAN = 100

# ─────────────────────────────────────────────
#  PADRÕES GDPR  (regex)
# ─────────────────────────────────────────────
PADRAO_EMAIL    = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PADRAO_TELEFONE = re.compile(r'\b(?:\+351\s?)?(?:9[1236]\d|2\d{2})\s?\d{3}\s?\d{3}\b')
PADRAO_IP       = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
PADRAO_NOME     = re.compile(r'(?i)(?:meu nome(?: real)? é|chamo[- ]me)\s+([A-ZÀÁÂÃÉÊÍÓÔÕÚ][a-zàáâãéêíóôõú]+(?:\s+[A-ZÀÁÂÃÉÊÍÓÔÕÚ][a-zàáâãéêíóôõú]+)+)')
PADRAO_DATA_NASC = re.compile(r'\b(?:0?[1-9]|[12]\d|3[01])[\/\-](?:0?[1-9]|1[0-2])[\/\-](?:19|20)\d{2}\b')
PADRAO_CARTAO   = re.compile(r'\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}|3(?:0[0-5]|[68]\d)\d{11}|6(?:011|5\d{2})\d{12})\b')
PADRAO_SENHA    = re.compile(r'(?i)(?:minha?\s+(?:senha|password|palavra[- ]passe)\s+(?:é|:))\s*(\S+)')

# Padrões de engenharia social (aumentam score mas não bloqueiam msg)
GATILHOS_ES = [
    r'\burgente\b', r'\bimediato\b', r'\bclica\s+aqui\b',
    r'\bganhaste\b', r'\bpromo[çc][aã]o\b', r'\boferta\b',
    r'\bverifica\s+a\s+tua\s+conta\b', r'\bsusp[ei]to\b',
    r'\bconfirm[ae]\s+os\s+teus\s+dados\b'
]

# ─────────────────────────────────────────────
#  UTILIDADES
# ─────────────────────────────────────────────
def agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def enviar(sock: socket.socket, texto: str) -> bool:
    """Envia texto codificado para um socket. Devolve False em caso de erro."""
    try:
        sock.send(texto.encode("utf-8"))
        return True
    except Exception:
        return False


def transmitir(mensagem: str, excluir: socket.socket | None = None):
    """Envia mensagem para todos os clientes (opcionalmente excluindo um)."""
    with lock_clientes:
        mortos = []
        for sock in clientes:
            if sock is excluir:
                continue
            if not enviar(sock, mensagem):
                mortos.append(sock)
        for sock in mortos:
            _remover_sem_lock(sock)


def _remover_sem_lock(sock: socket.socket):
    """Remove cliente do dicionário sem adquirir o lock (já deve estar adquirido)."""
    if sock in clientes:
        info = clientes.pop(sock)
        log.info("Conexão encerrada: %s", info["identidade"])
        try:
            sock.close()
        except Exception:
            pass


def remover_cliente(sock: socket.socket):
    """Remove e fecha a conexão de um cliente, notificando os restantes."""
    with lock_clientes:
        if sock not in clientes:
            return
        info = clientes[sock]
        _remover_sem_lock(sock)

    transmitir(f"[SISTEMA] {info['nome']} saiu do chat.")


# ─────────────────────────────────────────────
#  AUDITORIA GDPR
# ─────────────────────────────────────────────
def auditar_mensagem(mensagem: str, identidade: str) -> bool:
    """
    Verifica a mensagem em busca de dados pessoais (GDPR) e padrões
    de engenharia social. Devolve True se dados pessoais forem detetados
    (mensagem deve ser bloqueada).
    """
    dados_detetados = []
    score_adicionado = 0
    infracoes_es = []

    # ── GDPR ──────────────────────────────────
    emails = PADRAO_EMAIL.findall(mensagem)
    if emails:
        dados_detetados.append(f"Emails: {emails}")

    telefones = PADRAO_TELEFONE.findall(mensagem)
    if telefones:
        dados_detetados.append(f"Telefones: {telefones}")

    ips = PADRAO_IP.findall(mensagem)
    if ips:
        dados_detetados.append(f"IPs: {ips}")

    nomes = PADRAO_NOME.findall(mensagem)
    if nomes:
        dados_detetados.append(f"Nomes: {nomes}")

    datas = PADRAO_DATA_NASC.findall(mensagem)
    if datas:
        dados_detetados.append(f"Datas de nascimento: {datas}")

    cartoes = PADRAO_CARTAO.findall(mensagem)
    if cartoes:
        dados_detetados.append(f"Cartões: {cartoes}")

    senhas = PADRAO_SENHA.findall(mensagem)
    if senhas:
        dados_detetados.append(f"Senhas expostas: {senhas}")

    viola_gdpr = len(dados_detetados) > 0

    # ── Engenharia Social ──────────────────────
    for gatilho in GATILHOS_ES:
        if re.search(gatilho, mensagem, re.IGNORECASE):
            infracoes_es.append(gatilho)
            score_adicionado += 20

    # ── Atualizar reputação ────────────────────
    if identidade not in reputacao:
        reputacao[identidade] = 0
    reputacao[identidade] += score_adicionado

    ts = agora()

    # ── Registar violação GDPR ─────────────────
    if viola_gdpr:
        linha = (
            f"[{ts}] ALVO: {identidade} | "
            f"DADOS: {', '.join(dados_detetados)} | "
            f"MSG: '{mensagem}'\n"
        )
        with open(CAMINHO_LOG_GDPR, "a", encoding="utf-8") as f:
            f.write(linha)
        log.warning("VIOLAÇÃO GDPR de %s → %s", identidade, ', '.join(dados_detetados))

    # ── Registar engenharia social ─────────────
    if score_adicionado > 0:
        linha = (
            f"[{ts}] USER: {identidade} | "
            f"SCORE+: {score_adicionado} | "
            f"TOTAL: {reputacao[identidade]} | "
            f"GATILHOS: {infracoes_es} | "
            f"MSG: '{mensagem}'\n"
        )
        with open(CAMINHO_LOG_AUDITORIA, "a", encoding="utf-8") as f:
            f.write(linha)
        log.info("ES detetada de %s — score atual: %d", identidade, reputacao[identidade])

    return viola_gdpr


# ─────────────────────────────────────────────
#  TRATAMENTO DE CADA CLIENTE
# ─────────────────────────────────────────────
def lidar_cliente(sock: socket.socket, endereco: tuple):
    """Thread dedicada a cada cliente."""
    try:
        # Pedir nome de utilizador
        enviar(sock, "NOME_REQ")
        nome = sock.recv(1024).decode("utf-8").strip()
        if not nome:
            sock.close()
            return

        identidade = f"{nome} ({endereco[0]})"

        with lock_clientes:
            clientes[sock] = {"nome": nome, "ip": endereco[0], "identidade": identidade}

        log.info("Nova conexão: %s", identidade)
        transmitir(f"[SISTEMA] {nome} entrou na sala!", excluir=sock)
        enviar(sock, f"[SISTEMA] Bem-vindo, {nome}! Escreve /ajuda para ver os comandos.")

    except Exception as exc:
        log.error("Erro no handshake com %s: %s", endereco, exc)
        sock.close()
        return

    # ── Loop de mensagens ──────────────────────
    while True:
        try:
            dados = sock.recv(1024)
            if not dados:
                break

            mensagem = dados.decode("utf-8").strip()

            # ── Comandos especiais ─────────────
            if mensagem.lower() == "/exit":
                enviar(sock, "[SISTEMA] Até logo!")
                break

            if mensagem.lower() == "/status":
                score = reputacao.get(identidade, 0)
                enviar(sock, f"[SISTEMA] O teu score de risco atual é: {score}")
                continue

            if mensagem.lower() == "/utilizadores":
                with lock_clientes:
                    nomes = [info["nome"] for info in clientes.values()]
                enviar(sock, f"[SISTEMA] Utilizadores online: {', '.join(nomes)}")
                continue

            if mensagem.lower() == "/ajuda":
                ajuda = (
                    "[SISTEMA] Comandos disponíveis:\n"
                    "  /status       — ver o teu score de risco\n"
                    "  /utilizadores — listar utilizadores online\n"
                    "  /exit         — sair do chat\n"
                    "  /ajuda        — mostrar esta ajuda"
                )
                enviar(sock, ajuda)
                continue

            # ── Auditoria GDPR + ES ────────────
            viola_gdpr = auditar_mensagem(mensagem, identidade)

            # ── Verificar ban ──────────────────
            if reputacao.get(identidade, 0) > LIMITE_BAN:
                enviar(sock, "[SISTEMA] Foste banido por violações de segurança repetidas.")
                with lock_clientes:
                    nome_ban = clientes.get(sock, {}).get("nome", "Utilizador")
                transmitir(f"[SISTEMA] {nome_ban} foi banido do servidor.", excluir=sock)
                log.warning("BAN aplicado a %s (score: %d)", identidade, reputacao[identidade])
                break

            # ── Bloquear msg com dados pessoais ─
            if viola_gdpr:
                enviar(sock, "[SISTEMA] ⚠ ALERTA GDPR: A tua mensagem foi bloqueada por conter dados pessoais sensíveis.")
                continue

            # ── Retransmitir mensagem ──────────
            with lock_clientes:
                nome_atual = clientes.get(sock, {}).get("nome", "?")
            transmitir(f"{nome_atual}: {mensagem}", excluir=sock)
            log.info("[%s] %s", identidade, mensagem)

        except Exception as exc:
            log.error("Erro com cliente %s: %s", identidade, exc)
            break

    remover_cliente(sock)


# ─────────────────────────────────────────────
#  INICIAR SERVIDOR
# ─────────────────────────────────────────────
def iniciar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORTA))
    server_socket.listen()

    log.info("Servidor a escutar em %s:%d", HOST, PORTA)
    log.info("Pasta de logs: %s", PASTA_LOGS)

    try:
        while True:
            sock, endereco = server_socket.accept()
            thread = threading.Thread(target=lidar_cliente, args=(sock, endereco), daemon=True)
            thread.start()
            log.info("Thread criada para %s:%d (ativas: %d)", endereco[0], endereco[1], threading.active_count() - 1)
    except KeyboardInterrupt:
        log.info("Servidor encerrado pelo utilizador.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    iniciar_servidor()
