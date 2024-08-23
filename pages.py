import streamlit as st
from utils import transform_df_estoque, transform_df_inadimplencia, transform_df_contatos


class PageManager:
    def __init__(self, start_date, end_date, user_name):
        self.pages = {}
        self.start_date = start_date
        self.end_date = end_date
        self.user_name = user_name

    def add_page(self, name, page):
        self.pages[name] = page

    def render(self, page_name):
        page = self.pages.get(page_name)
        if page:
            page.render()
        else:
            st.error(f"Página '{page_name}' não encontrada.")

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
    
    
    
class RelatorioEstoquePage(BasePage):
    def __init__(self, df, start_date, end_date, user_name):
        super().__init__("Cotações com falta de Estoque", start_date, end_date, user_name)
        self.df = df

    def render(self):
        start_date, end_date = self.filter_dates()
        df_transformed = transform_df_estoque(self.df, start_date, end_date, self.user_name)
        st.title(self.title)
        if self.user_name == 'Gerência':
            st.write(f"Abaixo está o relatório de estoque em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de estoque para a vendedora {self.user_name}:")
        st.dataframe(df_transformed, 
                     column_config={
                        "Data Cotada": st.column_config.DateColumn(label="Data Cotada", format="DD/MM/YYYY")                            
                     },
                    hide_index=True)
        
class RelatorioInadimplenciaPage(BasePage):
    def __init__(self, df, start_date, end_date, user_name):
        super().__init__("Relatório de Inadimplência", start_date, end_date, user_name)
        self.df = df

    def render(self):
        start_date, end_date = self.filter_dates()
        df_transformed = transform_df_inadimplencia(self.df, start_date, end_date, self.user_name)
        st.title(self.title)
        if self.user_name == 'Gerência':
            st.write("Abaixo está o relatório de inadimplência em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de inadimplência para a vendedora {self.user_name}:")
        st.dataframe(df_transformed, 
                     column_config={
                         "Data de Vencimento" : st.column_config.DateColumn(label="Data de Vencimento", format="DD/MM/YYYY")
                     },
                     hide_index=True)

class RelatorioContatosPage(BasePage):
    def __init__(self, df, user_name):
        super().__init__("Relatório de Contatos", None, None, user_name)
        self.df = df

    def render(self):
        df_transformed = transform_df_contatos(self.df, self.user_name)
        st.title(self.title)
        if self.user_name == 'Gerência':
            st.write(f"Abaixo está o relatório de contatos em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de contatos para a vendedora {self.user_name}:")
        st.dataframe(df_transformed,
                     column_config={
                         "Último Telemarketing" : st.column_config.DateColumn(label="Último Telemarketing", format="DD/MM/YYYY"),
                         "Última Cotação" : st.column_config.DateColumn(label="Última Cotação", format="DD/MM/YYYY"),
                         "Última Venda" : st.column_config.DateColumn(label="Última Venda", format="DD/MM/YYYY")
                     },
                     hide_index=True)