import sys
import asyncio

sys.path.append("backend")

from services.ml import executar_pipeline_kmeans
from core.logger import logger
from core.database import AsyncSessionLocal
from services.analytics import IndicadoresAnaliticos

ATIVOS_B3 = [    
    "PETR4.SA", "PETR3.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", 
    "BBDC3.SA",  "BBAS3.SA", "ABEV3.SA", "WEGE3.SA", "SUZB3.SA",  
    "RENT3.SA", "B3SA3.SA", "RADL3.SA", "JBSS3.SA", "BPAC11.SA", 
    "EQTL3.SA", "VIVT3.SA","RAIL3.SA", "SBSP3.SA", "PRIO3.SA", 
    "BBSE3.SA", "GGBR4.SA", "UGPA3.SA", "CMIG4.SA", "CSAN3.SA", 
    "HYPE3.SA", "ENEV3.SA", "TIMS3.SA", "TOTS3.SA", "EGIE3.SA", 
    "KLBN11.SA", "CSNA3.SA", "ALPA4.SA","IVVB11.SA", "LVOL11.SA", 
    "DIVO11.SA", "SMAL11.SA", "BOVA11.SA"
    ]

async def main():
    logger.info("Iniciando teste do kmeans")

    async with AsyncSessionLocal() as session:
        analyzer = IndicadoresAnaliticos(session)

        try:
            df = await analyzer.get_matriz_retornos(
                dt_inicio="2026-07-02",
                dt_fim="2026-07-09",
                ativos= ATIVOS_B3
            )
        except Exception as e:
            logger.error(f"ERRO durante criação da matriz de retornos: {e}")
            return
        
        try:    
            resultado = executar_pipeline_kmeans(
                matriz_retornos=df, 
                n_clusters=4
            )
            
            print("\n" + "="*40)
            print("GRUPOS GERADOS PELO K-MEANS")
            print("="*40)
            
            for cluster_nome, ativos_no_grupo in resultado["clusters"].items():
                print(f"\n{cluster_nome}:")
                # Junta a lista de ativos com vírgulas para não ocupar muitas linhas
                print(" -> " + ", ".join(ativos_no_grupo))

            print("\n" + "="*40)
            print(f"Matriz de Correlação gerada com {len(resultado['correlacao'])} pares cruzados.")
            print("="*40 + "\n")

        except Exception as e:
            logger.error(f"ERRO na execução do pipeline do kmeans: {e}")

        finally:
            return logger.info("FIM DO TESTE")


if __name__ == "__main__":
    asyncio.run(main())