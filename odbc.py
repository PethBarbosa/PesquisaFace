from datetime import datetime, timezone
import pyodbc
import pickle
import os
import uuid
from dotenv import load_dotenv
import pytz

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

server = 'database-pesquisaface.czyg2wioga62.us-east-2.rds.amazonaws.com'
database = 'PesquisaFace'
username = 'adminPath'
password = '!PesquisaFace1232016!'
conn_str = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}'


def get_local_time():

    tz = pytz.timezone('America/Sao_Paulo')
    now_utc = datetime.utcnow()
    now_local = now_utc.astimezone(tz)
    formatted_time = now_local.strftime('%Y-%m-%d %H:%M') 

    return str(formatted_time)

def ConsultaUsuario(UserId=None):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()

        if UserId is not None:
            # Se UserId fornecido, busca Id, usuário e PassSal
            query = f"""
                SELECT Id, Usuario, Pass, PassSal
                FROM Usuarios 
                WHERE Ativo = 1 AND Id = '{UserId}'
            """
        else:
            # Se UserId não fornecido, busca todos Id e usuários
            query = """
                SELECT Id, Usuario
                FROM Usuarios 
                WHERE Ativo = 1
            """

        cursor.execute(query)
        result = cursor.fetchall()

        if result:
            return result
        else:
            print(f"Nenhum usuário encontrado")
            return None

    except Exception as e:
        print(f"Erro ao consultar Usuario: {e}")
        return None

    finally:
        if 'connection' in locals():
            connection.close()

def createUser(user, password, sal):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        id = str(uuid.uuid4())
        data_alteracao = get_local_time()

        cursor.execute("""
            INSERT INTO Usuarios (Id, Usuario, Pass, DataAlteracao, Ativo, PassSal)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (id, user, password,data_alteracao, sal)
        )

        # Commit para salvar as alterações
        connection.commit()

        print(f"Registro inserido com sucesso na tabela Usuario.")

        return id
    
    except Exception as e:
        print(f"Erro ao inserir registro na tabela Usuario: {e}")

    finally:
        # Certifique-se de fechar a conexão quando terminar
        if 'connection' in locals():
            connection.close()


def atualizaDataAlteracaoPdf(pdfImportacaoId):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        data_alteracao = get_local_time()

        print("Conexão bem-sucedida!")

        # Atualizar o campo Ativo nas faces relacionadas ao pdfImportacaoId
        cursor.execute("""
            UPDATE PdfImportacao
            SET DataAlteracao = ?
            WHERE Id = ?
            """,
            (data_alteracao, pdfImportacaoId)
        )

        connection.commit()

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

    finally:
        if 'connection' in locals():
            connection.close()

def InsertPdfImportacao(nome_arquivo):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        idPdfImportacao = uuid.uuid4()
        data_alteracao = get_local_time()

        cursor.execute("""
            INSERT INTO PdfImportacao (Id, Codigo, DataAlteracao, Ativo, NomeArquivo)
            VALUES (?, NULL, ?, 1, ?)
            """,
            (idPdfImportacao, data_alteracao, nome_arquivo)
        )

        # Commit para salvar as alterações
        connection.commit()

        print(f"Registro inserido com sucesso na tabela PdfImportacao.")

        return idPdfImportacao
    
    except Exception as e:
        print(f"Erro ao inserir registro na tabela PdfImportacao: {e}")

    finally:
        # Certifique-se de fechar a conexão quando terminar
        if 'connection' in locals():
            connection.close()


def ConsultaPdf(pdfId):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
    
        cursor.execute("""
            SELECT NomeArquivo
            FROM PdfImportacao
            WHERE  Id = ?
            """,
            (pdfId,)
        )

        result = cursor.fetchone()

        if result:

            return result.NomeArquivo
        else:
            print(f"Nenhum PDF encontrado com o ID {pdfId}")
            return None

    except Exception as e:
        print(f"Erro ao consultar PDF: {e}")
        return None

    finally:

        if 'connection' in locals():
            connection.close()



def InsertFaces(pdfImportacaoId, faces_on_all_pages):

    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        data_alteracao = get_local_time()

        print("Conexão bem-sucedida!")
        faces_on_all_pages_cleaned = [faces for faces in faces_on_all_pages if any(faces)]

        for faces_on_page in enumerate(faces_on_all_pages_cleaned):
            for face in faces_on_page[1]:

                cursor.execute("""
                    INSERT INTO Faces (Codigo, Encode, NumeroPagina, Localizacao, DataAlteracao, Ativo, pdfImportacaoId)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                    """,
                    (str(uuid.uuid4()), face['encode'], face['numero_pagina'], str(face['localizacao']), data_alteracao, pdfImportacaoId)
                )

        connection.commit()


    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

    finally:

        if 'connection' in locals():
            connection.close()

def DeleteFaces(pdfImportacaoId):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()

        print("Conexão bem-sucedida!")

        # Atualizar o campo Ativo nas faces relacionadas ao pdfImportacaoId
        cursor.execute("""
            UPDATE Faces
            SET Ativo = ?
            WHERE pdfImportacaoId = ?
            """,
            (False, pdfImportacaoId)
        )

        connection.commit()

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

    finally:
        if 'connection' in locals():
            connection.close()


def PesquisaPath(IdImportacao):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT PathPdf 
            FROM PdfImportacao
            WHERE Id = ?
            """,
            (IdImportacao)
        )

        result = cursor.fetchone()

        if result:

            return result.PathPdf
        else:
            print(f"Nenhum Path encontrado com o ID {IdImportacao}")
            return None

    except Exception as e:
        print(f"Erro ao consultar PDF: {e}")
        return None

    finally:

        if 'connection' in locals():
            connection.close()

