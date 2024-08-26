import streamlit as st
import streamlit_authenticator as stauth
import os
from google.cloud import bigquery
import pandas as pd
import pandas_gbq
import datetime
import yaml
from yaml.loader import SafeLoader
from utils import connect_bigquery
from queries import query_estoque, query_inadimplencia, query_contatos
from pages import BasePage, RelatorioEstoquePage, RelatorioInadimplenciaPage, RelatorioContatosPage, PageManager


# Configurações iniciais e autenticação
today = datetime.date.today()
thirty_days_ago = today - datetime.timedelta(days=30)
six_months_ago = today - datetime.timedelta(days=180)


first_day_of_current_month = today.replace(day=1)

# Subtrair um dia para obter o último dia do mês passado
last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)

print(last_day_of_previous_month)

project_id = 'manchester-ai'

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

passwords = ["abc", "def"]
hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days'],
    pre_authorized=config['pre-authorized'], auto_hash=False
)

name, authentication_status, username = authenticator.login()

if authentication_status:
    logo = 'https://storage.googleapis.com/imagem_app/logo_transparente.png'
    st.sidebar.image(logo, width=300)
    st.sidebar.write(f"Bem-vindo(a), {name}!")
    
    authenticator.logout(location='sidebar')
    
    # Conexão com BigQuery
    cliente = connect_bigquery()
    
    df_estoque = pandas_gbq.read_gbq(query_estoque, project_id=project_id)
    df_inadimplencia = pandas_gbq.read_gbq(query_inadimplencia, project_id=project_id)
    df_contatos = pandas_gbq.read_gbq(query_contatos, project_id=project_id)
    
    # Criação e gerenciamento de páginas
    page_manager = PageManager(thirty_days_ago, today, name)
    page_manager.add_page("Cotações com falta de Estoque", RelatorioEstoquePage(df_estoque, thirty_days_ago, today, name))
    page_manager.add_page("Relatório de Inadimplência", RelatorioInadimplenciaPage(df_inadimplencia, six_months_ago, last_day_of_previous_month, name))
    page_manager.add_page("Relatório de Contatos", RelatorioContatosPage(df_contatos, name))
    
    # Seleção e renderização da página
    selected_page = st.sidebar.selectbox("Selecione a Página", list(page_manager.pages.keys()))
    page_manager.render(selected_page)

elif authentication_status == False:
    st.error("Usuário ou senha incorretos")

elif authentication_status == None:
    st.warning("Por favor, insira seu usuário e senha")







#Cotações com falta de estoque - mudar a lógica para mostrar as quantidades na unidade cotada, não apenas em KG
#Adicionar coluna com 'matéria prima alternativa'
#Como o nome mudou, ver com Felipe potencial mudança da descrição


#Relatório de contatos 
#Implementar relatório especial para gerência, com agregados resumindo a situação de cada vendedor

# Vendedor - Carteira(qtd) - Já entrou em contato - Já cotou - Já vendeu - Qtos faltam - Ritmo - Pct




