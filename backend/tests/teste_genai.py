import sys
import os
from pathlib import Path

# Encontra a raiz do projeto dinamicamente a partir do arquivo de teste
BASE_DIR = Path(__file__).resolve().parent.parent.parent

sys.path.append(str(BASE_DIR / "backend"))


# Importa a biblioteca para carregar variáveis de ambiente locais
from dotenv import load_dotenv
# Aponta rigorosamente para o arquivo .env localizado na raiz do projeto
load_dotenv(dotenv_path=BASE_DIR / ".env")

from services.llm import AnalistaQualitativo

def testar_gemini():
    print("Iniciando teste do Analista Qualitativo (Gemini + Grounding)...")
    
    # Validação rápida para garantir que a chave foi injetada no ambiente do sistema operacional
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ERRO: GEMINI_API_KEY não encontrada no escopo do arquivo .env da raiz.")
        return

    # Agora a inicialização não falhará por falta de chave
    ia = AnalistaQualitativo()
    
    dt_inicio = "2026-07-02"
    dt_fim = "2026-07-09"
    ativos = ["PETR4.SA", "BBAS3.SA"]
    
    kpis_macro = {
        "selic": 14.25,
        "ipca": 4.64
    }
    
    dados_quant = [
        {"ativo": "PETR4.SA", "retorno_acumulado": 2.5, "volatilidade": 1.2},
        {"ativo": "BBAS3.SA", "retorno_acumulado": -4.1, "volatilidade": 2.8}
    ]
    
    try:
        resultado = ia.gerar_sintese(dt_inicio, dt_fim, dados_quant, kpis_macro, ativos) # type: ignore
        print("\n" + "="*50)
        print("🤖 RESPOSTA DA IA COM GROUNDING:")
        print("="*50)
        print(resultado)
        print("="*50 + "\n")
    except Exception as e:
        print(f"❌ Erro durante a execução da API: {e}")

if __name__ == "__main__":
    testar_gemini()