def AtualizaPath(IdImportacao, path):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE PdfImportacao
            SET PathPdf = ?
            WHERE Id = ?
            """,
            (path, IdImportacao)
        )

        connection.commit()

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

    finally:
        if 'connection' in locals():
            connection.close()


def ConsultaImportacaoPdfAtivos(id=None):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()

        query = """
            SELECT Id, Codigo, DataAlteracao, NomeArquivo, PathPdf
            FROM PdfImportacao 
            WHERE Ativo = 1
        """

        if id is not None:
            query += f" AND Id = {id}"

        cursor.execute(query)

        result = cursor.fetchall()

        if result:
            return result
        else:
            print(f"Nenhum PDF encontrado com o ID {id}")
            return None

    except Exception as e:
        print(f"Erro ao consultar PDF: {e}")
        return None

    finally:
        if 'connection' in locals():
            connection.close()

def ExcluirImportacaoPdf(pdfId):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        print("Conexão bem-sucedida!")

        cursor.execute("""
            UPDATE PdfImportacao
            SET Ativo = 0
            WHERE Ativo = 1 and Id = ?
            """,
            (pdfId)
        )
        connection.commit()

        return

    except Exception as e:
        print(f"Erro ao Excluir PDF: {e}")
        return None

    finally:

        if 'connection' in locals():
            connection.close()


def SelectAllFaces(importacaoId):
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        face_encoding_recuperado = []

        cursor.execute("""
            SELECT encode, NumeroPagina
            FROM Faces
            WHERE Ativo = 1 and pdfImportacaoId = ?
            """,
            (importacaoId)
        )

        result = cursor.fetchall()

        for row in result:
            # Suponha que 'face_encoding' seja o nome da coluna que armazena os bytes do código da face
            bytes_do_banco = row.encode 

            # Desserialize os bytes para obter o código da face original
            face_encoding_recuperado.append((pickle.loads(bytes_do_banco), row.NumeroPagina))

        if face_encoding_recuperado:

            return face_encoding_recuperado
        
        else:
            print(f"Nenhuma face encontrada")
            return None

    except Exception as e:
        print(f"Erro ao consultar face: {e}")
        return None

    finally:

        if 'connection' in locals():
            connection.close()
