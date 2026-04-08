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
                print("\n[CHAT] Ligacao encerrada pelo servidor.")
                sock.close()
                sys.exit(0)
 
            mensagem = dados.decode("utf-8")
 
            
            print(f"\r{mensagem}")
            print(">> ", end="", flush=True)
 
            
            if "Fuste expulso" in mensagem:
                sock.close()
                sys.exit(0)
 
        except:
            print("\n[CHAT] Perda de ligacao.")
            sock.close()
            sys.exit(0)
 

def iniciar():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    try:
        sock.connect((HOST, PORTA))
    except ConnectionRefusedError:
        print(f"[ERRO] Nao foi possivel ligar a {HOST}:{PORTA}.")
        print("       Certifica-te que o servidor esta a correr.")
        sys.exit(1)
 
    print("=========================================")
    print("   Sistema de Chat com Deteção GDPR")
    print("=========================================")
 
    
    try:
        resposta = sock.recv(1024).decode("utf-8")
        if resposta != "NOME_REQ":
            print("[ERRO] Resposta inesperada do servidor.")
            sock.close()
            sys.exit(1)
    except:
        print("[ERRO] Falha ao ligar ao servidor.")
        sock.close()
        sys.exit(1)
 
    
    while True:
        nome = input("O teu nome: ").strip()
        if nome:
            break
        print("[AVISO] O nome nao pode estar vazio.")
 
    sock.send(nome.encode("utf-8"))
 
    
    t = threading.Thread(target=receber, args=(sock,), daemon=True)
    t.start()
 
    print("\nLigado! Para sair escreve 'sair'. Para o teu estado de risco escreve '/estado'.\n")
 
   
    while True:
        try:
            print(">> ", end="", flush=True)
            mensagem = input()
 
            if not mensagem.strip():
                continue
 
            sock.send(mensagem.encode("utf-8"))
 
            if mensagem.strip().lower() == "sair":
                break
 
        except KeyboardInterrupt:
            print("\n[CLIENTE] A sair...")
            sock.send("sair".encode("utf-8"))
            break
        except:
            print("[CLIENTE] Erro ao enviar mensagem.")
            break
 
    sock.close()
 
if __name__ == "__main__":
    iniciar()