# Usar uma imagem base do Python
FROM python:3.10

# Configurar o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar os arquivos do seu aplicativo para o diretório de trabalho do contêiner
COPY . /app

# Instalar as dependências necessárias
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta usada pelo Streamlit
EXPOSE 8501

# Comando para rodar o aplicativo Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]










