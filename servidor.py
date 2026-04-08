
# Importação das bibliotecas
import socket      # Permite a comunicação TCP/IP
import threading   # Permite criar  vários clientes ao mesmo tempo
import re          # Expressões regulares 
import os          # Para criar pastas e verificar ficheiros
from datetime import datetime  # Para registar a data/hora nos logs

HOST = "127.0.0.1"  # Endereço local (localhost) 
PORT = 9955          # Porta onde o servidor 


PASTA_LOGS = "registos"                           # Nome da pasta para guardar os logs
os.makedirs(PASTA_LOGS, exist_ok=True)            # Cria a pasta se não existir

FICHEIRO_GDPR = os.path.join(PASTA_LOGS, "dados_pessoais.txt")     # Log de dados pessoais detetados
FICHEIRO_ATIVIDADE = os.path.join(PASTA_LOGS, "atividade.txt")      # Log de entradas/saídas

utilizadores = {}      # Dicionário: chave = socket do cliente
lock = threading.Lock()  # Lock para evitar que duas threads acedam ao dicionário ao mesmo tempo

RE_EMAIL = re.compile(r'\b[\w.%+-]+@[\w.-]+\.[a-zA-Z]{2,}\b')
RE_TELEFONE = re.compile(r'\b(?:\+351\s?)?(?:9[1236]\d|2\d{2})[\s\-]?\d{3}[\s\-]?\d{3}\b')
RE_IP = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
RE_NOME = re.compile(r'(?i)(?:o meu nome é|chamo-me|sou o|sou a)\s+([A-ZÀ-ÖØ-öø-ÿ][a-zÀ-ÖØ-öø-ÿ]+(?:\s+[A-ZÀ-ÖØ-öø-ÿ][a-zÀ-ÖØ-öø-ÿ]+){1,})')
RE_DATA = re.compile(r'\b(?:0?[1-9]|[12]\d|3[01])[\/\-\.](?:0?[1-9]|1[0-2])[\/\-\.](19|20)\d{2}\b')
RE_CARTAO = re.compile(r'\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13})\b')
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
        pass  # Se falhar (cliente desligado), ignoramos

def difundir(mensagem, exceto=None):
    with lock:  # Usamos lock para garantir que ninguém altera a lista enquanto enviamos
        for s in list(utilizadores):  # list() cria uma cópia para evitar erros se a lista mudar
            if s is not exceto:
                enviar(s, mensagem)

def desligar(sock):
    with lock:
        nome = utilizadores.pop(sock, None)  # Remove o socket e obtém o nome (se existir)
    
    if nome:
        print(f"[-] {nome} desligou-se.")
        registar(FICHEIRO_ATIVIDADE, f"{nome} saiu do chat.")
        difundir(f"[CHAT] {nome} saiu da sala.")
    
    try:
        sock.close() 
    except:
        pass

def contem_dados_pessoais(texto, nome):
    tipos = []  # Lista para guardar os tipos de dados encontrados
    if RE_EMAIL.search(texto):    tipos.append("email")
    if RE_TELEFONE.search(texto): tipos.append("telefone")
    if RE_IP.search(texto):       tipos.append("IP")
    if RE_NOME.search(texto):     tipos.append("nome")
    if RE_DATA.search(texto):     tipos.append("data")
    if RE_CARTAO.search(texto):   tipos.append("cartão")
    if RE_PASSWORD.search(texto): tipos.append("password")

    if tipos:
        # Regista no ficheiro GDPR
        registar(FICHEIRO_GDPR, f"UTILIZADOR: {nome} | DETETADO: {', '.join(tipos)} | MENSAGEM: {texto}")
        print(f"[GDPR] Dados pessoais detetados de {nome}: {tipos}")
        return True  # Mensagem contém dados pessoais
    
    return False  # Mensagem segura (sem dados pessoais)

