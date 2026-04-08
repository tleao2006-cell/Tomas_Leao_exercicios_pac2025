
# Importação das bibliotecas necessárias
import socket      # Para comunicar com o servidor
import threading   # Para receber mensagens enquanto o utilizador escreve
import sys         # Para sair do programa


HOST = "127.0.0.1"  # Endereço do servidor (localhost)
PORTA = 9955        # Porta do servidor 

def receber(sock):

    while True:
        try:
            # Tenta receber dados do servidor (máx 2048 bytes)
            dados = sock.recv(2048)
            
            # Se não receber dados, o servidor fechou a ligação
            if not dados:
                print("\n[CHAT] Ligação encerrada pelo servidor.")
                break

            # Converte bytes para string e imprime
            print(f"\r{dados.decode('utf-8')}")
            
            print(">> ", end="", flush=True)  # flush=True força a impressão imediata
        except:
            print("\n[CHAT] Perda de ligação ao servidor.")
            break

    # Quando sair do loop, fecha o socket e termina o programa
    sock.close()
    sys.exit(0)

def main():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria socket TCP/IP

    try:
        # Tenta ligar ao servidor
        sock.connect((HOST, PORTA))
    except ConnectionRefusedError:
        # Se o servidor não estiver a correr
        print(f"[ERRO] Não foi possível ligar a {HOST}:{PORTA}. O servidor está a correr?")
        sys.exit(1)

    
    print("=========================================")
    print("   Sistema de Chat com Deteção GDPR")
    print("=========================================")

    
    try:
        # Aguarda a mensagem "NOME_REQ" do servidor
        resposta = sock.recv(1024).decode("utf-8").strip()  # strip() remove \n e espaços
        
        # Verifica se a resposta é a esperada
        if resposta != "NOME_REQ":
            print(f"[ERRO] Resposta inesperada do servidor: {resposta}")
            sock.close()
            sys.exit(1)
    except Exception as e:
        print(f"[ERRO] Falha na ligação: {e}")
        sock.close()
        sys.exit(1)

    while True:
        nome = input("Escolhe o teu nome: ").strip()  # strip() remove espaços no início/fim
        if nome:
            break  # Nome válido
        print("Nome não pode estar vazio.")

    # Envia o nome escolhido para o servidor (codificado em bytes)
    sock.send(nome.encode("utf-8"))

    threading.Thread(target=receber, args=(sock,), daemon=True).start()

    print("\nLigado! Comandos: 'sair' | '/online' | '/pm nome mensagem'\n")

    try:
        while True:
            # Pede ao utilizador para escrever uma mensagem
            mensagem = input(">> ")
            
            # Ignora mensagens vazias
            if not mensagem.strip():
                continue

            # Envia a mensagem para o servidor
            sock.send(mensagem.encode("utf-8"))

            # Se o utilizador escreveu "sair", termina o loop
            if mensagem.strip().lower() == "sair":
                print("[CHAT] A desligar...")
                break
                
    except KeyboardInterrupt:
        print("\n[CLIENTE] A sair...")
    except Exception as e:
        # Outro erro de comunicação
        print(f"[CLIENTE] Erro de comunicação: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()