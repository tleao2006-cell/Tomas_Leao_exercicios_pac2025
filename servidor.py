import socket
import threading
import re
import os
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

HOST = "127.0.0.1"
PORT = 9955

PASTA_LOGS = "registos"
os.makedirs(PASTA_LOGS, exist_ok=True)

FICHEIRO_GDPR = os.path.join(PASTA_LOGS, "dados_pessoais.txt")
FICHEIRO_ATIVIDADE = os.path.join(PASTA_LOGS, "atividade.txt")

utilizadores = {}  
lock = threading.Lock()

# Expressões Regulares para deteção GDPR
RE_EMAIL    = re.compile(r'\b[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}\b')
RE_TELEFONE = re.compile(r'\b(?:\+351\s?)?(?:9[1236]\d|2\d{2})[\s\-]?\d{3}[\s\-]?\d{3}\b')
RE_IP       = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
RE_NOME     = re.compile(r'(?i)(?:o meu nome é|chamo-me|sou o|sou a)\s+([A-ZÀ-ÖØ-öø-ÿ][a-zÀ-ÖØ-öø-ÿ]+(?:\s+[A-ZÀ-ÖØ-öø-ÿ][a-zÀ-ÖØ-öø-ÿ]+){1,})')
RE_DATA     = re.compile(r'\b(?:0?[1-9]|[12]\d|3[01])[\/\-\.](?:0?[1-9]|1[0-2])[\/\-\.](19|20)\d{2}\b')
RE_CARTAO   = re.compile(r'\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13})\b')
RE_PASSWORD = re.compile(r'(?i)(?:password|senha|palavra[ -]?passe)\s*[:=é]\s*\S+')

def timestamp():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def registar(ficheiro, linha):
    with open(ficheiro, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp()}] {linha}\n")

def enviar(sock, texto):
    try:
        sock.sendall((texto + "\n").encode("utf-8"))
    except:
        pass

def difundir(mensagem, exceto=None):
    with lock:
        for s in list(utilizadores):
            if s is not exceto:
                enviar(s, mensagem)

def desligar(sock):
    with lock:
        nome = utilizadores.pop(sock, None)
    if nome:
        print(Fore.YELLOW + f"[-] {nome} desligou-se.")
        registar(FICHEIRO_ATIVIDADE, f"{nome} saiu do chat.")
        difundir(f"[CHAT] {nome} saiu da sala.")
    try:
        sock.close()
    except:
        pass

def contem_dados_pessoais(texto, nome):
    tipos = []
    if RE_EMAIL.search(texto):    tipos.append("email")
    if RE_TELEFONE.search(texto): tipos.append("telefone")
    if RE_IP.search(texto):       tipos.append("IP")
    if RE_NOME.search(texto):     tipos.append("nome")
    if RE_DATA.search(texto):     tipos.append("data")
    if RE_CARTAO.search(texto):   tipos.append("cartão")
    if RE_PASSWORD.search(texto): tipos.append("password")

    if tipos:
        registar(FICHEIRO_GDPR, f"UTILIZADOR: {nome} | DETETADO: {', '.join(tipos)} | MENSAGEM: {texto}")
        print(Fore.RED + f"[GDPR] Dados pessoais detetados de {nome}: {tipos}")
        return True
    return False

def gerir_cliente(sock, addr):
    try:
        enviar(sock, "NOME_REQ")
        nome = sock.recv(1024).decode("utf-8").strip()
        if not nome:
            return

        with lock:
            if any(n.lower() == nome.lower() for n in utilizadores.values()):
                enviar(sock, "[ERRO] Nome já em uso.")
                return
            utilizadores[sock] = nome

        print(Fore.GREEN + f"[+] {nome} ligou-se de {addr[0]}")
        registar(FICHEIRO_ATIVIDADE, f"{nome} entrou no chat ({addr[0]}).")
        difundir(f"[CHAT] {nome} entrou na sala.", exceto=sock)
        enviar(sock, f"[CHAT] Bem-vindo, {nome}! Comandos: sair | /online | /pm nome mensagem")

        while True:
            dados = sock.recv(2048)
            if not dados:
                break

            msg = dados.decode("utf-8").strip()
            if not msg:
                continue

            if msg.lower() == "sair":
                enviar(sock, "[CHAT] Até logo!")
                break

            if msg == "/online":
                with lock:
                    online = ", ".join(utilizadores.values())
                enviar(sock, f"[SISTEMA] Utilizadores online: {online}")
                continue

            # Mensagem Privada
            if msg.startswith("/pm "):
                try:
                    _, target, *texto_list = msg.split()
                    texto = " ".join(texto_list)
                    with lock:
                        target_sock = next((s for s, n in utilizadores.items() if n.lower() == target.lower()), None)
                    if target_sock:
                        enviar(target_sock, f"[PM de {nome}] {texto}")
                        enviar(sock, f"[PM para {target}] {texto}")
                    else:
                        enviar(sock, f"[ERRO] Utilizador {target} não encontrado.")
                except:
                    enviar(sock, "[ERRO] Uso: /pm nome mensagem")
                continue

            # Verificação GDPR
            if contem_dados_pessoais(msg, nome):
                enviar(sock, "[GDPR] AVISO: Mensagem bloqueada por conter dados pessoais.")
            else:
                print(f"  {nome}: {msg}")
                difundir(f"{nome}: {msg}", exceto=sock)

    except:
        pass
    finally:
        desligar(sock)

def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(20)

    print(Fore.CYAN + f"[*] Servidor GDPR Chat iniciado em {HOST}:{PORT}")
    print(Fore.CYAN + f"[*] Logs guardados em: {PASTA_LOGS}/")

    try:
        while True:
            sock, addr = servidor.accept()
            threading.Thread(target=gerir_cliente, args=(sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[*] Servidor encerrado.")
    finally:
        servidor.close()

if __name__ == "__main__":
    main()