import streamlit as st
from utils import transform_df_estoque, transform_df_inadimplencia, transform_df_contatos, transform_df_contatosagregados, transform_df_comissao, transform_df_comissao_agregado, transform_df_vendas
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
    def __init__(self, title, start_date, end_date, user_name, description = ""):
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.user_name = user_name
        self.description = description

    def get_description(self):
        # Personalize a descrição com o nome do usuário
        return self.description.format(user_name=self.user_name)
    
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
        self.original_df = df
        self.df = transform_df_estoque(df, start_date=start_date, end_date=end_date, name=user_name)
        num_cotacoes = len(self.df)
        description = (f"Você tem {num_cotacoes} cotações com falta de estoque nos últimos 30 dias.")
        super().__init__("Cotações com falta de Estoque", start_date, end_date, user_name, description=description)
        

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
        df_filtered = transform_df_estoque(self.original_df, start_date=start_date, end_date=end_date, name=self.user_name)
        excel_data = self.to_excel(df_filtered)
        st.title(self.title)
        if self.user_name == 'Gerência':
            st.write("Abaixo está o relatório de estoque em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de estoque para o(a) vendedor(a) {self.user_name}:")
        st.dataframe(df_filtered, 
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
    def __init__(self, df, start_date, end_date, user_name, checkbox_90_days):
        self.original_df = df
        self.df = transform_df_inadimplencia(df, start_date=start_date, end_date=end_date, name=user_name, checkbox_90_days=False)
        total_valor = round(self.df['Valor da Parcela'].sum(), 2)
        total_valor_formatted = f"{total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        description = f"Você tem um total de {len(self.df)} notas inadimplentes, com um valor total de {total_valor_formatted} R$."
        super().__init__("Relatório de Inadimplência", start_date, end_date, user_name, description=description)
        

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
        df_transformed = transform_df_inadimplencia(self.original_df, start_date, end_date, self.user_name, checkbox_90_days)
        
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
        self.original_df = df
        self.user_name = user_name
        self.df = transform_df_contatos(df, name=user_name,selectbox_vendedor=False, selectbox_venda=False, selectbox_cotacao=False, selectbox_telemarketing=False )
        if user_name != "Gerência":
            contatos = round((len(self.original_df[(self.original_df['apelido'] == self.user_name.upper()) & (self.original_df['contactou_ou_nao'] == 'Contato feito')]))/(len(self.original_df[self.original_df['apelido'] == self.user_name.upper()])) * 100, 2)
        else:
            contatos = 'Vou ver depois'
        description = f"Você contactou {contatos}% dos parceiros este mês. "
        super().__init__("Relatório de Contatos", None, None, user_name, description=description)
        

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
            if round((len(self.original_df[(self.original_df['apelido'] == self.user_name.upper()) & (self.original_df['contactou_ou_nao'] == 'Contato feito')]))/(len(self.original_df[self.original_df['apelido'] == self.user_name.upper()])) * 100, 2) == 100:
                st.metric(label="", value="Parabéns, meta batida!")
            else:
                st.metric(label="Contatos Feitos, em %", value=f"{round((len(self.original_df[(self.original_df['apelido'] == self.user_name.upper()) & (self.original_df['contactou_ou_nao'] == 'Contato feito')]))/(len(self.original_df[self.original_df['apelido'] == self.user_name.upper()])) * 100, 2)} %")
        # Transforma o dataframe usando os filtros (se existirem)
        df_transformed = transform_df_contatos(self.original_df, self.user_name, selectbox_vendedor, selectbox_telemarketing, selectbox_cotacao, selectbox_venda)
        
        excel_data = self.to_excel(df_transformed)
        
        st.dataframe(df_transformed,
                     column_config={
                         "ult_tele": st.column_config.DateColumn(label="Último Telemarketing", format="DD/MM/YYYY"),
                         "ult_cotacao": st.column_config.DateColumn(label="Última Cotação", format="DD/MM/YYYY"),
                         "ult_venda": st.column_config.DateColumn(label="Última Venda", format="DD/MM/YYYY"),
                         "codparc": st.column_config.TextColumn(label="Cód. Parceiro"),
                         "nomeparc": st.column_config.TextColumn(label="Nome do Parceiro"),
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
        
        selectbox_vendedor = None
        
        df_transformed = transform_df_comissao(self.df, self.user_name, start_date, end_date, mes_vigente, selectbox_vendedor)
        # df_transformed['Comissão'] = df_transformed['Comissão'].str.replace('.', '').str.replace(',', '.').astype(float)
        total_valor = df_transformed['Comissão'].sum()
        total_valor_formatted = f"{total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if self.user_name == 'Gerência':
            selectbox_vendedor = self.select_box(label="Escolha um vendedor", options=self.df['apelido'].unique(), placeholder="Selecione o vendedor")
            st.write(f"Abaixo está o relatório de comissão em nível gerencial:")
        else:
            st.write(f"Abaixo está o relatório de comissão para a vendedora {self.user_name}:")
            st.write(f"No período selecionado, você tem comissões que totalizam o valor de {total_valor_formatted} R$.")
            
            
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
            file_name=f'relatorio_comissao_agregados{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

class Relatorio_Vendas_Page(BasePage):
    def __init__(self, df, user_name):
        self.original_df = df
        self.df = transform_df_vendas(df, name=user_name,selectbox_vendedor=False, selectbox_venda=False, selectbox_cotacao=False, selectbox_telemarketing=False, melhor_dia=True) 
        parceiros_hoje = len(self.df)
        description = f"Você tem {parceiros_hoje} parceiros para entrar em contato hoje."
        super().__init__("Relatório de Vendas", None, None, user_name, description=description)
        

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
        melhor_dia = self.checkbox(label="Melhor Dia para Contato", value = True)
        if self.user_name == 'Gerência':
            st.write(f"Abaixo está o relatório de vendas em nível gerencial:")

            # Filtros para o usuário "Gerência"
            selectbox_vendedor = self.select_box(label="Escolha um vendedor", options=self.df['apelido'].unique(), placeholder="Selecione o vendedor")
            selectbox_telemarketing = self.select_box(label="Telemarketing?", options=self.df['telemarketing_feito'].unique(), placeholder="Selecione se houve telemarketing")
            selectbox_cotacao = self.select_box(label="Cotou?", options=self.df['cotacao_feita'].unique(), placeholder="Selecione se houve cotação")
            selectbox_venda = self.select_box(label="Vendeu?", options=self.df['venda_feita'].unique(), placeholder="Selecione se houve venda")
        else:
            st.write(f"Abaixo está o relatório de vendas para a vendedora {self.user_name}:")
            selectbox_vendedor = None
            selectbox_telemarketing = None
            selectbox_cotacao = None
            selectbox_venda = None
           # Transforma o dataframe usando os filtros (se existirem)
        df_transformed = transform_df_vendas(self.df, self.user_name, selectbox_vendedor, selectbox_telemarketing, selectbox_cotacao, selectbox_venda, melhor_dia)
        
        excel_data = self.to_excel(df_transformed)
        
        st.dataframe(df_transformed,
                     column_config={
                         "ult_tele": st.column_config.DateColumn(label="Último Telemarketing", format="DD/MM/YYYY"),
                         "ult_cotacao": st.column_config.DateColumn(label="Última Cotação", format="DD/MM/YYYY"),
                         "ult_venda": st.column_config.DateColumn(label="Última Venda", format="DD/MM/YYYY"),
                         "qtd_compras": st.column_config.TextColumn(label="N de Compras", help = "Número de compras realizadas pelo parceiro nos últimos 6 meses"),
                         "vlr_compras": st.column_config.NumberColumn(label="Valor das Compras", help = "Valor total das compras realizadas pelo parceiro nos últimos 6 meses", format = "R$ %.0f"),
                         "vlr_gasto_mes_passado" : st.column_config.NumberColumn(label = "Valor Gasto Mês Passado", format = "R$ %.0f"),
                         "vlr_gasto_mes_atual" : st.column_config.NumberColumn(label = "Valor Gasto Mês Atual", format = "R$ %.0f"),
                         "elasticidade" : st.column_config.NumberColumn(label = "Elasticidade", format = "R$ %.0f", help = "Elasticidade de compra do parceiro"),
                         "codparc": st.column_config.TextColumn(label="Cód. Parceiro"),
                         "apelido": st.column_config.TextColumn(label="Vendedor"),
                         "nomeparc": st.column_config.TextColumn(label="Nome do Parceiro"),
                         "telemarketing_feito": st.column_config.TextColumn(label="Entrou em contato por telemarketing?"),
                         "cotacao_feita": st.column_config.TextColumn(label="Cotou esse mês?"),
                         "venda_feita": st.column_config.TextColumn(label="Vendeu esse mês?"),
                         "contactou_ou_nao": st.column_config.TextColumn(label="Entrou em contato?"),
                         "tempo_ultima_venda" : st.column_config.NumberColumn(label = "Dias desde a Última Venda"),
                         "dias_preferidos_cotar" : st.column_config.Column(label = "Dias Preferidos para Cotar"),
                         "dias_preferidos_pedido" : st.column_config.Column(label = "Dias Preferidos para Fazer Pedido"),
                         "vergalhao" : st.column_config.Column(label = "Vergalhão"),
                         "cd" : st.column_config.Column(label = "C/D"),
                         "arame" : st.column_config.Column(label = "Arame"),
                         "prego" : st.column_config.Column(label = "Prego"),
                         "estribo" : st.column_config.Column(label = "Estribo"),
                         "coluna" : st.column_config.Column(label = "Coluna"),
                         "tela_soldada" : st.column_config.Column(label = "Tela Soldada"),
                         "trelica" : st.column_config.Column(label = "Treliça"),
                         "radier" : st.column_config.Column(label = "Radier"),
                         "bba" : st.column_config.Column(label = "BBA"),
                         "cercamento" : st.column_config.Column(label = "Cercamento"),
                         "perfil" : st.column_config.Column(label = "Perfil"),
                     },
                     hide_index=True)
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name=f'relatorio_vendas{today.year}{today.month}{today.day}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
