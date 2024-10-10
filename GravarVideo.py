import time
import os
from datetime import datetime, timedelta
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
import subprocess

# Inicializa a câmera
picam2 = Picamera2()

# Configurações de vídeo com otimização de qualidade e tamanho de arquivo
video_config = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "XBGR8888"},  # Reduzimos para HD (720p) e definimos o formato
    lores={"size": (640, 480)},  # Resolução de visualização em miniatura (opcional)
    display="main"
)

# Configura a taxa de quadros após criar a configuração de vídeo
picam2.configure(video_config)
picam2.set_controls({"FrameRate": 15})  # Define o framerate para 15 FPS

# Diretório para salvar os vídeos
output_dir = "videos"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Função para converter H264 para MP4 usando FFmpeg
def converter_h264_para_mp4(h264_file, mp4_file):
    comando_ffmpeg = ["ffmpeg", "-i", h264_file, "-c", "copy", mp4_file]
    try:
        subprocess.run(comando_ffmpeg, check=True)
        print(f"Vídeo convertido para MP4: {mp4_file}")
        # Deleta o arquivo H264 após conversão para economizar espaço
        os.remove(h264_file)
        print(f"Arquivo temporário {h264_file} deletado.")
    except subprocess.CalledProcessError as e:
        print(f"Erro na conversão de {h264_file} para MP4: {e}")

# Função para gravar vídeos de 2 horas
def gravar_video():
    picam2.start()

    # Intervalo de 2 horas para dividir os vídeos
    intervalo = timedelta(hours=2)
    count = 0

    # Hora atual
    agora = datetime.now()

    # Define o horário de término do dia (17:40)
    fim_gravacao = agora.replace(hour=17, minute=40, second=0, microsecond=0)

    # Grava enquanto o horário atual for menor que 17:40
    while agora < fim_gravacao:
        # Nome do arquivo de vídeo com o contador (em H264)
        h264_filename = os.path.join(output_dir, f"video_parte_{count}.h264")
        mp4_filename = os.path.join(output_dir, f"video_parte_{count}.mp4")  # Nome do arquivo final em MP4

        # Ajuste de bitrate para reduzir o tamanho do arquivo (10 Mbps em vez de 15 Mbps)
        encoder = H264Encoder(bitrate=1000000)  # Ajuste o bitrate conforme necessário
        
        # Configuração de arquivo de saída
        output = FileOutput(h264_filename)
        
        # Inicia a gravação com as novas configurações
        print(f"Iniciando gravação: {h264_filename} com qualidade otimizada")
        picam2.start_recording(encoder, output)

        # Grava por 2 horas ou até o horário de término (se for menos de 2 horas)
        tempo_final = min(agora + intervalo, fim_gravacao)
        while datetime.now() < tempo_final:
            time.sleep(1)

        # Para a gravação e salva o arquivo
        picam2.stop_recording()
        print(f"Gravação finalizada: {h264_filename}")

        # Converte o arquivo H264 para MP4 automaticamente após gravação
        converter_h264_para_mp4(h264_filename, mp4_filename)

        # Atualiza o tempo atual
        agora = datetime.now()
        count += 1

    picam2.stop()

# Função principal para controlar o loop
def loop_gravacao_diaria():
    while True:
        agora = datetime.now()

        # Define os horários de início (5:20) e término (17:40)
        inicio_gravacao = agora.replace(hour=5, minute=20, second=0, microsecond=0)
        fim_gravacao = agora.replace(hour=17, minute=40, second=0, microsecond=0)

        # Se o horário atual estiver entre 5:20 e 17:40, começa a gravar
        if inicio_gravacao <= agora < fim_gravacao:
            print(f"Iniciando gravação diária às {inicio_gravacao}")
            gravar_video()
        else:
            # Se estiver fora do intervalo, espera até o próximo dia às 5:20
            if agora >= fim_gravacao:
                # Aguarda até o próximo dia às 5:20
                proximo_inicio = (inicio_gravacao + timedelta(days=1)).replace(hour=5, minute=20)
            else:
                # Se ainda não for 5:20, aguarda até o mesmo dia às 5:20
                proximo_inicio = inicio_gravacao

            # Calcula quanto tempo esperar
            tempo_espera = (proximo_inicio - agora).total_seconds()
            print(f"Aguardando até o próximo início às {proximo_inicio}, tempo de espera: {tempo_espera / 3600:.2f} horas.")
            time.sleep(tempo_espera)

# Inicia o loop de gravação diária
loop_gravacao_diaria()

