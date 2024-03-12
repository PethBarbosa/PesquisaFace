
# Use uma imagem base do Python
#FROM python:3.10-slim

FROM python:3.8-slim

RUN apt-get update && \
apt-get upgrade -y

RUN apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick
RUN apt-get install -y --fix-missing pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*


# Install DLIB
RUN mkdir -p /root/dlib
RUN git clone -b 'v19.24' --single-branch https://github.com/davisking/dlib.git /root/dlib/
RUN cd /root/dlib/ && \
    python3 setup.py install


# Install Flask
RUN cd ~ && \
    pip3 install flask flask-cors


# Instale o OpenCV
RUN apt-get install -y libgl1-mesa-glx

# Instale outras dependências do sistema, se necessário
RUN apt-get install -y unixodbc

# Instale o FreeTDS (driver ODBC para SQL Server)
RUN apt-get update && \
    apt-get install -y freetds-bin freetds-dev tdsodbc

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