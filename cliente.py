import socket
import threading
import sys
from colorama import init, Fore, Style

init(autoreset=True)

HOST = "127.0.0.1"
PORT = 9955

def receber(sock):
    while True:
        try:
            dados = sock.recv(2048)
            if not dados:
                print(Fore.RED + "\n[CHAT] Ligação encerrada pelo servidor.")
                break
            print(f"\r{dados.decode('utf-8')}")
            print(">> ", end="", flush=True)
        except:
            print(Fore.RED + "\n[CHAT] Perda de ligação ao servidor.")
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
    except:
        print(Fore.RED + f"[ERRO] Não foi possível ligar a {HOST}:{PORT}")
        sys.exit(1)

    print(Fore.CYAN + "="*50)
    print(Fore.CYAN + "   Sistema de Chat com Deteção GDPR")
    print(Fore.CYAN + "="*50)

    try:
        if sock.recv(1024).decode("utf-8") != "NOME_REQ":
            print(Fore.RED + "[ERRO] Resposta inesperada do servidor.")
            sock.close()
            sys.exit(1)
    except:
        print(Fore.RED + "[ERRO] Falha na ligação.")
        sock.close()
        sys.exit(1)

    while True:
        nome = input("Escolhe o teu nome: ").strip()
        if nome:
            break
        print(Fore.YELLOW + "Nome não pode estar vazio.")

    sock.send(nome.encode("utf-8"))

    threading.Thread(target=receber, args=(sock,), daemon=True).start()

    print(Fore.GREEN + "\nLigado! Comandos: sair | /online | /pm nome mensagem\n")

    try:
        while True:
            print(">> ", end="", flush=True)
            mensagem = input()

            if not mensagem.strip():
                continue

            sock.send(mensagem.encode("utf-8"))

            if mensagem.strip().lower() == "sair":
                print(Fore.YELLOW + "[CHAT] A desligar...")
                break
    except:
        pass
    finally:
        sock.close()

if __name__ == "__main__":
    main()