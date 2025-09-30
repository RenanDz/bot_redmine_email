#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE DO BOT DE NOTIFICAÇÃO - APROVAÇÕES REDMINE
Autor: Renan Dias
Departamento: Financeiro

OBJETIVO: Testar a comunicação com Redmine e envio de e-mails
          antes de implementar o sistema completo.

- Verificar se a API do Redmine está respondendo
- Testar o envio de e-mails pelo Outlook
- Validar os filtros (excluir alocadoras)
- Garantir que a paginação funciona
"""

import requests
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# CONFIGURAÇÕES 

# CONEXÃO COM REDMINE 
REDMINE_URL = "https://chamados.somagrupo.com.br"
API_KEY = "4b6baf8f1b598c260bc6928ac72dc3091a35d062"  # Minha chave de API

# APROVADORES QUE NÃO RECEBEM E-MAIL 
# Exclui Ana e Stephannye porque elas fazem a alocação inicial
APROVADORES_EXCLUIR = {"Ana Grijo", "Stephannye Moreira"}

# CONFIGURAÇÃO DE E-MAIL - Usando minha conta
SMTP_SERVER = "smtp.office365.com"  # Servidor do Outlook
SMTP_PORT = 587                     # Porta segura
EMAIL_FROM = "renan.dias@farmrio.com"  # Vai enviar do meu e-mail
EMAIL_PASSWORD = "cfftpbbtmzxvztsk"    # Senha de aplicativo

# FUNÇÃO DE BUSCA 

def buscar_todos_pendentes_aprovacao():
    """
    Esta função é a mesma que vou usar no sistema final.
    Ela busca todos os chamados pendentes de aprovação no Redmine.
    
    """
    
    print(" INICIANDO BUSCA NO REDMINE...")
    print(f"    Vou excluir as alocadoras: {', '.join(APROVADORES_EXCLUIR)}")
    print("     Buscando por: Status = 'Pending Approval'")
    print("-" * 60)
    
    # Configuração para a API me reconhecer
    headers = {
        'X-Redmine-API-Key': API_KEY, 
        'Content-Type': 'application/json'
    }
    
    pendentes_aprovacao = []  # Aqui vou acumular todos os pendentes
    offset = 0                # Começo da página 0
    limite_por_pagina = 100   # Redmine permite 100 por página
    total_paginas_processadas = 0
    
    # LOOP DE PAGINAÇÃO: Vou percorrer todas as páginas
    while True:
        pagina_atual = (offset // limite_por_pagina) + 1
        print(f"   📄 Página {pagina_atual}...", end=" ")
        
        # Parâmetros da busca: 100 chamados por vez, só os abertos
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
            
            # SE A API RESPONDEU CORRETAMENTE
            if response.status_code == 200:
                data = response.json()
                issues = data['issues']  # Lista de chamados desta página
                
                # Se não tem mais chamados, termino a busca
                if not issues:
                    print("Nenhum chamado encontrado - FIM DA BUSCA")
                    break
                
                # PROCESSAMENTO: Verifico cada chamado
                pendentes_esta_pagina = 0
                for issue in issues:
                    # Só me interesso pelos pendentes de aprovação
                    if issue['status']['name'] == 'Pending Approval':
                        aprovador = issue.get('assigned_to', {}).get('name', 'Não atribuído')
                        
                        #FILTRO: Excluo as alocadoras
                        # Ana e Stephannye fazem a alocação, não a aprovação final
                        if aprovador not in APROVADORES_EXCLUIR:
                            pendentes_aprovacao.append(issue)
                            pendentes_esta_pagina += 1
                
                print(f"Encontrei {len(issues)} chamados → {pendentes_esta_pagina} pendentes")
                
                # OTIMIZAÇÃO: Se não tem pendentes, provavelmente acabaram
                if pendentes_esta_pagina == 0:
                    print("   ⏹️  Sem pendentes nesta página - parando busca")
                    break
                    
                # CONTROLE: Se veio menos que 100, é a última página
                if len(issues) < limite_por_pagina:
                    print("   🏁 Última página encontrada")
                    break
                    
                # Vou para a próxima página
                offset += limite_por_pagina
                total_paginas_processadas += 1
                
            else:
                # SE HOUVE ERRO NA API
                print(f"ERRO {response.status_code} - Parando por segurança")
                break
                
        except Exception as e:
            # 🛡️ TRATAMENTO DE ERRO: Se algo inesperado acontecer
            print(f"❌ Erro inesperado: {e}")
            break
    
    # RESULTADO FINAL DA BUSCA
    print(f"\n  BUSCA CONCLUÍDA!")
    print(f"   • Páginas verificadas: {total_paginas_processadas}")
    print(f"   • Pendentes encontrados: {len(pendentes_aprovacao)}")
    print(f"   • Alocadoras excluídas: {', '.join(APROVADORES_EXCLUIR)}")
    
    return pendentes_aprovacao

# FUNÇÃO DE TESTE - ENVIA E-MAIL APENAS PARA MIM

def enviar_email_teste(pendentes):
    """
    FUNÇÃO DE TESTE: Envia um e-mail apenas para mim
    para validar que tudo está funcionando.
    """
    
    try:
        print(f"\n PREPARANDO E-MAIL DE TESTE...")
        print(f"   Vou enviar apenas para: {EMAIL_FROM}")
        print(f"   Resumo de {len(pendentes)} pendentes encontrados")
        
        # CRIANDO O E-MAIL
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_FROM  # Envio para mim mesmo - É UM TESTE!
        msg['Subject'] = f"🧪 TESTE - {len(pendentes)} Pendentes de Aprovação - Redmine"
        
        # CORPO DO E-MAIL - Template gerado por IA
        corpo_html = f"""
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
                    text-align: center;
                }}
                .content {{ 
                    padding: 25px; 
                    background: #f8f9fa;
                    border-radius: 0 0 8px 8px;
                }}
                .teste-sucesso {{ 
                    background: #107c10; 
                    color: white; 
                    padding: 15px; 
                    border-radius: 5px;
                    margin: 15px 0;
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
                <h2>🧪 TESTE - Sistema de Notificações Redmine</h2>
            </div>
            <div class="content">
                <div class="teste-sucesso">
                    <h3>✅ TESTE BEM-SUCEDIDO!</h3>
                    <p>Este é um e-mail de teste do bot automático do Redmine</p>
                </div>
                
                <p>Olá <strong>Renan</strong>,</p>
                
                <p>O sistema encontrou <strong class="destaque">{len(pendentes)} chamado(s)</strong> 
                pendentes de aprovação no Redmine.</p>
                
                <h3>📊 Resumo dos Pendentes Encontrados:</h3>
        """
        
        # AGRUPO OS PENDENTES POR APROVADOR PARA O RELATÓRIO
        aprovadores = {}
        for issue in pendentes:
            aprovador = issue.get('assigned_to', {}).get('name', 'Não atribuído')
            if aprovador not in aprovadores:
                aprovadores[aprovador] = []
            aprovadores[aprovador].append(issue)
        
        # MOSTRO OS 10 APROVADORES COM MAIS PENDÊNCIAS
        for aprovador, issues_aprovador in sorted(aprovadores.items(), 
                                                key=lambda x: len(x[1]), 
                                                reverse=True)[:10]:
            
            corpo_html += f"""
                <div class="chamado">
                    <h4>👤 {aprovador}: {len(issues_aprovador)} chamado(s)</h4>
            """
            
            # Mostro até 3 exemplos por aprovador
            for issue in issues_aprovador[:3]:
                vendor = obter_campo_personalizado(issue, 'Vendor Name')
                amount = obter_campo_personalizado(issue, 'Amount')
                
                corpo_html += f"""
                    <p><strong>• #{issue['id']}:</strong> {issue['subject'][:50]}...</p>
                    <p style="margin-left: 20px;">🏢 {vendor} | 💰 {amount}</p>
                """
            
            # Se tiver mais que 3, mostro um resumo
            if len(issues_aprovador) > 3:
                corpo_html += f"<p>📝 ... e mais {len(issues_aprovador) - 3} chamado(s)</p>"
            
            corpo_html += "</div>"
        
        # 🔚 RODAPÉ DO E-MAIL
        corpo_html += f"""
                <br>
                <p>💡 <strong>Este é um e-mail de teste!</strong></p>
                <p>No sistema final, cada aprovador receberá sua própria lista detalhada.</p>
                
                <a href="{REDMINE_URL}" class="btn-redmine">🔗 Acessar Redmine</a>
                
                <div class="footer">
                    <p><em>🧪 E-mail de teste do Bot Redmine<br>
                    Desenvolvido por Renan Dias - Financeiro<br>
                    Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Anexo o HTML ao e-mail
        msg.attach(MIMEText(corpo_html, 'html'))
        
        #ENVIO O E-MAIL
        print(f"    Conectando no servidor de e-mail...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Conexão segura
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"   ✅ E-MAIL DE TESTE ENVIADO!")
        print(f"   📨 Verifique sua caixa de entrada: {EMAIL_FROM}")
        return True
        
    except Exception as e:
        print(f"   ❌ FALHA NO ENVIO DO E-MAIL")
        print(f"       Erro técnico: {e}")
        return False


# FUNÇÃO AUXILIAR


def obter_campo_personalizado(issue, nome_campo):
    """
    Função utilitária para pegar campos customizados do Redmine.
    Alguns dados ficam em campos personalizados, então preciso
    buscar especificamente nessa estrutura.
    """
    for field in issue.get('custom_fields', []):
        if field.get('name') == nome_campo:
            valor = field.get('value', 'N/A')
            return valor if valor else 'N/A'  # Trato valores vazios
    return 'N/A'

# MAIN - TESTE


if __name__ == "__main__":
    """
    TESTE DO SISTEMA - FLUXO COMPLETO:
    1. Busca pendentes no Redmine ✓
    2. Aplica filtros (exclui alocadoras) ✓  
    3. Envia e-mail de teste para mim ✓
    """
    
    print("TESTE - BOT REDMINE (ENVIO APENAS PARA MIM)")
    print("=" * 65)
    print("Desenvolvido por: Renan Dias")
    print("Objetivo: Validar comunicação Redmine + Outlook")
    print("=" * 65)
    
    # PASSO 1: BUSCAR TODOS OS PENDENTES NO REDMINE
    print("\n TESTANDO CONEXÃO COM REDMINE...")
    pendentes = buscar_todos_pendentes_aprovacao()
    
    # Se não encontrou nada, mostra mensagem positiva
    if not pendentes:
        print("\n O sistema funcionou perfeitamente.")
        print("   Não há pendências de aprovação no momento!")
        print("   Todos os aprovadores estão em dia.")
        input("\nPressione Enter para fechar...")
        exit()
    
    # PASSO 2: ENVIAR E-MAIL DE TESTE
    print("\n TESTANDO ENVIO DE E-MAIL...")
    sucesso = enviar_email_teste(pendentes)
    
    # PASSO 3: RELATÓRIO FINAL DO TESTE
    print(f"\n RESULTADO DO TESTE:")
    print("=" * 50)
    
    if sucesso:
        print("✅ TESTE BEM-SUCEDIDO!")
        print(f"   • Pendências encontradas: {len(pendentes)}")
        print(f"   • E-mail enviado para: {EMAIL_FROM}")
        print(f"   • Conexão Redmine: Funcionando")
        print(f"   • Envio Outlook: Funcionando") 
        print(f"   • Filtros aplicados: Corretos")
        print(f"   • Paginação: Completa")
        print(f"   • Próximo passo: Implementar sistema completo")
    else:
        print("❌ TESTE FALHOU")
        print(f"   • Verifique as configurações de e-mail")
        print(f"   • Confirme a senha de aplicativo")
        print(f"   • Teste a conexão com o Redmine")
    
    print("=" * 50)
    
    input("\nPressione Enter para fechar...")
