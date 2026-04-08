import socket
import threading
import re
import os
from datetime import datetime
 
# ── Configuração ────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORTA = 9955
 
PASTA_LOGS = "registos"
os.makedirs(PASTA_LOGS, exist_ok=True)
 
FICHEIRO_GDPR      = os.path.join(PASTA_LOGS, "dados_pessoais.txt")
FICHEIRO_ES        = os.path.join(PASTA_LOGS, "engenharia_social.txt")
FICHEIRO_ATIVIDADE = os.path.join(PASTA_LOGS, "atividade.txt")
 
# ── Estado global ────────────────────────────────────────────────────
utilizadores = {}           # socket -> nome
pontuacao_risco = {}        # nome -> int
lock = threading.Lock()
 
LIMITE_EXPULSAO = 100
 
# ── Padrões de deteção GDPR ─────────────────────────────────────────
RE_EMAIL     = re.compile(r'\b[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}\b')
RE_TELEFONE  = re.compile(r'\b(?:\+351\s?)?(?:9[1236]\d|2\d{2})[\s\-]?\d{3}[\s\-]?\d{3}\b')
RE_IP        = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
RE_NOME      = re.compile(r'(?i)(?:o meu nome é|chamo-me|sou o|sou a)\s+([A-ZÀÁÂÃ][a-zàáâã]+(?:\s+[A-ZÀÁÂÃ][a-zàáâã]+)+)')
RE_DATA      = re.compile(r'\b(?:0?[1-9]|[12]\d|3[01])[\/\-.](?:0?[1-9]|1[0-2])[\/\-.](19|20)\d{2}\b')
RE_CARTAO    = re.compile(r'\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13})\b')
RE_PASSWORD  = re.compile(r'(?i)(?:password|senha|palavra.passe)\s*[=:é]\s*\S+')
 
# Gatilhos de engenharia social
GATILHOS_ES = [
    "urgente", "clica aqui", "ganhaste", "promoção",
    "confirma os teus dados", "acesso imediato", "oferta exclusiva"
]
 
# ── Funções auxiliares ───────────────────────────────────────────────
def timestamp():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
 
def registar(ficheiro, linha):
    with open(ficheiro, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp()}] {linha}\n")
 
def enviar_msg(sock, texto):
    try:
        sock.sendall(texto.encode("utf-8"))
    except:
        pass
 
def difundir(mensagem, exceto=None):
    with lock:
        for sock in list(utilizadores):
            if sock is exceto:
                continue
            enviar_msg(sock, mensagem)
 
def desligar_utilizador(sock):
    with lock:
        nome = utilizadores.pop(sock, None)
    if nome:
        print(f"[-] {nome} desligou-se.")
        registar(FICHEIRO_ATIVIDADE, f"{nome} saiu do chat.")
        difundir(f"[CHAT] {nome} saiu da sala.")
    try:
        sock.close()
    except:
        pass
 
# ── Deteção de dados pessoais e engenharia social ────────────────────
def verificar_mensagem(texto, nome_utilizador):
    dados_encontrados = []
 
    if RE_EMAIL.search(texto):
        dados_encontrados.append("email")
    if RE_TELEFONE.search(texto):
        dados_encontrados.append("telefone")
    if RE_IP.search(texto):
        dados_encontrados.append("endereco IP")
    if RE_NOME.search(texto):
        dados_encontrados.append("nome pessoal")
    if RE_DATA.search(texto):
        dados_encontrados.append("data de nascimento")
    if RE_CARTAO.search(texto):
        dados_encontrados.append("cartao de credito")
    if RE_PASSWORD.search(texto):
        dados_encontrados.append("password")
 
    contem_dados_pessoais = len(dados_encontrados) > 0
 
    # Guardar no log GDPR
    if contem_dados_pessoais:
        registar(FICHEIRO_GDPR,
            f"UTILIZADOR: {nome_utilizador} | DETETADO: {', '.join(dados_encontrados)} | MENSAGEM: {texto}")
        print(f"[GDPR] Dados pessoais detetados de {nome_utilizador}: {dados_encontrados}")
 
    # Verificar engenharia social
    gatilhos_presentes = [g for g in GATILHOS_ES if g.lower() in texto.lower()]
    if gatilhos_presentes:
        pontos = len(gatilhos_presentes) * 25
        pontuacao_risco[nome_utilizador] = pontuacao_risco.get(nome_utilizador, 0) + pontos
        registar(FICHEIRO_ES,
            f"UTILIZADOR: {nome_utilizador} | GATILHOS: {gatilhos_presentes} | PONTOS: +{pontos} | TOTAL: {pontuacao_risco[nome_utilizador]} | MENSAGEM: {texto}")
        print(f"[ES] Engenharia social de {nome_utilizador} — pontuacao: {pontuacao_risco[nome_utilizador]}")
 
    return contem_dados_pessoais
 
# ── Thread por cliente ───────────────────────────────────────────────
def gerir_cliente(sock, endereco):
    # Pedir username
    try:
        enviar_msg(sock, "NOME_REQ")
        nome = sock.recv(1024).decode("utf-8").strip()
        if not nome:
            sock.close()
            return
    except:
        sock.close()
        return
 
    with lock:
        utilizadores[sock] = nome
 
    print(f"[+] {nome} ligou-se a partir de {endereco[0]}:{endereco[1]}")
    registar(FICHEIRO_ATIVIDADE, f"{nome} entrou no chat ({endereco[0]}).")
    difundir(f"[CHAT] {nome} entrou na sala.", exceto=sock)
    enviar_msg(sock, f"[CHAT] Ligado com sucesso. Bem-vindo, {nome}!")
 
    # Loop de receção de mensagens
    while True:
        try:
            dados = sock.recv(2048)
            if not dados:
                break
 
            mensagem = dados.decode("utf-8").strip()
            if not mensagem:
                continue
 
            # Comando para sair
            if mensagem.lower() == "sair":
                enviar_msg(sock, "[CHAT] Ate logo!")
                break
 
            # Comando de estado
            if mensagem.lower() == "/estado":
                pontos = pontuacao_risco.get(nome, 0)
                enviar_msg(sock, f"[SISTEMA] A tua pontuacao de risco e: {pontos}")
                continue
 
            # Verificar dados pessoais e ES
            bloqueada = verificar_mensagem(mensagem, nome)
 
            # Expulsar se ultrapassou o limite
            if pontuacao_risco.get(nome, 0) >= LIMITE_EXPULSAO:
                enviar_msg(sock, "[SISTEMA] Fuste expulso do servidor devido a comportamento suspeito repetido.")
                difundir(f"[SISTEMA] {nome} foi expulso do servidor.", exceto=sock)
                print(f"[BAN] {nome} foi expulso (pontuacao: {pontuacao_risco[nome]}).")
                break
 
            if bloqueada:
                enviar_msg(sock, "[GDPR] AVISO: A tua mensagem foi bloqueada por conter dados pessoais.")
            else:
                print(f"  {nome}: {mensagem}")
                difundir(f"{nome}: {mensagem}", exceto=sock)
 
        except:
            break
 
    desligar_utilizador(sock)
 
# ── Arranque do servidor ─────────────────────────────────────────────
def arrancar():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen(10)
 
    print(f"[*] Servidor iniciado em {HOST}:{PORTA}")
    print(f"[*] Logs guardados em: {PASTA_LOGS}/")
 
    try:
        while True:
            sock, endereco = servidor.accept()
            t = threading.Thread(target=gerir_cliente, args=(sock, endereco), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Servidor encerrado.")
    finally:
        servidor.close()
 
if __name__ == "__main__":
    arrancar()