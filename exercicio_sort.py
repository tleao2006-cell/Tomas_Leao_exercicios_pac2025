# ================================================
# EXERCÍCIOS DE ORDENAÇÃO -
# ================================================

# 1. Ordenar lista de palavras por ordem alfabética (A → Z)
def ordenar_alfabetico(palavras):
    
    n = len(palavras)
    for i in range(n):
        for j in range(0, n - i - 1):
            
            if palavras[j] > palavras[j + 1]:
                palavras[j], palavras[j + 1] = palavras[j + 1], palavras[j]
    return palavras


# 2. Ordenar por ordem inversa (Z → A), ignorando maiúsculas/minúsculas
def ordenar_inverso_ignorando_case(palavras):
    
    n = len(palavras)
    for i in range(n):
        for j in range(0, n - i - 1):
            
            a = palavras[j].lower()
            b = palavras[j + 1].lower()
            if a < b:  
                palavras[j], palavras[j + 1] = palavras[j + 1], palavras[j]
    return palavras


# 3. Ordenar os caracteres de uma palavra por ordem alfabética
def ordenar_caracteres(palavra):
    
    lista_caracteres = list(palavra)
    
    
    n = len(lista_caracteres)
    for i in range(n):
        for j in range(0, n - i - 1):
            if lista_caracteres[j] > lista_caracteres[j + 1]:
                lista_caracteres[j], lista_caracteres[j + 1] = lista_caracteres[j + 1], lista_caracteres[j]
    
    return ''.join(lista_caracteres)


# 4. Ordenar palavras pela quantidade de letras minúsculas
def contar_minusculas(palavra):
    
    return sum(1 for c in palavra if 'a' <= c <= 'z')


def ordenar_por_minusculas(palavras):
    
    n = len(palavras)
    for i in range(n):
        for j in range(0, n - i - 1):
            if contar_minusculas(palavras[j]) > contar_minusculas(palavras[j + 1]):
                palavras[j], palavras[j + 1] = palavras[j + 1], palavras[j]
    return palavras


# 5. Agrupar por letra inicial e ordenar cada grupo
def agrupar_e_ordenar(palavras):
    """Exercício 5: Agrupa por letra inicial e ordena cada grupo"""
    from collections import defaultdict
    grupos = defaultdict(list)
    
    for palavra in palavras:
        if palavra:  
            letra_inicial = palavra[0].lower()
            grupos[letra_inicial].append(palavra)
    
    
    resultado = {}
    for letra in sorted(grupos.keys()):
        grupo = grupos[letra]
        
        resultado[letra] = ordenar_alfabetico(grupo[:])  
    
    return resultado