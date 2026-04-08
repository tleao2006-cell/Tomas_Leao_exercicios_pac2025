import socket
import threading
import sys

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO
# ─────────────────────────────────────────────
HOST  = "127.0.0.1"
PORTA = 12340

# ─────────────────────────────────────────────
#  RECEBER MENSAGENS (thread separada)
# ─────────────────────────────────────────────
def receber_mensagens(sock: socket.socket):
    """
    Corre numa thread dedicada. Recebe mensagens do servidor
    e imprime-as no terminal. Termina quando a conexão é fechada.
    """
    while True:
        try:
            dados = sock.recv(4096)
            if not dados:
                print("\n[SISTEMA] Conexão encerrada pelo servidor.")
                break

            mensagem = dados.decode("utf-8")

            # Limpar a linha de input atual antes de imprimir
            print(f"\r{mensagem}")
            print("Tu: ", end="", flush=True)

            # Se o servidor enviou um aviso de ban, sair
            if "Foste banido" in mensagem:
                sock.close()
                sys.exit(0)

        except Exception:
            print("\n[CLIENTE] Perda de conexão com o servidor.")
            break

    sock.close()
    sys.exit(0)


# ─────────────────────────────────────────────
#  LIGAR AO SERVIDOR
# ─────────────────────────────────────────────
def iniciar_cliente():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORTA))
    except ConnectionRefusedError:
        print(f"[ERRO] Não foi possível ligar ao servidor em {HOST}:{PORTA}.")
        print("       Verifica se o servidor está em execução.")
        sys.exit(1)

    print("=" * 50)
    print("   CHAT GDPR — Sistema de Chat Seguro")
    print("=" * 50)

    # ── Handshake: enviar nome ─────────────────
    try:
        pedido = sock.recv(1024).decode("utf-8")
        if pedido != "NOME_REQ":
            print("[ERRO] Resposta inesperada do servidor.")
            sock.close()
            sys.exit(1)
    except Exception:
        print("[ERRO] Falha ao comunicar com o servidor.")
        sock.close()
        sys.exit(1)

    while True:
        nome = input("Introduz o teu nome de utilizador: ").strip()
        if nome:
            break
        print("[AVISO] O nome não pode estar vazio.")

    sock.send(nome.encode("utf-8"))

    # ── Iniciar thread de receção ──────────────
    thread_recv = threading.Thread(target=receber_mensagens, args=(sock,), daemon=True)
    thread_recv.start()

    print("\nLigado ao servidor! Escreve /ajuda para ver os comandos disponíveis.")
    print("Para sair, escreve /exit\n")

    # ── Loop de envio ──────────────────────────
    while True:
        try:
            print("Tu: ", end="", flush=True)
            mensagem = input()

            if not mensagem.strip():
                continue

            sock.send(mensagem.encode("utf-8"))

            if mensagem.strip().lower() == "/exit":
                print("[CLIENTE] A desligar...")
                break

        except KeyboardInterrupt:
            print("\n[CLIENTE] Interrompido pelo utilizador.")
            sock.send("/exit".encode("utf-8"))
            break
        except Exception as exc:
            print(f"\n[CLIENTE] Erro ao enviar mensagem: {exc}")
            break

    sock.close()
    sys.exit(0)


if __name__ == "__main__":
    iniciar_cliente()
