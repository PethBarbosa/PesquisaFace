import io
import os
import threading
from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, send_file
from PdfAnalizer import consultarUsuario, criaUsuario, ConsultaImportacaoAtivos, ConsultaPdf, InsertPdfImportacao, ExcluirPdfImportacaoPdf, EncodeImage, AtualizaPath, PesquisaPath, atualizarpdf, ProcessarPdf
import datetime 
import fitz
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import Flask, jsonify, request
import requests
import bcrypt
from werkzeug.utils import secure_filename
from PIL import Image



app = Flask(__name__)
CORS(app)


# Configurando a chave secreta para a JWT. Mantenha isso seguro na produção.
app.config['JWT_SECRET_KEY'] = 'sua-chave-secreta'
jwt = JWTManager(app)


@app.route('/Usuario', methods=['POST'])
def cadastrar_usuario():
    try:
        
        users = consultarUsuario()
        # Obtemos os dados do corpo da solicitação
        data = request.get_json()
        nome_usuario = data.get('email')
        senha = data.get('password')

        if nome_usuario is None or senha is None:
            return jsonify({'error': 'Nome de usuário e senha são obrigatórios'}), 400

        print("variavel users:")
        print(users)
        
        usersList = [item for _, item in users]

        if nome_usuario in usersList:
            return jsonify({'error': 'Nome de usuário já cadastrado'}), 409

        sal = bcrypt.gensalt()

        senha_com_sal = senha.encode('utf-8') + sal

        hash_senha = bcrypt.hashpw(senha_com_sal, sal)

        usuarioId = criaUsuario(nome_usuario, hash_senha, sal)

        return jsonify({'message': 'Usuário cadastrado com sucesso', 'UserId': usuarioId}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # Responde à solicitação OPTIONS com os cabeçalhos CORS apropriados
        response = jsonify({'message': 'Success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    users = consultarUsuario() 
    usersList = [item for _, item in users]
    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)


    if username not in usersList:
        return jsonify({'message': 'Credenciais inválidas'}), 401
    else:
        id_correspondente = next((id_usuario for id_usuario, usuario in users if usuario == username), None)
        userLogin = consultarUsuario(id_correspondente)
        
        senha_com_sal = password + userLogin[0][3]
        novo_hash = bcrypt.hashpw(senha_com_sal.encode('utf-8'), userLogin[0][3].encode('utf-8'))
        
        if novo_hash.decode('utf-8') == userLogin[0][2]:
            print("Senha correta! Login bem-sucedido.")
            access_token = create_access_token(identity=username)
            # Retorna o token em JSON
            return jsonify({'access_token': access_token})
        else:
            print("Senha incorreta! Login falhou.")
            return jsonify({'error': 'Login e/ou senha incorretos'}), 500



@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/atualizapdf/<idPdf>', methods=['POST'])
@jwt_required()
def atualizapdf(idPdf):
    try:

        linkPdf = PesquisaPath(idPdf)

        if not linkPdf:
            return jsonify({'error': 'Link do PDF não encontrado'}), 404

        response = requests.get(linkPdf)

        
        if response.status_code != 200:
            return jsonify({'error': f'Falha ao baixar o PDF do link: {linkPdf}'}), 500


        nomeArquivo = ConsultaPdf(idPdf)

        if not os.path.exists('Pdfs'):
            os.makedirs('Pdfs')


        caminho_arquivo = os.path.join('Pdfs', f'{nomeArquivo}')

        with open(caminho_arquivo, 'wb') as arquivo_pdf:
            arquivo_pdf.write(response.content)

        atualizarpdf(idPdf)

        threading.Thread(target=ProcessarPdf, args=(idPdf,)).start()

        return jsonify({'message': 'Arquivo salvo, processamento em andamento ... ', 'ImportacaoId': idPdf })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def row_to_dict(row):
    """Função para converter objeto pyodbc.Row para dicionário."""
    def serialize_datetime(obj):
        """Função para serializar objetos datetime."""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return obj

    return {row.cursor_description[i][0]: serialize_datetime(value) for i, value in enumerate(row)}

def rows_to_list_of_dicts(rows):
    """Converte uma lista de objetos pyodbc.Row para uma lista de dicionários."""
    return [row_to_dict(row) for row in rows]


@app.route('/pdfimportacao', methods=['PUT'])
@cross_origin()
@jwt_required()
def atualizaPath():
    try:
        importacao_id = request.headers.get('id')
        path = request.json.get('path')
        
        app.logger.info(f'Recebido id: {importacao_id}, path: {path}')
        result = AtualizaPath(importacao_id, path)
        return jsonify({'message': 'Atualizado com sucesso !', 'Id': importacao_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/pdfimportacao/<PdfId>', methods=['DELETE'])
@cross_origin()
@jwt_required()
def excluirImportacao(PdfId):
    try:
        delete = ExcluirPdfImportacaoPdf(PdfId)
        return jsonify({'message': 'Excluido com sucesso !', 'ImportacaoId': PdfId})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 

@app.route('/pdfimportacao', methods=['POST'])
@cross_origin()
@jwt_required()
def inserirImportacao():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo PDF enviado'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Nome de arquivo inválido'}), 400

        # Salvar o arquivo localmente
        nome_arquivo = secure_filename(file.filename)
        caminho_arquivo_original = os.path.join('Pdfs', nome_arquivo)
        file.save(caminho_arquivo_original)

        IdPdfInsert = InsertPdfImportacao(nome_arquivo)

        if IdPdfInsert:
            threading.Thread(target=ProcessarPdf, args=(IdPdfInsert,)).start()
            return jsonify({'message': 'Importação de PDF bem-sucedida, faces em processamento. Aguarde ...', 'ImportacaoId': IdPdfInsert})
        else:
            return jsonify({'error': 'Erro ao inserir importação de PDF'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/list/pdfimportacao/configuracao/<PdfId>', methods=['GET'])
@cross_origin()
@jwt_required()
def obterConfiguracaoPdf(PdfId):
    try:
        resultados = ConsultaImportacaoAtivos(PdfId)

        if isinstance(resultados, list):
            resultados_list_of_dicts = rows_to_list_of_dicts(resultados)
            return jsonify(resultados_list_of_dicts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/list/pdfimportacao', methods=['GET', 'OPTIONS'])
@cross_origin()
@jwt_required()
def obterPdf():
    if request.method == 'OPTIONS':
        # Responde à solicitação OPTIONS com os cabeçalhos CORS apropriados
        response = jsonify({'message': 'Success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    try:

        resultados = ConsultaImportacaoAtivos()

        if resultados:
            resultados_list_of_dicts = rows_to_list_of_dicts(resultados)
            return jsonify(resultados_list_of_dicts), 200

        return jsonify({"Retorno:":"Não existem registros ativos"}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/imagem/<importacaoId>', methods=['POST'])
@cross_origin()
@jwt_required()
def enviarImagem(importacaoId):
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo de imagem enviado'}), 400

        file = request.files['file']
        imagem_processada = EncodeImage(file.read(), importacaoId)

        response = jsonify(imagem_processada)
        response.headers.add('Access-Control-Allow-Origin', 'https://pesquisafacebackredirect.online')

        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/download_pdf/<pdf_id>/<int:pagina>')
@cross_origin()
@jwt_required()
def download_pdf(pdf_id, pagina):
    # Obtém o nome do arquivo PDF com base no ID
    nome_arquivo = ConsultaPdf(pdf_id)
    caminho_arquivo = os.path.join('Pdfs', nome_arquivo)
    if os.path.exists(caminho_arquivo):
        with fitz.open(caminho_arquivo) as pdf_document:
            pagina_pdf = pdf_document.load_page(pagina - 1)  # A contagem de páginas começa em 0
            novo_pdf = fitz.open()
            novo_pdf.insert_pdf(pdf_document, from_page=pagina - 1, to_page=pagina - 1)
            bytes_do_novo_pdf = novo_pdf.write()
            
            return send_file(
                io.BytesIO(bytes_do_novo_pdf),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'pdf_{pdf_id}_pagina_{pagina}.pdf'
            )
    else:
        return "PDF não encontrado", 200
    

@app.route('/download_imagem/<pdf_id>/<int:pagina>')
@cross_origin()
@jwt_required()
def download_imagem(pdf_id, pagina):
    # Obtém o nome do arquivo PDF com base no ID
    nome_arquivo = ConsultaPdf(pdf_id)
    caminho_arquivo = os.path.join('Pdfs', nome_arquivo)
    if os.path.exists(caminho_arquivo):
        with fitz.open(caminho_arquivo) as pdf_document:
            pagina_pdf = pdf_document.load_page(pagina - 1)  # A contagem de páginas começa em 0
            
            # Converter a página PDF em uma imagem
            imagem = pagina_pdf.get_pixmap()
            imagem_pil = Image.frombytes("RGB", [imagem.width, imagem.height], imagem.samples)

            # Salvar a imagem em um buffer com qualidade ajustável
            imagem_buffer = io.BytesIO()
            imagem_pil.save(imagem_buffer, format='PNG', compress_level=9)  # Nível de compressão: 0 a 9
            imagem_buffer.seek(0)

            # Retorna a imagem
            return send_file(
                imagem_buffer,
                mimetype='image/png',
                as_attachment=True,
                download_name=f'imagem_{pdf_id}_pagina_{pagina}.png'
            )
    else:
        return "PDF não encontrado", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 
