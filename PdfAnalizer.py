import io
import os
import cv2
import face_recognition
from PIL import Image
import numpy as np
from Functions import geraImagemTemporaria, recognize_faces
import odbc
import fitz 


def consultarUsuario(idUsuario=None):
    result = odbc.ConsultaUsuario(idUsuario)
    return result

def criaUsuario(user, password, sal):
    usuarioId = odbc.createUser(user, password, sal)
    return usuarioId

def atualizarpdf(idPdf, pdfBytes):
    odbc.atualizaPdf(idPdf, pdfBytes)
    return


def PesquisaPath(id):
    result = odbc.PesquisaPath(id)
    return result


def ExcluirPdfImportacaoPdf(pdfId):
    odbc.ExcluirImportacaoPdf(pdfId)
    odbc.DeleteFaces(pdfId)
    return

def InsertPdfImportacao(nome_arquivo):
    IdPdf = odbc.InsertPdfImportacao(nome_arquivo)
    ProcessarPdf(IdPdf)

    return IdPdf

def ConsultaImportacaoAtivos(id=None):
    Consulta = odbc.ConsultaImportacaoPdfAtivos(id)

    return Consulta

def AtualizaPath(id, path):
    result = odbc.AtualizaPath(id, path)
    return result

def ConsultaPdf(pdfId):
    
    NomeArquivo = odbc.ConsultaPdf(pdfId)
    
    return NomeArquivo

def ProcessarPdf(pdfId):

    try:
        faces_on_all_pages = []

        NomeArquivo = ConsultaPdf(pdfId)
        
        caminho_arquivo = os.path.join('pdfs', NomeArquivo)

        with open(caminho_arquivo, 'rb') as arquivo_pdf:
            blob_Pdfdata = arquivo_pdf.read()

        # Carregar o PDF em memória apenas para leitura dos blobs
        pdf = fitz.open(stream=blob_Pdfdata, filetype="pdf")
        
        for page_number in range(1, pdf.page_count - 1):
            
            try:
                tempImagem = geraImagemTemporaria(page_number, pdf)
                faces_on_page = recognize_faces(tempImagem, page_number)
                faces_on_all_pages.append(faces_on_page)
            
            except Exception as e:
                print(f"Erro ao processar página {page_number}: {e}")
                pass
            
        pdf.close()
        odbc.DeleteFaces(pdfId)
        odbc.InsertFaces(pdfId, faces_on_all_pages)
        
        print(f"PDF processado !")

    except Exception as e:
        print(f"Processar PDF:  {e}")
        pass

    return

def EncodeImage(image, importacaoId):

    try:
        # Convertendo a imagem do PIL para um array NumPy
        image_array = np.array(Image.open(io.BytesIO(image)))

        # Localizando as faces na imagem
        face_locations = face_recognition.face_locations(image_array)

        if face_locations:
            # Obtendo os encodings das faces
            face_encodings = face_recognition.face_encodings(image_array, face_locations)

            if face_encodings:
                list_BytesEncode_faces, list_NumeroPagina = zip(*odbc.SelectAllFaces(importacaoId))

                # Comparando as faces
                compare_faces_result = face_recognition.compare_faces(list_BytesEncode_faces, face_encodings[0], tolerance=0.4)

        resultados_associados = [numero_pagina for corresponde, numero_pagina in zip(compare_faces_result, list_NumeroPagina) if corresponde]

        if resultados_associados:
            return {'success': True, 'message': 'Face processada com sucesso',  'paginas_associadas': resultados_associados}
        else:
            return {'success': False, 'message': 'Nenhuma correspondência encontrada', 'paginas_associadas': []}
    except Exception as e:
        return {'success': False, 'message': f'Erro ao processar imagem: {str(e)}'}, 500
    
####################################################################
def testeImagem(caminho_imagem):
    # Abre a imagem local usando o OpenCV
    imagem = cv2.imread(caminho_imagem)

    # Converte a imagem para o formato RGB
    imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)

    # Converte a imagem para uma matriz NumPy
    image_array = np.array(imagem_rgb)

    # Simula a criação de um pixmap usando samples
    height, width, _ = image_array.shape
    samples = image_array.tobytes()

    # Cria uma imagem PIL usando samples (simulando o comportamento do PDF)
    imagem_pil = Image.frombytes("RGB", (width, height), samples)

    # Converte a imagem PIL para uma matriz NumPy
    imagem_processada = np.array(imagem_pil)

    return imagem_processada

    

# # pdf_path = 'C:\\Repositorios\\anything\\PesquisaFace\\PdfExtracao.pdf'

# Caminho da imagem local
# caminho_imagem = 'C:\\Users\\patrick.barbosa\\Pictures\\iaanalise\\analise.jpeg'

# imagem_array = testeImagem(caminho_imagem)

# facePdf = recognize_faces(imagem_array, 1)

# print(facePdf)

# #############

# pdf_document = fitz.open('C:\\Users\\patrick.barbosa\\Pictures\\iaanalise\\imagemTest.pdf')

# imagemTemp = geraImagemTemporaria(pdf_document)
