import requests
from bs4 import BeautifulSoup
import urllib.robotparser
from urllib.parse import urlparse, urljoin
import time
import json

# Configuração
USER_AGENT = "MeuCrawlerEducacional/1.0 (estudo)"
DEFAULT_DELAY = 1.0  

def obter_robots_parser(url_inicial):
    
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(url_inicial, "/robots.txt"))
    try:
        rp.read()
    except:
        return None
    return rp

def pode_visitar(rp, url, user_agent):
    
    if rp is None:
        return True
    return rp.can_fetch(user_agent, url)

def obter_delay(rp, user_agent):
    
    if rp is None:
        return DEFAULT_DELAY
    delay = rp.crawl_delay(user_agent)
    return delay if delay is not None else DEFAULT_DELAY

def crawler(url_inicial, max_paginas=20, mesmo_dominio=True):

    headers = {"User-Agent": USER_AGENT}
    dominio_original = urlparse(url_inicial).netloc

    # Prepara robots
    rp = obter_robots_parser(url_inicial)
    delay = obter_delay(rp, USER_AGENT)

    print(f"Iniciando em: {url_inicial}")
    print(f"Delay: {delay:.1f}s | Respeita robots.txt: {rp is not None}")
    print(f"Ficar apenas no domínio {dominio_original}: {mesmo_dominio}\n")

    visitadas = set()
    fila = [url_inicial]
    resultados = []   # lista final no formato pedido

    while fila and len(visitadas) < max_paginas:
        url_atual = fila.pop(0)   # FIFO simples

        if url_atual in visitadas:
            continue

        # (Opcional) não sair do domínio inicial
        if mesmo_dominio and urlparse(url_atual).netloc != dominio_original:
            continue

        if not pode_visitar(rp, url_atual, USER_AGENT):
            print(f"[Bloqueado robots.txt] {url_atual}")
            continue

        print(f"[{len(visitadas)+1}/{max_paginas}]: {url_atual}")

        try:
            resp = requests.get(url_atual, headers=headers, timeout=8)
            resp.raise_for_status()
        except Exception as e:
            print(f"  Erro: {e}")
            continue

        
        soup = BeautifulSoup(resp.text, "html.parser")
        titulo = soup.title.string.strip() if soup.title and soup.title.string else "Sem título"

        
        links = []
        for tag_a in soup.find_all("a", href=True):
            url_completa = urljoin(url_atual, tag_a["href"])
            if url_completa.startswith(("http://", "https://")):
                links.append(url_completa)
                
                if url_completa not in visitadas and url_completa not in fila:
                    if not mesmo_dominio or urlparse(url_completa).netloc == dominio_original:
                        fila.append(url_completa)

        
        resultados.append({
            "url": url_atual,
            "titulo": titulo,
            "links": links
        })

        visitadas.add(url_atual)
        time.sleep(delay)   

    
    with open("crawler_resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\nConcluído! {len(resultados)} páginas guardadas em crawler_resultados.json")
    return resultados

# Exemplo de execução
if __name__ == "__main__":
    url = input("URL inicial (ex: https://quotes.toscrape.com): ").strip()
    if not url.startswith("http"):
        url = "https://" + url
    max_pag = input("Máximo de páginas (ex: 20): ").strip()
    max_pag = int(max_pag) if max_pag.isdigit() else 20
    crawler(url, max_pag, mesmo_dominio=True)