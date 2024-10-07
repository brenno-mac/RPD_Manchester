import os
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

hoje = datetime.now()

hoje.month

inicio_mes_vigente = datetime(hoje.year, hoje.month, 1)

def format_numbers_br(df, cols):
    for col in cols:
        df[col] = df[col].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df[col] = df[col].astype(str)
    return df


def connect_bigquery():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "googlecredentials.json"
    project_id = 'manchester-ai'
    cliente = bigquery.Client()
    return cliente


def transform_df_estoque(df, start_date, end_date, name):
    # Converte as datas para o tipo datetime64
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
    
        df['data_cotada'] = pd.to_datetime(df['data_cotada'], format = '%d/%m/%Y')
    # Filtra o DataFrame pelas datas escolhidas
        df = df[(df['data_cotada'] >= start_date) & (df['data_cotada'] <= end_date)]
    
        df = df[df['pos_cotacao'] < 0] 
        # df = format_numbers_br(df = df, cols = ['valor_da_nota', 'cotado', 'estoque', 'pos_cotacao'])
        df['n_da_nota'] = df['n_da_nota'].astype(str)
        df.rename(columns={'n_da_nota':'N. da Nota', 'valor_da_nota':'Valor da Nota', 'data_cotada':'Data Cotada', 'cliente':'Cliente', 'vendedor':'Vendedor', 'empresa':'Empresa', 'produto':'Produto', 'caracteristica':'Característica', 'cotado':'Cotado', 'estoque':'Estoque', 'pos_cotacao':'Pós-Cotação'}, inplace = True)
        if name != 'Gerência':
            df = df[df['Vendedor'] == name.upper()]
            df.drop(columns = ['Vendedor'], inplace = True)
        else:
            pass
        return df
    
def transform_df_inadimplencia(df, start_date, end_date, name, checkbox_90_days):
    # Converte as datas para o tipo datetime64
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        df.drop(columns=['valor_da_nota'], inplace=True)
        df['data_de_vencimento'] = pd.to_datetime(df['data_de_vencimento'], format = '%d/%m/%Y')
    # Filtra o DataFrame pelas datas escolhidas
        df = df[(df['data_de_vencimento'] >= start_date) & (df['data_de_vencimento'] <= end_date)]
    
        df['numero_da_nota'] = df['numero_da_nota'].astype(str)
        df['codigo_parceiro'] = df['codigo_parceiro'].astype(str)
        df['dias_vencidos'] = df['dias_vencidos'].astype(int)
        df.rename(columns={'codigo_parceiro':'Código Parceiro', 'nome_parceiro':'Nome Parceiro', 'vendedor':'Vendedor', 'data_de_vencimento':'Data de Vencimento', 'numero_da_nota':'N. da Nota', 'descricao_oper':'Descrição da Operação', 'numero_parcela':'N. da Parcela', 'tipo_de_titulo':'Tipo de Título', 'dias_vencidos':'Dias Vencidos', 'valor_parcela':'Valor da Parcela', 'historico':'Histórico', 'codemp':'Empresa'}, inplace = True)
        if checkbox_90_days:
            df = df[(df['Dias Vencidos'] <= 90) & (df['Tipo de Título'] != 'INCLUIDO NO SERASA') & (df['Tipo de Título'] != 'PROTESTO')] 
        if name != 'Gerência':
            df = df[df['Vendedor'] == name.upper()]
            df.drop(columns = ['Vendedor'], inplace = True)
        else:
            pass
        return df
    
def transform_df_contatos(df, name, selectbox_vendedor, selectbox_telemarketing, selectbox_cotacao, selectbox_venda):
    df['codparc'] = df['codparc'].astype(str)
    df.rename(columns={'codparc':'Código Parceiro', 'apelido':'Vendedor', 'nomeparc':'Nome do Parceiro', 'telemarketing_feito':'Fez telemarketing?', 'cotacao_feita':'Cotou?', 'contactou_ou_nao':'Fez contato esse mês?', 'ult_tele':'Último Telemarketing', 'ult_cotacao':'Última Cotação', 'ult_venda':'Última Venda', 'venda_feita':'Vendeu?', 'tempo_ultima_venda':'Dias desde Última Venda'}, inplace = True)
    if name != 'Gerência':
        df = df[(df['Fez contato esse mês?'] == 'Não contactou') & (df['Vendedor'] == name.upper())]
        df.drop(columns = ['Vendedor', 'Cotou?', 'Fez telemarketing?', 'Fez contato esse mês?', 'Vendeu?', 'Dias desde Última Venda'], inplace = True)
    else:
        if selectbox_vendedor:
            df = df[df['Vendedor'] == selectbox_vendedor]
        if selectbox_telemarketing:
            df = df[df['Fez telemarketing?'] == selectbox_telemarketing]
        if selectbox_cotacao:
            df = df[df['Cotou?'] == selectbox_cotacao]
        if selectbox_venda:
            df = df[df['Vendeu?'] == selectbox_venda]
    return df

