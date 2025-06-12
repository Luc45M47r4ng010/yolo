from ultralytics import YOLO
import cv2, easyocr, os, csv
from datetime import datetime
import numpy as np

# Força o modelo a rodar na GPU
model = YOLO("modelos/license_plate_detector.pt").to("cuda")

# EasyOCR também usa GPU se disponível
reader = easyocr.Reader(['en'], gpu=True)

os.makedirs("resultados", exist_ok=True)

def detectar_placa_e_ocr(input_data, is_video_frame=False):
    """
    Processa imagem ou frame de vídeo para detectar placas e realizar OCR
    
    Args:
        input_data: caminho da imagem ou frame numpy array
        is_video_frame: True se input_data for um frame de vídeo
    
    Returns:
        tuple: (imagem com resultados, lista de placas detectadas)
    """
    if is_video_frame:
        imagem = input_data
    else:
        imagem = cv2.imread(input_data)
        if imagem is None:
            raise ValueError(f"Não foi possível carregar a imagem: {input_data}")

    results = model(imagem, conf=0.5, imgsz=640)
    placas = []

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if (x2-x1) > 80 and (y2-y1) > 25:  # Filtro para evitar detecções muito pequenas
                cropped = imagem[y1:y2, x1:x2]
                
                # Pré-processamento para melhorar o OCR
                gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                ocr = reader.readtext(thresh)
                if ocr:
                    # Pega o texto com maior confiança
                    ocr.sort(key=lambda x: x[2], reverse=True)
                    placa = ocr[0][1].upper().replace(" ", "")
                    
                    # Filtro básico para formatos comuns de placas (BR e Mercosul)
                    if len(placa) >= 6 and any(c.isalpha() for c in placa) and any(c.isdigit() for c in placa):
                        placas.append((placa, (x1, y1, x2, y2)))
                        cv2.rectangle(imagem, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(imagem, placa, (x1, y1-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    if not is_video_frame:
        caminho = f"resultados/resultado_{os.path.basename(input_data)}"
        cv2.imwrite(caminho, imagem)

        with open("historico.csv", "a", newline="") as f:
            writer = csv.writer(f)
            for placa, _ in placas:
                writer.writerow([placa, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    return imagem, placas

def buscar_no_historico(termo_busca):
    """Busca placas no histórico pelo termo informado"""
    resultados = []
    if not os.path.exists("historico.csv"):
        return resultados
    
    with open("historico.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 1 and termo_busca.lower() in row[0].lower():
                resultados.append(row)
    
    return resultados