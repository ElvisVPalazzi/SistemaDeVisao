import cv2
import numpy as np
import math
import requests
from datetime import datetime
from time import sleep
from time import time
from picamera import PiCamera
from picamera.array import PiRGBArray

backgroundSubtrator = cv2.createBackgroundSubtractorMOG2(history=30000, varThreshold=50, detectShadows=True) #Cria um objeto do tipo backgroundSubtractor

camera = PiCamera()		# Declaração do objeto PiCamera
camera.resolution = (640, 480)	# Definição da resolução da câmera                
camera.iso = 800		# Definição do ISO da câmera                
camera.framerate = 5	# Definição da taxa de quadros por segundo	
           
sleep(2)			# Aguardar a inicializaçao da camera

# Trecho para fixar os valores da configuração obtidos durante a inicialização
camera.shutter_speed = camera.exposure_speed
camera.exposure_mode = 'off'
g = camera.awb_gains
camera.awb_mode = 'off'
camera.awb_gains = g

capture = PiRGBArray(camera, size=(640, 480)) # Cria um objeto para processamento dos frames captados
hora = datetime.now()			# Atribui a hora atual a variável hora
horamensagem = datetime.min	# Atribui a hora mínima a variável horamensagem
dados_historico = []	# Cria uma lista vazia para armazenar os dados do histórico

linhasuperiorxinicio = 0	# Coordenada X do ponto inicial da linha superior
linhasuperiorxfim = 1280	# Coordenada X do ponto final da linha superior
linhasuperioryinicio = 190	# Coordenada Y do ponto inicial da linha superior
linhasuperioryfim = 190		# Coordenada Y do ponto final da linha superior
linhainferiorxinicio = 0	# Coordenada X do ponto inicial da linha inferior
linhainferiorxfim = 1280	# Coordenada X do ponto final da linha inferior
linhainferioryinicio = 270	# Coordenada Y do ponto inicial da linha inferior
linhainferioryfim = 270		# Coordenada Y do ponto final da linha inferior
margemsuperior = 190		# Definição da largura em pixels da margem superior
margeminferior = 190		# Definição da largura em pixels da margem inferior

areaLimiar = 9000	# Definição da área mínima do objeto para contabilização
direcao = ''	# Variável para armazenar a direção do objeto atual
contadorTotal = 0	# Variável para número total de pessoas contabilizadas
contadorEntrando = 0	# Variável para número de entrada de pessoas
contadorSaindo = 0	# Variável para número de saída de pessoas
id_objeto = 0	# Variável para identificador único dos objetos
objetos = [[0, 0, '', 0, 0]]    # Array contendo as informações do objeto
centroidx = 0	# Coordenada X do centróide do objeto atual
centroidy = 0	# Coordenada Y do centróide do objeto atual
centroidx_anterior = 0	# Coordenada X do centróide do objeto anterior
centroidy_anterior = 0	# Coordenada Y do centróide do objeto anterior

tempo_frame_atual = 0	#  Variável para armazenar o tempo atual do frame
tempo_frame_anterior = 0	#  Variável para armazenar o tempo anterior do frame

gravacao = cv2.VideoWriter('NomeeLocalDoVideo.mp4', cv2.VideoWriter_fourcc(*'MJPG'), 5, (640, 480))  # Cria um objeto do tipo VideoWriter para gravar o vídeo

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2,2)) # Cria um kernel

