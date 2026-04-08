 Sistema de Chat com Deteção de Dados Pessoais (GDPR)

 Descrição

Este projeto consiste num sistema de chat multiusuário desenvolvido em Python, com deteção automática de dados pessoais em conformidade com o GDPR.

O servidor analisa as mensagens e bloqueia as que contenham dados sensíveis, registando as ocorrências.

 Funcionalidades

- Suporte a múltiplos utilizadores em simultâneo
- Deteção de dados pessoais (GDPR) com expressões regulares
- Bloqueio de mensagens com dados sensíveis
- Registo de atividade e violações GDPR
- Mensagens privadas (/pm)
- Interface colorida com colorama

 Tecnologias Utilizadas

- Python 3
- socket
- threading
- re (expressões regulares)

 Como Executar

gdpr-chat/
├── server.py
├── client.py
├── registos/
│   ├── dados_pessoais.txt
│   └── atividade.txt
└── README.md