import requests
from bs4 import BeautifulSoup
import urllib.robotparser
from urllib.parse import urlparse, urljoin
import time
import json
import os
from collections import deque
import random

def get_robots_parser(base_url, user_agent):
    """Lê robots.txt apenas uma vez por domínio"""
    rp = urllib.robotparser.RobotFileParser()
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp
    except:
        return None

def can_fetch(rp, url, user_agent):
    if rp is None:
        return True
    try:
        return rp.can_fetch(user_agent, url)
    except:
        return True

def get_crawl_delay(rp, user_agent, default=1.0):
    if rp is None:
        return default
    try:
        delay = rp.crawl_delay(user_agent)
        return delay if delay else default
    except:
        return default

def crawler(url_inicial, max_paginas=20):
    user_agent = "MeuCrawlerEducacional/1.0 (para fins académicos)"
    headers = {"User-Agent": user_agent}

    dominio_inicial = urlparse(url_inicial).netloc
    paginas_visitadas = set()
    fila_urls = deque([url_inicial])          

    resultados = []
    erros = []
    grafico = {}

    # Ler robots.txt uma única vez
    rp = get_robots_parser(url_inicial, user_agent)
    crawl_delay = get_crawl_delay(rp, user_agent, default=1.5)

    print(f"Iniciando crawler em: {url_inicial}")
    print(f"Respeitando delay de ≈ {crawl_delay:.1f}s")

    try:
        while fila_urls and len(paginas_visitadas) < max_paginas:
            url_atual = fila_urls.popleft()

            if url_atual in paginas_visitadas:
                continue

            # Filtro importante: manter no mesmo domínio 
            if urlparse(url_atual).netloc != dominio_inicial:
                continue

            paginas_visitadas.add(url_atual)

            print(f"[{len(paginas_visitadas)}/{max_paginas}] → {url_atual}")

            if not can_fetch(rp, url_atual, user_agent):
                print(f"  Bloqueado pelo robots.txt")
                continue

            try:
                response = requests.get(url_atual, headers=headers, timeout=8)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                titulo = soup.title.string.strip() if soup.title and soup.title.string else "Sem título"

                links = []
                for a in soup.find_all('a', href=True):
                    full_url = urljoin(url_atual, a['href'])
                    if full_url.startswith(('http://', 'https://')):
                        links.append(full_url)
                        if (full_url not in paginas_visitadas and 
                            full_url not in fila_urls and
                            urlparse(full_url).netloc == dominio_inicial):
                            fila_urls.append(full_url)

                # Guardar no gráfico
                grafico[url_atual] = links[:50]   # limitar para não ficar gigante

                resultados.append({
                    "url": url_atual,
                    "titulo": titulo,
                    "total_links": len(links),
                    "links": links[:30]   # guardar só os primeiros 30 para o JSON não explodir
                })

            except requests.exceptions.RequestException as e:
                erros.append({"url": url_atual, "erro": str(e)})

            # Delay respeitando robots.txt + aleatoriedade
            time.sleep(crawl_delay + random.uniform(0.5, 1.5))

    except KeyboardInterrupt:
        print("\n\nInterrompido pelo utilizador. Guardando dados...")

    # ==================== Guardar resultados ====================
    pasta = os.path.join(os.path.dirname(__file__), dominio_inicial.replace(".", "_"))
    os.makedirs(pasta, exist_ok=True)

    with open(os.path.join(pasta, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    with open(os.path.join(pasta, "erros.json"), "w", encoding="utf-8") as f:
        json.dump(erros, f, ensure_ascii=False, indent=2)

    with open(os.path.join(pasta, "grafico_navegacao.json"), "w", encoding="utf-8") as f:
        json.dump(grafico, f, ensure_ascii=False, indent=2)

    print(f"\nCrawler finalizado! {len(resultados)} páginas guardadas em:")
    print(f"   → {pasta}")

if __name__ == "__main__":
    url = input("URL inicial (ex: https://quotes.toscrape.com): ").strip()
    if not url.startswith("http"):
        url = "https://" + url

    max_p = input("Número máximo de páginas (ex: 30): ").strip()
    max_paginas = int(max_p) if max_p.isdigit() else 20

    crawler(url, max_paginas)