for image in camera.capture_continuous(capture, format="bgr", use_video_port=True):       # Loop For contendo a função que captura os frames da câmera    
    tempo_frame_anterior = tempo_frame_atual   
    tempo_frame_atual = time()
    fps_calculado = 1/(tempo_frame_atual - tempo_frame_anterior)
    print(fps_calculado)        # Exibe no terminal a taxa de quadros
    
    hora = datetime.now()
    frames = image.array

    mask = backgroundSubtrator.apply(frames) # Aplica o backgroundSubtractor no frame captado

    _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY) # Aplica um threshold na mascara
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=3) # Aplica um filtro morfologico na mascara

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)     # Função para encontrar os contornos 

    if not contours:
        id_objeto = 0
        objetos = [[0, 0, '', 0, 0]]

    cv2.line(frames, (linhasuperiorxinicio, linhasuperioryinicio), (linhasuperiorxfim, linhasuperioryfim), (255, 0, 0), 2) # Desenha a linha azul
    cv2.line(frames, (linhainferiorxinicio, linhainferioryinicio), (linhainferiorxfim, linhainferioryfim), (0, 0, 255), 2) # Desenha a linha vermelha

    cv2.rectangle(frames, (200, 5), (0, 50), (255, 255, 255), -1) # Desenha a caixa
    cv2.putText(frames, 'Entrada: ' + str(contadorEntrando), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) # Desenha a linha azul
    cv2.rectangle(frames, (200, 55), (0, 100), (255, 255, 255), -1) # Desenha a linha azul
    cv2.putText(frames, 'Saida: ' + str(contadorSaindo), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) # Desenha a linha azul 
    cv2.rectangle(frames, (200, 105), (0, 150), (255, 255, 255), -1) # Desenha a linha azul
    cv2.putText(frames, 'Total: ' + str(contadorTotal), (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA) # Desenha a linha azul

    for cnt in contours: # Loop for para percorrer os contornos encontrados
        area = cv2.contourArea(cnt) # Calcula a área do contorno
        if area > areaLimiar: # Verifica se a área do contorno em questão é maior que o limiar definido
            x, y, w, h = cv2.boundingRect(cnt)	# Obtém as coordenadas ‘x’ e ‘y’ do ponto superior esquerdo, a largura ‘w’ e altura ‘h’ do retângulo que envolve o contorno

            centroidx = int(x + w / 2)  # Calcula a coordenada X do centroide do retângulo
            centroidy = int(y + h / 2)  # Calcula a coordenada Y do centroide do retângulo

            if math.hypot(centroidx - centroidx_anterior, centroidy - centroidy_anterior) > 180: 
                objetos.append([id_objeto, 0, '', centroidx, centroidy])
                id_objeto = id_objeto + 1

            else:
                objetos[id_objeto - 1] = [id_objeto - 1, objetos[id_objeto - 1][1], objetos[id_objeto - 1][2], centroidx, centroidy, objetos[id_objeto - 1]]

            centroidx_anterior = centroidx
            centroidy_anterior = centroidy

            cv2.rectangle(frames, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.circle(frames, (centroidx, centroidy), 0, (0, 255, 0), -1)

        if centroidy > linhasuperioryinicio-margemsuperior and centroidy < linhasuperioryinicio and objetos[id_objeto - 1][2] == '': # Verifica se o centroide se localiza na região definida pela linha superior e a margemsuperior
            objetos[id_objeto - 1][2] = 'Entrada'	# Define que o objeto está entrando no local
            
        if centroidy > linhainferioryinicio and centroidy < linhainferioryinicio+margeminferior and objetos[id_objeto - 1][2] == '': # Verifica se o centroide se localiza na região definida pela linha inferior e a margem inferior
            objetos[id_objeto - 1][2] = 'Saida'	# Define que o objeto está saindo no local

        if (centroidy > linhasuperioryinicio-margemsuperior and centroidy < linhasuperioryfim and objetos[id_objeto - 1][2] == 'Saida') or (centroidy > linhainferioryinicio and centroidy < linhainferioryfim+margeminferior and objetos[id_objeto - 1][2] == 'Entrada'): # Verifica se um objeto já registrado como “Entrada” ou “Saida” cruzou sua segunda linha
            if objetos[id_objeto - 1][1] == 0:  # Verifica se o objeto já foi contabilizado
                
                cv2.rectangle(frames, (x, y), (x + w, y + h), (0, 0, 255), 2)
                objetos[id_objeto - 1][1] = 1	# Marca o objeto como contado
                contadorTotal = contadorTotal + 1	# Adiciona 1 ao total
                hora_captura = datetime.now()	# Obtém-se a hora e data da detecção
                
                if objetos[id_objeto - 1][2] == 'Entrada':
                    contadorEntrando = contadorEntrando + 1	# Adiciona 1 ao contador de entrada
                    dados_historico.insert(0, [hora_captura.strftime("%Y%m%d"), hora_captura.strftime('%H%M%S'), contadorEntrando, contadorSaindo, contadorTotal, 1])		# Na variável dados_historico registra-se o dia e hora da captura e as contagens atuais

                elif objetos[id_objeto - 1][2] == 'Saida':
                    contadorSaindo = contadorSaindo + 1	# Adiciona 1 ao contador de saida
                    dados_historico.insert(0, [hora_captura.strftime("%Y%m%d"), hora_captura.strftime('%H%M%S'), contadorEntrando, contadorSaindo, contadorTotal, 0])        

    if (hora - horamensagem).seconds > 20:	# Verifica se passaram 20 segundos desde o envio da última mensagem         
        
        try:
            ultimo_dado = dados_historico.pop()       # Variável ultimo_dado recebe a última linha do array dados_historico
            url = 'https://api.thingspeak.com/update?api_key=YD6SRZW89IXA4WB3&field1=' + str(ultimo_dado[0]) + '&field2=' + str(ultimo_dado[1]) + '&field3=' + str(ultimo_dado[2]) + '&field4=' + str(ultimo_dado[3]) + '&field5=' + str(ultimo_dado[4]) + '&field6=' + str(ultimo_dado[5])			# Variável contendo a url para o envio das informações para a nuvem
            msg = requests.post(url)	# Função para envio da mensagem

            if msg.status_code == 200: # Verifica se a mensagem foi enviada com sucesso
                print('Mensagem enviada com sucesso')
                horamensagem = datetime.now()
            else:
                print('Erro ao enviar mensagem')
          
        except IndexError:
            pass

    gravacao.write(frames)		# Função para gravar as imagens em arquivo de vídeo

    cv2.imshow('frame', frames)	# Função para exibir em tempo real os frames processados
    if cv2.waitKey(1) == 27:	# Verifica se a tecla “ESC” foi pressionada
        break

    capture.truncate(0)
    
gravacao.release()      	# Função para encerrar a gravação
cv2.destroyAllWindows()	# Função para fechar as janelas
