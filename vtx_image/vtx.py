from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

load_dotenv()

# Carregar configuração do arquivo
def load_config():
    with open("config.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    ppt = lines[0].strip()
    input_image = lines[1].strip() if len(lines) > 1 else "none"
    system_prompt = "".join(lines[2:]).strip() if len(lines) > 2 else ""
    
    # Converter "none" para None
    input_image = None if input_image.lower() == "none" else input_image
    
    return ppt, input_image, system_prompt

ppt, input_image, system_prompt = load_config()

# Inicializar banco de dados
def init_database():
    conn = sqlite3.connect("generations.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ppt TEXT,
            input_image TEXT,
            output_filename TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# Registrar geração no banco de dados
def register_generation(ppt_value, input_image_path=None):
    conn = sqlite3.connect("generations.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO generations (ppt, input_image, created_at)
        VALUES (?, ?, ?)
    """, (ppt_value, input_image_path, datetime.now().isoformat()))
    conn.commit()
    generation_id = cursor.lastrowid
    conn.close()
    return generation_id

init_database()

def generate(input_image_path=None):
    # Registrar geração no banco de dados
    generation_id = register_generation(ppt, input_image_path)
    
    # Note: If you are strictly using an API key from Google AI Studio, 
    # you usually want vertexai=False. If you are using Google Cloud Vertex AI, 
    # it normally relies on Application Default Credentials rather than an api_key.
    client = genai.Client(
        vertexai=True,
        api_key=os.environ.get("GOOGLE_CLOUD_API_KEY"),
    )

    model = "gemini-3.1-flash-image-preview"
    
    # Preparar contents com imagem de entrada (se fornecida) e prompt
    if input_image_path and os.path.exists(input_image_path):
        # Ler a imagem de entrada
        with open(input_image_path, "rb") as f:
            image_data = f.read()
        
        # Detectar tipo MIME baseado na extensão
        file_ext = os.path.splitext(input_image_path)[1].lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        mime_type = mime_types.get(file_ext, "image/png")
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=ppt),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=image_data
                        )
                    )
                ]
            )
        ]
    else:
        # Apenas o prompt de texto
        contents = ppt

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7, # Lower temperature is usually better for image consistency
        response_modalities=["IMAGE"],
        system_instruction=system_prompt,  # System prompt adicionado aqui
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
        # Removed thinking_config and max_output_tokens
    )

    print("Generating image... this may take a few seconds.")
    
    # 1. Use generate_content instead of generate_content_stream
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    # 2. Extract the image bytes and save to a file
    if response.candidates and response.candidates[0].content.parts:
        # The image data is returned as raw bytes in inline_data
        image_bytes = response.candidates[0].content.parts[0].inline_data.data
        
        # Nome do arquivo: {ppt}_{id}.png
        output_filename = f"{ppt}_{generation_id}.png"
        with open(output_filename, "wb") as f:
            f.write(image_bytes)
        
        # Atualizar nome do arquivo no banco de dados
        conn = sqlite3.connect("generations.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE generations SET output_filename = ? WHERE id = ?
        """, (output_filename, generation_id))
        conn.commit()
        conn.close()
            
        print(f"Success! Image saved to {output_filename}")
    else:
        print("No image was generated. Check the response for errors.")
        print(response)

if __name__ == "__main__":
    # Chamar com imagem configurada em config.txt
    generate(input_image)