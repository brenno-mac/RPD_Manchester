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
from pages import PageManager, Relatorio_Estoque_Page, Relatorio_Inadimplencia_Page, Relatorio_Contatos_Page, Relatorio_ContatosAgregados_Page, Relatorio_Vendas_Page
from dateutil.relativedelta import relativedelta
from utils import transform_df_estoque, transform_df_inadimplencia, transform_df_contatos, transform_df_contatosagregados, transform_df_comissao, transform_df_comissao_agregado, transform_df_vendas



# Configurações iniciais e autenticação
today = datetime.date.today()
thirty_days_ago = today - datetime.timedelta(days=30)
six_months_ago = today - datetime.timedelta(days=180)
first_day_of_current_month = today.replace(day=1)
last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)

project_id = 'manchester-ai'

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days'],
    pre_authorized=config['pre-authorized'], auto_hash=False
)

name, authentication_status, username = authenticator.login()

# Funções com cache para evitar consultas repetidas
@st.cache_data(ttl=600)
def get_estoque_data():
    return pandas_gbq.read_gbq(query_estoque, project_id=project_id)

@st.cache_data(ttl=600)
def get_inadimplencia_data():
    return pandas_gbq.read_gbq(query_inadimplencia, project_id=project_id)

@st.cache_data(ttl=600)
def get_contatos_data():
    return pandas_gbq.read_gbq(query_contatos, project_id=project_id)

# Inicializa o estado da página, caso não esteja definido
if 'selected_page' not in st.session_state:
    st.session_state['selected_page'] = "Painel de Relatórios"

# Função callback para alterar a página
def set_page(page_name):
    st.session_state['selected_page'] = page_name

def pagina_inicial(page_manager):
    st.title("Painel de Relatórios")
    cols = st.columns(3)  # Três colunas para distribuir os cards

    # Lista de relatórios
    for i, (page_name, page_obj) in enumerate(page_manager.pages.items()):
        with cols[i % 3]:  # Alterna entre as três colunas
            st.markdown(f"### {page_name}")
            st.write(page_obj.get_description())
            # Botão que utiliza o callback `set_page` para atualizar `selected_page`
            st.button(f"Abrir {page_name}", on_click=set_page, args=(page_name,), key=page_name)



if authentication_status:
    logo = 'https://storage.googleapis.com/imagem_app/logo_transparente.png'
    st.sidebar.image(logo, width=300)
    st.sidebar.write(f"Bem-vindo(a), {name}!")
    
    authenticator.logout(location='sidebar')
    # Conexão com BigQuery
    cliente = connect_bigquery()
    
    # Recuperando dados com cache
    df_contatos = get_contatos_data()
    
    # df_estoque = (
    # get_estoque_data()
    # .pipe(transform_df_estoque, start_date=thirty_days_ago, end_date=today, name=name))
    
    df_estoque = get_estoque_data()
    
    
    df_inadimplencia = get_inadimplencia_data()
    
    
    # df_inadimplencia = (
    # get_inadimplencia_data()
    # .pipe(transform_df_inadimplencia, start_date=six_months_ago, end_date=last_day_of_previous_month, name=name))
    
    # Criação e gerenciamento de páginas
    page_manager = PageManager(thirty_days_ago, today, name)
    
    page_manager.add_page("Cotações com falta de Estoque", Relatorio_Estoque_Page(df_estoque, thirty_days_ago, today, name))
    page_manager.add_page("Relatório de Inadimplência", Relatorio_Inadimplencia_Page(df_inadimplencia, six_months_ago, last_day_of_previous_month, name))
    page_manager.add_page("Relatório de Contatos", Relatorio_Contatos_Page(df_contatos, name))
    page_manager.add_page("Relatório de Contatos - Agregado", Relatorio_ContatosAgregados_Page(df_contatos, name), allowed_users=["Gerência"])
    page_manager.add_page("Relatório de Vendas", Relatorio_Vendas_Page(df_contatos, name))

    # Renderiza a página selecionada
    if st.session_state['selected_page'] == "Painel de Relatórios":
        pagina_inicial(page_manager)
    else:
        page_manager.render(st.session_state['selected_page'])
        # Botão de voltar, utilizando callback
        st.sidebar.button("Voltar ao Painel de Relatórios", on_click=set_page, args=("Painel de Relatórios",))

elif authentication_status == False:
    st.error("Usuário ou senha incorretos")

elif authentication_status == None:
    st.warning("Por favor, insira seu usuário e senha")
