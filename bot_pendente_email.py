#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DE NOTIFICAÇÃO - APROVAÇÕES REDMINE
Autor: Renan Dias
Departamento: Financeiro
"""

import requests
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# CONEXÃO COM REDMINE - Dados de acesso à nossa plataforma
REDMINE_URL = "https://chamados.somagrupo.com.br"
API_KEY = "4b6baf8f1b598c260bc6928ac72dc3091a35d062"  # Chave de API pessoal

# APROVADORES QUE NÃO RECEBEM E-MAIL - São as alocadoras
# Decidi excluir Ana e Stephannye porque elas fazem a alocação, não a aprovação final
APROVADORES_EXCLUIR = {"Ana Grijo", "Stephannye Moreira"}

# CONFIGURAÇÃO DE E-MAIL - Usando minha conta corporativa
# Configurei uma senha de app específica para esse bot
SMTP_SERVER = "smtp.office365.com"  # Servidor do Outlook
SMTP_PORT = 587                     # Porta segura para envio
EMAIL_FROM = "renan.dias@farmrio.com"  # Vai enviar do meu e-mail
EMAIL_PASSWORD = "cfftpbbtmzxvztsk"    # Senha de aplicativo - gerei uma única

# FUNÇÃO - BUSCA OS CHAMADOS PENDENTES

def buscar_todos_pendentes_aprovacao():
    
    print(" INICIANDO BUSCA NO REDMINE...")
    print(f"  Excluindo alocadoras: {', '.join(APROVADORES_EXCLUIR)}")
    print("   Buscando por: Status = 'Pending Approval'")
    print("-" * 60)
    
    # Configuro os headers para a API entender que sou eu
    headers = {
        'X-Redmine-API-Key': API_KEY, 
        'Content-Type': 'application/json'
    }
    
    pendentes_aprovacao = []  # Aqui vou guardar todos os pendentes encontrados
    offset = 0                # Começo da página 0
    limite_por_pagina = 100   # Redmine permite até 100 por página
    total_paginas = 0
    
    # LOOP: Vou percorrer todas as páginas até acabar os pendentes
    while True:
        pagina_atual = (offset // limite_por_pagina) + 1
        print(f"   📄 Página {pagina_atual}...", end=" ")
        
        # Parâmetros da busca: pego 100 chamados por vez, só os abertos
        params = {
            'limit': limite_por_pagina, 
            'offset': offset, 
            'status_id': 'open'  # Busco todos abertos e filtro depois
        }
        
        try:
            # FAÇO A CHAMADA PARA API DO REDMINE
            response = requests.get(f"{REDMINE_URL}/issues.json", 
                                  headers=headers, 
                                  params=params)
            
            # SE DEU CERTO
            if response.status_code == 200:
                data = response.json()
                issues = data['issues']  # Lista de chamados desta página
                
                # Se não tem mais chamados, paro o loop
                if not issues:
                    print("Nenhum chamado encontrado - FIM DA BUSCA")
                    break
                
                # PROCESSAMENTO: Verifico cada chamado individualmente
                pendentes_esta_pagina = 0
                for issue in issues:
                    # Apenas pendentes de aprovação
                    if issue['status']['name'] == 'Pending Approval':
                        aprovador = issue.get('assigned_to', {}).get('name', 'Não atribuído')
                        
                        # FILTRO: Excluo as alocadoras
                        if aprovador not in APROVADORES_EXCLUIR:
                            pendentes_aprovacao.append(issue)
                            pendentes_esta_pagina += 1
                
                print(f"Encontrei {len(issues)} chamados → {pendentes_esta_pagina} pendentes")
                
                #OTIMIZAÇÃO: Se não achei pendentes nesta página, provavelmente acabaram
                if pendentes_esta_pagina == 0:
                    print("   Sem pendentes nesta página - parando busca")
                    break
                    
                # CONTROLE: Se veio menos que 100, é a última página
                if len(issues) < limite_por_pagina:
                    print(" Última página atingida")
                    break
                    
                #Vou para a próxima página
                offset += limite_por_pagina
                total_paginas += 1
                
            else:
                #SE DEU ERRO NA API
                print(f"ERRO {response.status_code} - Parando por segurança")
                break
                
        except Exception as e:
            #TRATAMENTO DE ERRO: Se algo inesperado acontecer
            print(f"❌ Erro inesperado: {e}")
            break
    
    #RESULTADO FINAL DA BUSCA
    print(f"\n✅ BUSCA CONCLUÍDA!")
    print(f"   • Páginas verificadas: {total_paginas}")
    print(f"   • Pendentes encontrados: {len(pendentes_aprovacao)}")
    print(f"   • Alocadoras excluídas: {', '.join(APROVADORES_EXCLUIR)}")
    
    return pendentes_aprovacao

# FUNÇÃO PARA AGRUPAR POR APROVADOR

def agrupar_por_aprovador(pendentes):
    
    print("\n ORGANIZANDO PENDÊNCIAS POR APROVADOR...")
    
    aprovadores = {}  # Dicionário para guardar tudo organizado
    
    for issue in pendentes:
        aprovador = issue.get('assigned_to', {}).get('name', 'Não atribuído')
        
        # Se é um aprovador novo, crio uma entrada para ele
        if aprovador not in aprovadores:
            email = descobrir_email(aprovador)  # Tento descobrir o e-mail
            aprovadores[aprovador] = {
                'email': email,
                'pendentes': []  # Lista vazia para os chamados dele
            }
        
        # Adiciono esse chamado à lista do aprovador
        aprovadores[aprovador]['pendentes'].append(issue)
    
    print(f"   Organizado! {len(aprovadores)} aprovadores identificados")
    return aprovadores

def descobrir_email(nome_aprovador):
       
    # MAPEAMENTO MANUAL - Vou expandindo
    # Isso vai crescer com o tempo
    mapeamento_emails = {
        "Gabriella Wolf": "gabriella.wolf@farmrio.com",
        
    }
    
    # Primeiro checo se já está mapeado
    if nome_aprovador in mapeamento_emails:
        return mapeamento_emails[nome_aprovador]
    
    # Se não está, tento adivinhar pelo padrão da empresa
    partes_nome = nome_aprovador.lower().split()
    if len(partes_nome) >= 2:
        #Tento o formato: primeironome.ultimonome@farmrio.com
        email_auto = f"{partes_nome[0]}.{partes_nome[-1]}@farmrio.com"
        print(f"   E-mail não mapeado - Gerado automaticamente: {email_auto}")
        return email_auto
    
    # Se não consegui descobrir de nenhuma forma
    print(f"   ⚠️  ATENÇÃO: Não consegui descobrir e-mail para {nome_aprovador}")
    return None

# FUNÇÃO DE ENVIO DE E-MAIL

def enviar_email_aprovador(aprovador, email, pendentes):
    
    if not email:
        print(f"   ❌ IMPOSSÍVEL ENVIAR: {aprovador} não tem e-mail cadastrado")
        return False
    
    try:
        print(f"   📧 Preparando e-mail para {aprovador}...")
        
        # CRIANDO O E-MAIL
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = email
        msg['Subject'] = f"📋 {len(pendentes)} Chamado(s) Pendente(s) de Aprovação - Redmine"
        
        #CORPO DO E-MAIL EM HTML - IA fez o template
        corpo_html += f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{ 
                    background: #0078D4; 
                    color: white; 
                    padding: 20px; 
                    border-radius: 8px 8px 0 0;
                }}
                .content {{ 
                    padding: 25px; 
                    background: #f8f9fa;
                    border-radius: 0 0 8px 8px;
                }}
                .chamado {{ 
                    border-left: 4px solid #0078D4; 
                    padding: 15px; 
                    margin: 15px 0; 
                    background: white;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .destaque {{ 
                    color: #d13438; 
                    font-weight: bold; 
                    font-size: 1.1em;
                }}
                .btn-redmine {{
                    background: #0078D4; 
                    color: white; 
                    padding: 12px 20px; 
                    text-decoration: none; 
                    border-radius: 5px;
                    display: inline-block;
                    margin: 10px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 0.9em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📋 Aprovações Pendentes - Redmine</h2>
            </div>
            <div class="content">
                <p>Prezado(a) <strong>{aprovador}</strong>,</p>
                
                <p>Você tem <span class="destaque">{len(pendentes)} chamado(s)</span> 
                pendente(s) de sua aprovação no Redmine:</p>
                
                <h3>📊 Seus Chamados Pendentes:</h3>
        """
        
        # LISTA TODOS OS CHAMADOS PENDENTES
        for i, issue in enumerate(pendentes, 1):
            vendor = obter_campo_personalizado(issue, 'Vendor Name')
            amount = obter_campo_personalizado(issue, 'Amount')
            invoice = obter_campo_personalizado(issue, 'Invoice Number')
            
            corpo_html += f"""
                <div class="chamado">
                    <h4>#{i}: {issue['subject']}</h4>
                    <p><strong>ID:</strong> {issue['id']}</p>
                    <p><strong>Fornecedor:</strong> {vendor}</p>
                    <p><strong>Valor:</strong> {amount}</p>
                    <p><strong>Invoice:</strong> {invoice}</p>
                    <p><strong>Link:</strong> <a href="{REDMINE_URL}/issues/{issue['id']}">Acessar no Redmine</a></p>
                </div>
            """
        
        #RODAPÉ DO E-MAIL
        corpo_html += f"""
                <br>
                <p>💡 <strong>Acesse o Redmine para realizar as aprovações!</strong></p>
                <a href="{REDMINE_URL}" class="btn-redmine">🔗 Acessar Redmine</a>
                
                <div class="footer">
                    <p><em>E-mail enviado automaticamente pelo Sistema de Notificações<br>
                    Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}</em></p>
                    <p><small>Desenvolvido por Renan Dias - Financeiro</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Anexo o HTML ao e-mail
        msg.attach(MIMEText(corpo_html, 'html'))
        
        # ENVIO O E-MAIL
        print(f"   🔄 Conectando no servidor de e-mail...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Conexão segura
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"   ✅ E-MAIL ENVIADO para: {aprovador}")
        print(f"   📨 Destinatário: {email}")
        print(f"   📊 Pendências notificadas: {len(pendentes)}")
        return True
        
    except Exception as e:
        print(f"   ❌ FALHA NO ENVIO para {aprovador}")
        print(f"   🐛 Erro técnico: {e}")
        return False

# FUNÇÕES AUXILIARES

def obter_campo_personalizado(issue, nome_campo):
    """
    Função utilitária para pegar campos customizados do Redmine.
    O Redmine guarda alguns dados em campos personalizados, então
    preciso buscar especificamente nessa estrutura.
    """
    for field in issue.get('custom_fields', []):
        if field.get('name') == nome_campo:
            valor = field.get('value', 'N/A')
            return valor if valor else 'N/A'  # Trato valores vazios
    return 'N/A'  # Retorno padrão se não encontrar

# MAIN

if __name__ == "__main__":
    
    print("BOT REDMINE - NOTIFICAÇÕES AUTOMÁTICAS")
    print("=" * 65)
    print("Desenvolvido por: Renan Dias")
    print("Objetivo: Agilizar aprovações pendentes no Redmine")
    print("=" * 65)
    
    #PASSO 1: BUSCAR TODOS OS PENDENTES
    print("\n INICIANDO BUSCA NO REDMINE...")
    pendentes = buscar_todos_pendentes_aprovacao()
    
    # Se não encontrou nada, termina aqui
    if not pendentes:
        print("\n🎉 EXCELENTE! Não há pendências de aprovação no momento.")
        print("   Todos os aprovadores estão em dia!")
        input("\nPressione Enter para fechar...")
        exit()
    
    #PASSO 2: ORGANIZAR POR APROVADOR
    print("\n2️⃣  ORGANIZANDO PENDÊNCIAS...")
    aprovadores = agrupar_por_aprovador(pendentes)
    
    #PASSO 3: ENVIAR E-MAILS
    print(f"\n3️⃣  PREPARANDO ENVIO DE E-MAILS")
    print(f"   📬 {len(aprovadores)} aprovador(es) para notificar")
    print("-" * 50)
    
    sucessos = 0
    falhas = 0
    
    for aprovador, info in aprovadores.items():
        pendentes_aprovador = info['pendentes']
        email = info['email']
        
        print(f"\n👤 APROVADOR: {aprovador}")
        print(f"   📋 Pendências: {len(pendentes_aprovador)}")
        print(f"   📧 E-mail: {email if email else 'NÃO ENCONTRADO'}")
        
        if enviar_email_aprovador(aprovador, email, pendentes_aprovador):
            sucessos += 1
        else:
            falhas += 1
    
    #PASSO 4: RELATÓRIO FINAL
    print(f"\n  PROCESSO CONCLUÍDO!")
    print("=" * 50)
    print(f"RESUMO EXECUTIVO:")
    print(f"     -E-mails enviados com sucesso: {sucessos}")
    print(f"     -Falhas no envio: {falhas}")
    print(f"     -Total de pendências processadas: {len(pendentes)}")
    print(f"     -Aprovadores notificados: {sucessos}")
    print(f"     -Alocadoras excluídas: {', '.join(APROVADORES_EXCLUIR)}")
    print("=" * 50)
    
    input("\nPressione Enter para fechar o bot...")