def gerir_cliente(sock, addr):
    try:
        enviar(sock, "NOME_REQ")  # Envia comando para o cliente pedir o nome
        nome = sock.recv(1024).decode("utf-8").strip()  # Recebe o nome do cliente
        if not nome:  # Se não receber nome, termina
            return

        # Verificar se o nome já está em uso
        with lock:
            if any(n.lower() == nome.lower() for n in utilizadores.values()):# Verifica se existe algum utilizador com o mesmo nome (case-insensitive)
                enviar(sock, "[ERRO] Nome já em uso.")
                return
            # Adiciona o novo utilizador ao dicionário
            utilizadores[sock] = nome

        # PASSO 3: Anunciar a entrada do novo utilizador
        print(f"[+] {nome} ligou-se de {addr[0]}")
        registar(FICHEIRO_ATIVIDADE, f"{nome} entrou no chat ({addr[0]}).")
        difundir(f"[CHAT] {nome} entrou na sala.", exceto=sock)
        
        enviar(sock, f"[CHAT] Bem-vindo, {nome}! Comandos: 'sair' | '/online' | '/pm nome mensagem'")

        while True:
            dados = sock.recv(2048)  # Recebe dados do cliente (máx 2048 bytes)
            if not dados:  # Cliente desligou
                break

            msg = dados.decode("utf-8").strip()  # Converte bytes para string
            if not msg:  # Mensagem vazia, ignorar
                continue

            if msg.lower() == "sair":
                enviar(sock, "[CHAT] Até logo!")
                break  

            # COMANDO: /online - lista utilizadores online
            if msg == "/online":
                with lock:
                    online = ", ".join(utilizadores.values())  # Junta todos os nomes com vírgulas
                enviar(sock, f"[SISTEMA] Utilizadores online: {online}")
                continue  # Volta ao início do loop

            if msg.startswith("/pm "):# COMANDO: /pm nome mensagem - mensagem privada
                try:
                    # Divide a mensagem em 3 partes: comando, destino, texto
                    parts = msg.split(maxsplit=2)
                    if len(parts) < 3:
                        raise ValueError("Mensagem incompleta")
                    _, target, texto = parts  # _ ignora o "/pm"
                    
                    # Procura o socket do destinatário
                    with lock:
                        target_sock = next((s for s, n in utilizadores.items() if n.lower() == target.lower()), None)
                    
                    # Se encontrou e não é o próprio
                    if target_sock and target_sock != sock:
                        enviar(target_sock, f"[PM de {nome}] {texto}")  # Envia ao destino
                        enviar(sock, f"[PM para {target}] {texto}")      # Confirma ao remetente
                    else:
                        enviar(sock, f"[ERRO] Utilizador '{target}' não encontrado.")
                except:
                    enviar(sock, "[ERRO] Uso: /pm nome mensagem")
                continue
            # Verifica se a mensagem contém dados pessoais
            if contem_dados_pessoais(msg, nome):
                # Mensagem BLOQUEADA - avisa apenas o remetente
                enviar(sock, "[GDPR] AVISO: Mensagem bloqueada por conter dados pessoais (GDPR).")
            else:
                print(f"  {nome}: {msg}") # Mensagem APROVADA - mostra no servidor e difunde para todos
                difundir(f"{nome}: {msg}", exceto=sock)  # Envia para todos exceto o remetente

    except:
        pass  # Erro inesperado, termina a thread
    finally:
        desligar(sock)  # Garante que o cliente é removido corretamente
def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET = IPv4, SOCK_STREAM = TCP
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permite reutilizar a porta imediatamente
    servidor.bind((HOST, PORT))# Associa o socket ao endereço e porta
    servidor.listen(20)    # Começa a "ouvir" por ligações (máximo 20 clientes em fila de espera)

    print(f"[*] Servidor GDPR Chat iniciado em {HOST}:{PORT}")
    print(f"[*] Logs guardados em: {PASTA_LOGS}/")

    try:
        while True:
            sock, addr = servidor.accept()  # Bloqueia até alguém ligar
            threading.Thread(target=gerir_cliente, args=(sock, addr), daemon=True).start()# Cria uma nova thread para gerir este cliente
    except KeyboardInterrupt:
        print("\n[*] Servidor encerrado.")
    finally:
        servidor.close()  

if __name__ == "__main__":
    main()