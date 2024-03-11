import face_recognition
from PIL import Image
import pickle
import uuid
import json
import numpy as np 


def geraImagemTemporaria(page_number, pdf):
    pdf_page = pdf.load_page(page_number - 1)
    pix = pdf_page.get_pixmap()
    imagePIL = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    image = np.array(imagePIL)
    return image

# RECONHECE TODAS AS FACES DO PDF
def recognize_faces(image, page_number):

    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    faces_list = []
    
    if face_locations:
        print(f"Encontrado(s) {len(face_locations)} rosto(s) na imagem da página {page_number}.")

        for i, face_location in enumerate(face_locations):

            top, right, bottom, left = face_location
            new_guid = uuid.uuid4()
            blobCordenadas = pickle.dumps(face_encodings[i].tolist())

            face_object = {
                "codigo": str(new_guid),
                "encode": blobCordenadas,
                "numero_pagina": page_number,
                "localizacao": json.dumps({"topo": top, "direita": right, "baixo": bottom, "esquerda": left}),              
            }

            faces_list.append(face_object)

            print(f"Rosto {i + 1}: Código: {face_object['codigo']}, Localização: {face_object['localizacao']}")

            # Desenhar caixas ao redor dos rostos na imagem
            #pil_image = Image.fromarray(image)
            #draw = ImageDraw.Draw(pil_image)
            #draw.rectangle([left, top, right, bottom], outline="red", width=2)

        #pil_image.show()
    else:
        print(f"Nenhum rosto encontrado na imagem da página {page_number}.")

    return faces_list