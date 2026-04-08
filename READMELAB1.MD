 Sistema de Chat com Deteção de Dados Pessoais (GDPR)
 Descrição

Este projeto foi desenvolvido no âmbito da unidade curricular PAC e consiste num sistema de chat multiusuário em tempo real implementado em Python. 
 Funcionalidades

- Suporte a múltiplos utilizadores em simultâneo
- Deteção de dados pessoais (GDPR) com expressões regulares
- Bloqueio de mensagens com dados sensíveis
- Registo de atividade e violações GDPR
- Mensagens privadas (/pm)


 Tecnologias Utilizadas

- Python 3
- socket
- threading
- re (expressões regulares)
- datetime
- os

 Como Executar
Abre o terminal e liga primeiro de tudo o servidor depois sim os clientes para eles se conectarem.
Alguns atalhos criados.
-/online	Mostra a lista de utilizadores atualmente ligados
-/pm nome mensagem	Envia uma mensagem privada para outro utilizador	exe:/pm João Olá, tudo bem?
-texto normal	Envia uma mensagem pública para toda a sala exemp: Ciseg para sempre
-Todas as menssagens com informaçoes como: Email,Telefone,Endereço IP,Nome completo,Data de nascimento,Cartão de crédito e passwords nao seram mostradas no servidor e quem enviou recebera um aviso
gdpr-chat/
├── server.py
├── client.py
├── registos/
│   ├── dados_pessoais.txt
│   └── atividade.txt
└── README.md
 Logs e Registo de Atividade
 Regista entradas e saídas de utilizadores:atividade.txt
 Regista tentativas de envio de dados pessoais:dados_pessoais.txt


Tomás Leão