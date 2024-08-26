import os
from google.cloud import bigquery
import pandas as pd

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
        df = format_numbers_br(df = df, cols = ['valor_da_nota', 'cotado', 'estoque', 'pos_cotacao'])
        df['n_da_nota'] = df['n_da_nota'].astype(str)
        df.rename(columns={'n_da_nota':'N. da Nota', 'valor_da_nota':'Valor da Nota(R$)', 'data_cotada':'Data Cotada', 'cliente':'Cliente', 'vendedor':'Vendedor', 'empresa':'Empresa', 'produto':'Produto', 'caracteristica':'Característica', 'cotado':'Cotado', 'estoque':'Estoque', 'pos_cotacao':'Pós-Cotação'}, inplace = True)
        if name != 'Gerência':
            df = df[df['Vendedor'] == name.upper()]
            df.drop(columns = ['Vendedor'], inplace = True)
        else:
            pass
        return df
    
    
    
def transform_df_inadimplencia(df, start_date, end_date, name):
    # Converte as datas para o tipo datetime64
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
    
        df['data_de_vencimento'] = pd.to_datetime(df['data_de_vencimento'], format = '%d/%m/%Y')
    # Filtra o DataFrame pelas datas escolhidas
        df = df[(df['data_de_vencimento'] >= start_date) & (df['data_de_vencimento'] <= end_date)]
    
        df = format_numbers_br(df = df, cols = ['valor_da_nota', 'valor_parcela'])
        df['numero_da_nota'] = df['numero_da_nota'].astype(str)
        df['codigo_parceiro'] = df['codigo_parceiro'].astype(str)
        df['dias_vencidos'] = df['dias_vencidos'].astype(int)
        df.rename(columns={'codigo_parceiro':'Código Parceiro', 'nome_parceiro':'Nome Parceiro', 'vendedor':'Vendedor', 'data_de_vencimento':'Data de Vencimento', 'numero_da_nota':'N. da Nota', 'valor_da_nota':'Valor da Nota(R$)', 'descricao_oper':'Descrição da Operação', 'numero_parcela':'N. da Parcela', 'tipo_de_titulo':'Tipo de Título', 'dias_vencidos':'Dias Vencidos', 'valor_parcela':'Valor da Parcela(R$)'}, inplace = True)
        df.drop(columns=['Valor da Nota(R$)'], inplace=True)
        if name != 'Gerência':
            df = df[df['Vendedor'] == name.upper()]
            df.drop(columns = ['Vendedor'], inplace = True)
        else:
            pass
        return df
    
def transform_df_contatos(df, name, selectbox_vendedor, selectbox_telemarketing, selectbox_cotacao, selectbox_venda):
    df['codparc'] = df['codparc'].astype(str)
    df.rename(columns={'codparc':'Código Parceiro', 'apelido':'Vendedor', 'nomeparc':'Nome do Parceiro', 'telemarketing_feito':'Fez telemarketing?', 'cotacao_feita':'Cotou?', 'contactou_ou_nao':'Fez contato esse mês?', 'ult_tele':'Último Telemarketing', 'ult_cotacao':'Última Cotação', 'ult_venda':'Última Venda', 'venda_feita':'Vendeu?'}, inplace = True)
    if name != 'Gerência':
        df = df[(df['Fez contato esse mês?'] == 'Não contactou') & (df['Vendedor'] == name.upper())]
        df.drop(columns = ['Vendedor', 'Cotou?', 'Fez telemarketing?', 'Fez contato esse mês?', 'Vendeu?'], inplace = True)
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
