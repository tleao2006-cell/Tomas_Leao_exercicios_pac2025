import requests
from bs4 import BeautifulSoup
import urllib.robotparser
from urllib.parse import urlparse, urljoin
import time
import json
import os
import random

def can_fetch_url(url, user_agent):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = f"{base_url}/robots.txt"
    
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        return True

def crawler(url_inicial, max_paginas):
    user_agent = "MrL30"
    headers = {"User-Agent": user_agent}
    
    paginas_visitadas = set()
    fila_urls = [url_inicial]
    
    resultados_sucesso = []
    resultados_erro = []
    
    grafico_navegacao = {} 
    
    print("Pressiona 'Ctrl + C' para parar e guardar os dados")

    try:
        while fila_urls and len(paginas_visitadas) < max_paginas:
            url_atual = fila_urls.pop(0)
            
            if url_atual in paginas_visitadas:
                continue
                
            paginas_visitadas.add(url_atual)
            
            limite_display = "∞" if max_paginas == float('inf') else max_paginas
            print(f"[{len(paginas_visitadas)}/{limite_display}] A visitar: {url_atual}")
            
            if not can_fetch_url(url_atual, user_agent):
                print(f"Bloqueado pelo robots.txt")
                continue

            try:
                response = requests.get(url_atual, headers=headers, timeout=5)
                
                if response.status_code >= 300:
                    resultados_erro.append({
                        "url": url_atual,
                        "status_code": response.status_code,
                        "razao": response.reason
                    })
                    continue

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    titulo = soup.title.string.strip() if soup.title else "Sem título"
                    
                    links = []
                    for a_tag in soup.find_all('a', href=True):
                        full_url = urljoin(url_atual, a_tag['href'])
                        
                        if full_url.startswith('http'):
                            links.append(full_url)
                            if full_url not in paginas_visitadas and full_url not in fila_urls:
                                fila_urls.append(full_url)
                    
                    grafico_navegacao[url_atual] = list(set(links)) 

                    resultados_sucesso.append({
                        "url": url_atual,
                        "titulo": titulo,
                        "total_links_encontrados": len(links),
                        "links": links
                    })

            except requests.exceptions.RequestException as e:
                resultados_erro.append({
                    "url": url_atual,
                    "status_code": "Erro de Conexão",
                    "razao": str(e)
                })

            delay = random.uniform(1.0, 2.5)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\nExecução interrompida. A guardar dados em segurança...")

    dominio = urlparse(url_inicial).netloc
    if not dominio:
        dominio = url_inicial.replace("https://", "").replace("http://", "").split("/")[0]

    pasta_raiz = os.path.dirname(os.path.abspath(__file__))
    pasta_destino = os.path.join(pasta_raiz, dominio)

    os.makedirs(pasta_destino, exist_ok=True)

    with open(os.path.join(pasta_destino, 'crawler_sucesso.json'), 'w', encoding='utf-8') as f:
        json.dump(resultados_sucesso, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(pasta_destino, 'crawler_erros.json'), 'w', encoding='utf-8') as f:
        json.dump(resultados_erro, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(pasta_destino, 'crawler_grafico.json'), 'w', encoding='utf-8') as f:
        json.dump(grafico_navegacao, f, ensure_ascii=False, indent=2)

    print(f"Finalizado! Ficheiros guardados na pasta: {pasta_destino}")

if __name__ == "__main__":
    print("=== Crawler Bot ===")

    url_alvo = input("Insere o URL inicial (ex: https://example.com): ").strip()
    
    print("\nOpções de limite:")
    print("- Escreve um número para definir o máximo de páginas (ex: 20)")
    print("- Escreve 'tudo' para mapear sem limite numérico")
    limite_str = input("Escolha: ").strip().lower()
    
    if limite_str == 'tudo':
        max_paginas = float('inf') 
        print("\n[!] MODO 'TUDO' ATIVADO.")
        print("[!] O programa correrá sem limite. Pressiona Ctrl+C para parar e guardar.")
    elif limite_str.isdigit():
        max_paginas = int(limite_str)
    else:
        print("\nValor inválido. A assumir 20 páginas por defeito.")
        max_paginas = 20

    print(f"\nA iniciar o crawler em {url_alvo}...")
    crawler(url_alvo, max_paginas)