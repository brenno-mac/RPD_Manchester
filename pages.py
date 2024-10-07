import streamlit as st
from utils import transform_df_estoque, transform_df_inadimplencia, transform_df_contatos, transform_df_contatosagregados, transform_df_comissao, transform_df_comissao_agregado
from io import BytesIO
import pandas as pd

from datetime import datetime

today = datetime.now()

class PageManager:
    def __init__(self, start_date, end_date, user_name):
        self.pages = {}
        self.start_date = start_date
        self.end_date = end_date
        self.user_name = user_name

    def add_page(self, name, page, allowed_users=None):
        if allowed_users is None or self.user_name in allowed_users:
            self.pages[name] = page

    def render(self, page_name):
        page = self.pages.get(page_name)
        if page:
            page.render()
        else:
            st.error(f"Página '{page_name}' não encontrada ou você não tem permissão para acessá-la.")

class BasePage:
    def __init__(self, title, start_date, end_date, user_name):
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.user_name = user_name

    def render(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def filter_dates(self):
        return st.sidebar.date_input(label="Período", value=[self.start_date, self.end_date])
    
    def select_box(self, label, options, placeholder):
        return st.sidebar.selectbox(label = label, options = (options), index=None, placeholder = placeholder)

    def checkbox(self, label, value):
        return st.sidebar.checkbox(label = label, value = value)
    
    
class Relatorio_Estoque_Page(BasePage):
    def __init__(self, df, start_date, end_date, user_name):
        super().__init__("Cotações com falta de Estoque", start_date, end_date, user_name)
        self.df = df

    def to_excel(self, df):
        # Criando um buffer de Bytes para o arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        # Movendo o cursor para o início do buffer
        output.seek(0)
        return output

    def render(self):
        start_date, end_date = self.filter_dates()
        df_transformed = transform_df_estoque(self.df, start_date, end_date, self.user_name)
        excel_data = self.to_excel(df_transformed)
        st.title(self.title)
        if self.user_name == 'Gerência':
            st.write(f"Abaixo está o relatório de estoque em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de estoque para a vendedora {self.user_name}:")
        st.dataframe(df_transformed, 
                     column_config={
                        "Data Cotada": st.column_config.DateColumn(label="Data Cotada", format="DD/MM/YYYY"),
                        "Valor da Nota": st.column_config.NumberColumn(label="Valor da Nota", format="R$ %.0f")                            
                     },
                    hide_index=True)
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name=f'relatorio_estoque{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
class Relatorio_Inadimplencia_Page(BasePage):
    def __init__(self, df, start_date, end_date, user_name):
        super().__init__("Relatório de Inadimplência", start_date, end_date, user_name)
        self.df = df

    def to_excel(self, df):
        # Criando um buffer de Bytes para o arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        # Movendo o cursor para o início do buffer
        output.seek(0)
        return output

    def render(self):
        start_date, end_date = self.filter_dates()
        checkbox_90_days = self.checkbox(label = 'Últimos 90 dias e fora do Serasa', value = False)
        df_transformed = transform_df_inadimplencia(self.df, start_date, end_date, self.user_name, checkbox_90_days)
        
        excel_data = self.to_excel(df_transformed)
        st.title(self.title)
        total_valor = round(df_transformed['Valor da Parcela'].sum(), 2)
        
        total_valor_formatted = f"{total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if self.user_name == 'Gerência':
            st.write("Abaixo está o relatório de inadimplência em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de inadimplência para a vendedora {self.user_name}:")
            st.write(f"Você tem um total de {len(df_transformed)} notas inadimplentes, com um valor total de {total_valor_formatted} R$.")
        st.dataframe(df_transformed, 
                     column_config={
                         "Data de Vencimento" : st.column_config.DateColumn(label="Data de Vencimento", format="DD/MM/YYYY"),
                         "Valor da Parcela": st.column_config.NumberColumn(label="Valor da Parcela", format="R$ %.0f")
                     },
                     hide_index=True)
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name=f'relatorio_inadimplencia{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

class Relatorio_Contatos_Page(BasePage):
    def __init__(self, df, user_name):
        super().__init__("Relatório de Contatos", None, None, user_name)
        self.df = df

    def to_excel(self, df):
        # Criando um buffer de Bytes para o arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        # Movendo o cursor para o início do buffer
        output.seek(0)
        return output

    def render(self):
        st.title(self.title)
        if self.user_name == 'Gerência':
            st.write(f"Abaixo está o relatório de contatos em nível gerencial:")

            # Filtros para o usuário "Gerência"
            selectbox_vendedor = self.select_box(label="Escolha um vendedor", options=self.df['apelido'].unique(), placeholder="Selecione o vendedor")
            selectbox_telemarketing = self.select_box(label="Telemarketing?", options=self.df['telemarketing_feito'].unique(), placeholder="Selecione se houve telemarketing")
            selectbox_cotacao = self.select_box(label="Cotou?", options=self.df['cotacao_feita'].unique(), placeholder="Selecione se houve cotação")
            selectbox_venda = self.select_box(label="Vendeu?", options=self.df['venda_feita'].unique(), placeholder="Selecione se houve venda")
        else:
            st.write(f"Abaixo está o relatório de contatos para a vendedora {self.user_name}:")
            selectbox_vendedor = None
            selectbox_telemarketing = None
            selectbox_cotacao = None
            selectbox_venda = None
            # Adiciona o cálculo de métricas se o usuário não for "Gerência"
            if round((len(self.df[(self.df['apelido'] == self.user_name.upper()) & (self.df['contactou_ou_nao'] == 'Contato feito')]))/(len(self.df[self.df['apelido'] == self.user_name.upper()])) * 100, 2) == 100:
                st.metric(label="", value="Parabéns, meta batida!")
            else:
                st.metric(label="Contatos Feitos, em %", value=f"{round((len(self.df[(self.df['apelido'] == self.user_name.upper()) & (self.df['contactou_ou_nao'] == 'Contato feito')]))/(len(self.df[self.df['apelido'] == self.user_name.upper()])) * 100, 2)} %")
        # Transforma o dataframe usando os filtros (se existirem)
        df_transformed = transform_df_contatos(self.df, self.user_name, selectbox_vendedor, selectbox_telemarketing, selectbox_cotacao, selectbox_venda)
        
        excel_data = self.to_excel(df_transformed)
        
        st.dataframe(df_transformed,
                     column_config={
                         "Último Telemarketing": st.column_config.DateColumn(label="Último Telemarketing", format="DD/MM/YYYY"),
                         "Última Cotação": st.column_config.DateColumn(label="Última Cotação", format="DD/MM/YYYY"),
                         "Última Venda": st.column_config.DateColumn(label="Última Venda", format="DD/MM/YYYY")
                     },
                     hide_index=True)
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name=f'relatorio_contatos{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
class Relatorio_ContatosAgregados_Page(BasePage):
    def __init__(self, df, user_name):
        super().__init__("Relatório de Contatos - Agregado", None, None, user_name)
        self.df = df

    def to_excel(self, df):
        # Criando um buffer de Bytes para o arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        # Movendo o cursor para o início do buffer
        output.seek(0)
        return output

    def render(self):
        df_transformed = transform_df_contatosagregados(self.df, self.user_name)
        st.title(self.title)
        if self.user_name == 'Gerência':
            st.write(f"Abaixo está o relatório de contatos agregados em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de contatos agregados para a vendedora {self.user_name}:")
        st.dataframe(df_transformed,
                     hide_index=True)
        
        excel_data = self.to_excel(df_transformed)
        
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name=f'relatorio_contatos_agregados{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
class Relatorio_Comissao_Page(BasePage):
    def __init__(self, df, user_name, start_date, end_date):
        super().__init__("Relatório de Comissão", start_date, end_date, user_name)
        self.df = df

    def to_excel(self, df):
        # Criando um buffer de Bytes para o arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        # Movendo o cursor para o início do buffer
        output.seek(0)
        return output

    def render(self):
        start_date, end_date = self.filter_dates()
        mes_vigente = self.checkbox(label="Mês Vigente", value = True)
        st.title(self.title)
        
        # df_transformed['Comissão'] = df_transformed['Comissão'].str.replace('.', '').str.replace(',', '.').astype(float)
        total_valor = self.df['comiss'].sum()
        total_valor_formatted = f"{total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if self.user_name == 'Gerência':
            selectbox_vendedor = self.select_box(label="Escolha um vendedor", options=self.df['apelido'].unique(), placeholder="Selecione o vendedor")
            st.write(f"Abaixo está o relatório de comissão em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de comissão para a vendedora {self.user_name}:")
            st.write(f"No período selecionado, você tem comissões que totalizam o valor de {total_valor_formatted} R$.")
            
        df_transformed = transform_df_comissao(self.df, self.user_name, start_date, end_date, mes_vigente, selectbox_vendedor)
            
            
        st.dataframe(df_transformed,
                     column_config={
                         "Data Faturada" : st.column_config.DateColumn(label="Data Faturada", format="DD/MM/YYYY"),
                         "Data de Vencimento" : st.column_config.DateColumn(label="Data de Vencimento", format="DD/MM/YYYY"),
                         "Data da Baixa" : st.column_config.DateColumn(label="Data da Baixa", format="DD/MM/YYYY"),
                         "Comissão" : st.column_config.NumberColumn(label="Comissão", format = "R$ %.2f"),
                         "Valor do Desdobramento" : st.column_config.NumberColumn(label="Valor do Desdobramento", format = "R$ %.0f")
                     },
                     hide_index=True)
        
        excel_data = self.to_excel(df_transformed)
        
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name=f'relatorio_comissao{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
            
class Relatorio_ComissaoAgregados_Page(BasePage):
    def __init__(self, df, user_name):
        super().__init__("Relatório de Comissão - Agregado", None, None, user_name)
        self.df = df

    def to_excel(self, df):
        # Criando um buffer de Bytes para o arquivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        # Movendo o cursor para o início do buffer
        output.seek(0)
        return output

    def render(self):
        df_transformed = transform_df_comissao_agregado(self.df, self.user_name)
        st.title(self.title)
        # if self.user_name == 'Gerência':
        #     st.write(f"Abaixo está o relatório de contatos agregados em nível gerencial:")
        # else:
        #     st.write(f"Abaixo está o relatório de contatos agregados para a vendedora {self.user_name}:")
        st.dataframe(df_transformed)
        
        excel_data = self.to_excel(df_transformed)
        
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name=f'relatorio_contatos_agregados{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
