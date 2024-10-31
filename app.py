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
from queries import query_estoque, query_inadimplencia, query_contatos, query_comissao
from pages import BasePage, Relatorio_Estoque_Page, Relatorio_Inadimplencia_Page, Relatorio_Contatos_Page, PageManager, Relatorio_ContatosAgregados_Page, Relatorio_Comissao_Page, Relatorio_ComissaoAgregados_Page, Relatorio_Vendas_Page
from dateutil.relativedelta import relativedelta

# Configurações iniciais e autenticação
today = datetime.date.today()
thirty_days_ago = today - datetime.timedelta(days=30)
six_months_ago = today - datetime.timedelta(days=180)

first_day_six_months_ago = (today - relativedelta(months=6)).replace(day=1)
first_day_of_current_month = today.replace(day=1)
last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)

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

# Funções com cache para evitar consultas repetidas
@st.cache_data(ttl=600)  # cache válido por 10 minutos
def get_estoque_data():
    return pandas_gbq.read_gbq(query_estoque, project_id=project_id)

@st.cache_data(ttl=600)
def get_inadimplencia_data():
    return pandas_gbq.read_gbq(query_inadimplencia, project_id=project_id)

@st.cache_data(ttl=600)
def get_contatos_data():
    return pandas_gbq.read_gbq(query_contatos, project_id=project_id)

# @st.cache_data(ttl=600)
# def get_comissao_data():
#     return pandas_gbq.read_gbq(query_comissao, project_id=project_id)

if authentication_status:
    logo = 'https://storage.googleapis.com/imagem_app/logo_transparente.png'
    st.sidebar.image(logo, width=300)
    st.sidebar.write(f"Bem-vindo(a), {name}!")
    
    authenticator.logout(location='sidebar')

    # Conexão com BigQuery
    cliente = connect_bigquery()
    
    # Recuperando dados com cache
    df_estoque = get_estoque_data()
    df_inadimplencia = get_inadimplencia_data()
    df_contatos = get_contatos_data()
    # df_comissao = get_comissao_data()
    
    # Criação e gerenciamento de páginas
    page_manager = PageManager(thirty_days_ago, today, name)
    page_manager.add_page("Cotações com falta de Estoque", Relatorio_Estoque_Page(df_estoque, thirty_days_ago, today, name))
    page_manager.add_page("Relatório de Inadimplência", Relatorio_Inadimplencia_Page(df_inadimplencia, six_months_ago, last_day_of_previous_month, name))
    page_manager.add_page("Relatório de Contatos", Relatorio_Contatos_Page(df_contatos, name))
    page_manager.add_page("Relatório de Contatos - Agregado", Relatorio_ContatosAgregados_Page(df_contatos, name), allowed_users=["Gerência"])
    # page_manager.add_page("Relatório de Comissão", Relatorio_Comissao_Page(df_comissao, name, first_day_six_months_ago, today), allowed_users = ['Gerência'])
    # page_manager.add_page("Relatório de Comissão - Agregado", Relatorio_ComissaoAgregados_Page(df_comissao, name), allowed_users=["Gerência"])
    page_manager.add_page("Relatório de Vendas", Relatorio_Vendas_Page(df_contatos, name))

    # Seleção e renderização da página
    selected_page = st.sidebar.selectbox("Selecione a Página", list(page_manager.pages.keys()))
    page_manager.render(selected_page)

elif authentication_status == False:
    st.error("Usuário ou senha incorretos")

elif authentication_status == None:
    st.warning("Por favor, insira seu usuário e senha")








#Cotações com falta de estoque - mudar a lógica para mostrar as quantidades na unidade cotada, não apenas em KG
#Adicionar coluna com 'matéria prima alternativa'

# contatos -- conversao(%) e novos clientes

# estoque -- separar por gerencia(filtro) - código do produto