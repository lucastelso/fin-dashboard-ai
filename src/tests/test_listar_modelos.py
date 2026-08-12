import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "backend"))

from core.logger import logger

from dotenv import load_dotenv
load_dotenv(dotenv_path=BASE_DIR / ".env")

from google import genai

def ver_modelos_autorizados():
    logger.info("Consultando a infraestrutura do Google para listar os modelos liberados na sua chave...")
    try:
        # A injeção de dependência via .env já está garantida
        client = genai.Client()
        
        print("\n--- MODELOS DISPONÍVEIS ---")
        # Itera sobre o catálogo oficial da API
        for m in client.models.list():
            print(f"{m.name}")
        print("---------------------------\n")
            
    except Exception as e:
        logger.error(f"Erro de conexão com o Gateway: {e}")

if __name__ == "__main__":
    ver_modelos_autorizados()