def transform_df_contatosagregados(df, name):
    # df['codparc'] = df['codparc'].astype(str)
    # df.rename(columns={'codparc':'Código Parceiro', 'apelido':'Vendedor', 'nomeparc':'Nome do Parceiro', 'telemarketing_feito':'Fez telemarketing?', 'cotacao_feita':'Cotou?', 'contactou_ou_nao':'Fez contato esse mês?', 'ult_tele':'Último Telemarketing', 'ult_cotacao':'Última Cotação', 'ult_venda':'Última Venda', 'venda_feita':'Vendeu?'}, inplace = True)
    # df = df[~df['tempo_ultima_venda'].isna()]
    # df = df[df['tempo_ultima_venda'] < 90]
    df_agrupado = df.groupby('apelido').agg(
        Carteira=('codparc', 'size'),
        Contatos=('contactou_ou_nao', lambda x: (x == 'Contato feito').sum()),
        Fez_telemarketing=('telemarketing_feito', lambda x: (x == 'Entrou em contato esse mês').sum()),
        Cotou=('cotacao_feita', lambda x: (x == 'Cotou esse mês').sum()),
        Vendeu=('venda_feita', lambda x: (x == 'Vendeu esse mês').sum()),
        Ultima_Venda=('tempo_ultima_venda', 'min')
        )
    df_agrupado = df_agrupado[(df_agrupado['Ultima_Venda'].notna() | df_agrupado['Ultima_Venda'] < 90) & (df_agrupado['Contatos'] != 0)]
    df_agrupado.drop(columns = ['Ultima_Venda'], inplace = True)
    df_agrupado['Faltam contatos'] = df_agrupado['Carteira'] - df_agrupado['Contatos']
    df_agrupado['Porcentagem'] = (df_agrupado['Contatos'] / df_agrupado['Carteira']) * 100
    df_agrupado = df_agrupado.reset_index()
    df_agrupado.rename(columns = {'apelido':'Vendedor', 'Fez_telemarketing':'Fez telemarketing', }, inplace = True)
    df_agrupado.sort_values(by='Porcentagem', ascending = False, inplace = True)
    return df_agrupado

def transform_df_comissao(df, name, start_date, end_date, mes_vigente):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df = df[(df['dhbaixa'] >= start_date) & (df['dhbaixa'] <= end_date)]
    
    df.rename(columns={'nufin':'N. Financeiro','numnota':'N. da Nota', 'dhbaixa':'Data da Baixa', 'dtfatur':'Data Faturada', 'dtvenc':'Data de Vencimento',  'diaatraso':'Dias Atrasado', 'parcela':'Parcela', 'codparc':'Cód. Parceiro', 'nomeparc':'Nome do Parceiro', 'vlrdesdob':'Valor do Desdobramento', 'comissao':'Comissão %', 'comiss':'Comissão', 'apelido':'Vendedor', 'codvend':'Cód. do Vendedor'}, inplace=True)
    df.drop(columns=['numnota2'], inplace=True)
    
    # df = df[df['Valor em Aberto'] == 0]
    # df['Comissão(R$)'] = df['Comissão(R$)'].apply(formatar_brasileiro)

    
    # df = format_numbers_br(df = df, cols = ['Valor do Desdobramento(R$)',  'Comissão(R$)', 'Comissão %'])
    df['N. Financeiro'] = df['N. Financeiro'].astype(str)
    df['N. da Nota'] = df['N. da Nota'].astype(str)
    df['Cód. Parceiro'] = df['Cód. Parceiro'].astype(str)
    
    if mes_vigente:
        df = df[df['Data da Baixa'] > inicio_mes_vigente]
        
    if name != 'Gerência':
            df = df[df['Vendedor'] == name.upper()]
            df.drop(columns = ['Vendedor', 'Cód. do Vendedor'], inplace = True)
    return df

