FROM python:3.8-slim

# Atualize os pacotes e instale dependências
RUN apt-get update && \
    apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    libgl1-mesa-glx \
    unixodbc

# Instale o FreeTDS (driver ODBC para SQL Server)
RUN apt-get install -y freetds-bin freetds-dev tdsodbc

# Install ODBC Driver 17 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Configure o diretório de trabalho
WORKDIR /app

# Copie os arquivos do seu projeto para o contêiner
COPY . .

# Instale as dependências do seu projeto (se houver)
RUN pip install -r requirements.txt

# Exponha a porta 5000 para permitir conexões externas
EXPOSE 5000

# Comando a ser executado quando o contêiner iniciar
CMD ["python", "app.py"]
