import os
import time
import sys
from google import genai
from google.genai import types

# 1. Aponta para o arquivo JSON de credenciais
# ATENÇÃO: Lembre-se de baixar a chave no painel do Google Cloud e colocar neste caminho
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/vando/projects/vtx/somnacity-credenciais.json"

# 2. Inicializa o cliente na Vertex AI usando o projeto e localização
client = genai.Client(
    vertexai=True,
    project="somnacity-493113",
    location="us-central1",
)

source = types.GenerateVideosSource(
    prompt="""Crie um vídeo curto (6 a 10 segundos), sem tela de abertura, começando direto na ação.

Tema: suporte técnico e consultoria em tecnologia no dia a dia.

Cenário:
Ambiente realista (casa, pequeno escritório ou comércio). Uma pessoa comum visivelmente frustrada com um problema técnico (computador lento, sistema travando, internet instável, tarefa manual repetitiva).

Cena 1 (0–3s):
A pessoa tenta resolver o problema, demonstra leve frustração (sem exagero). Ambiente natural, sem atuação forçada.

Cena 2 (3–6s):
Transição simples mostrando a solução sendo aplicada (pode ser alguém configurando, organizando ou automatizando). Tudo de forma visual e objetiva.

Cena 3 (6–10s):
Resultado: tudo funcionando de forma fluida. Pessoa mais tranquila, trabalhando normalmente.

Estilo visual:
- realista
- iluminação natural
- cores neutras
- sem estética corporativa
- sem exagero futurista

Texto na tela (curto e direto):
"Não está funcionando direito?"
→ "Dá pra resolver."

OU

"Menos problema. Mais solução."

Sem narração obrigatória (opcional, tom natural se houver).
Sem música épica (som ambiente ou leve trilha discreta).

Objetivo:
Transmitir que problemas técnicos do dia a dia têm solução simples com ajuda certa.

Tom:
humano, acessível, prático, confiável.

Evitar:
- linguagem técnica
- termos complexos
- estética de empresa grande
- promessas exageradas""",
)

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
        
        # Define o nome do arquivo (ex: somnacity_video_0.mp4)
        nome_arquivo = f"somnacity_video_{i}.mp4"
        
        # Cria e salva o arquivo fisicamente na pasta onde você rodou o script
        with open(nome_arquivo, "wb") as f:
            f.write(video_bytes)
            
        print(f"Vídeo salvo com sucesso na sua máquina: {nome_arquivo}")