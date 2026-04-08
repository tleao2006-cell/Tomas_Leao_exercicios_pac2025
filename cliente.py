import socket
import threading
import sys

HOST = "127.0.0.1"
PORTA = 9955

def receber(sock):
    while True:
        try:
            dados = sock.recv(2048)
            if not dados:
                print("\n[CHAT] Ligação encerrada pelo servidor.")
                break

            print(f"\r{dados.decode('utf-8')}")
            print(">> ", end="", flush=True)
        except:
            print("\n[CHAT] Perda de ligação ao servidor.")
            break

    sock.close()
    sys.exit(0)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORTA))
    except ConnectionRefusedError:
        print(f"[ERRO] Não foi possível ligar a {HOST}:{PORTA}. O servidor está a correr?")
        sys.exit(1)

    print("=========================================")
    print("   Sistema de Chat com Deteção GDPR")
    print("=========================================")

    
    try:
        if sock.recv(1024).decode("utf-8") != "NOME_REQ":
            print("[ERRO] Resposta inesperada do servidor.")
            sock.close()
            sys.exit(1)
    except:
        print("[ERRO] Falha na ligação.")
        sock.close()
        sys.exit(1)

    while True:
        nome = input("Escolhe o teu nome: ").strip()
        if nome:
            break
        print("Nome não pode estar vazio.")

    sock.send(nome.encode("utf-8"))

    
    threading.Thread(target=receber, args=(sock,), daemon=True).start()

    print("\nLigado! Comandos: 'sair' | '/online'\n")

    try:
        while True:
            print(">> ", end="", flush=True)
            mensagem = input()

            if not mensagem.strip():
                continue

            sock.send(mensagem.encode("utf-8"))

            if mensagem.strip().lower() == "sair":
                print("[CHAT] A desligar...")
                break
    except KeyboardInterrupt:
        print("\n[CLIENTE] A sair...")
    except:
        print("[CLIENTE] Erro de comunicação.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()