import os
import time
import sys
from google import genai
from google.genai import types

# 1. Aponta para o arquivo JSON de credenciais
# ATENÇÃO: Lembre-se de baixar a chave no painel do Google Cloud e colocar neste caminho
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/vando/projects/vtx/vtx.json"

# 2. Inicializa o cliente na Vertex AI usando o projeto e localização
client = genai.Client(
    vertexai=True,
    project="somnacity-493113",
    location="us-central1",
)

# Caminho para o arquivo de texto com o prompt e tema
caminho_prompt = "prompt.txt"

# Lê o tema, caminho da imagem e prompt do arquivo de texto
# Primeira linha = tema
# Segunda linha = caminho da imagem (ou "none" para não usar imagem)
# Resto das linhas = prompt do vídeo
with open(caminho_prompt, "r", encoding="utf-8") as f:
    linhas = f.read().splitlines()
    tema = linhas[0].strip()
    caminho_imagem_lido = linhas[1].strip().lower()
    prompt_texto = "\n".join(linhas[2:]).strip()

# Determina se vamos usar imagem
caminho_imagem = caminho_imagem_lido if caminho_imagem_lido != "none" else None

# Cria o source com prompt e imagem (se fornecida)
source_kwargs = {
    "prompt": prompt_texto
}

if caminho_imagem:
    source_kwargs["image"] = types.Image.from_file(location=caminho_imagem)

source = types.GenerateVideosSource(**source_kwargs)

config = types.GenerateVideosConfig(
    aspect_ratio="9:16",
    number_of_videos=1,
    duration_seconds=8,
    person_generation="allow_all",
    generate_audio=True,
    resolution="720p",
    seed=0,
)

# Generate the video generation request
operation = client.models.generate_videos(
    model="veo-3.1-generate-001", source=source, config=config
)

# Waiting for the video(s) to be generated
while not operation.done:
    print("Video has not been generated yet. Check again in 10 seconds...")
    time.sleep(10)
    operation = client.operations.get(operation)

response = operation.result
if not response:
    print("Error occurred while generating video.")
    sys.exit(1)

generated_videos = response.generated_videos
if not generated_videos:
    print("No videos were generated.")
    sys.exit(1)

print(f"Generated {len(generated_videos)} video(s).")
for i, generated_video in enumerate(generated_videos):
    if generated_video.video:
        # Pega os dados do vídeo gerado
        video_bytes = generated_video.video.video_bytes
        
        # Define o nome do arquivo (ex: video1.mp4)
        nome_arquivo = f"video_{tema}_{i}.mp4"
        
        # Cria e salva o arquivo fisicamente na pasta onde você rodou o script
        with open(nome_arquivo, "wb") as f:
            f.write(video_bytes)
            
        print(f"Vídeo salvo com sucesso na sua máquina: {nome_arquivo}")