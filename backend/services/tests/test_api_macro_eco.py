import sys
import asyncio

sys.path.append("backend")

from services.macro_eco import MacroeconomiaAPI
from core.logger import logger

async def main():
    logger.info("INICIANDO TESTE DA API DE DADOS MACROECONÔMICOS")
    
    try:
        macro = MacroeconomiaAPI()
        data = await macro.get_kpis_gerais()
        
        
        print(
            f"="*20, "\n"
            f"SELIC:{data.get('selic')}",
            f"\nIPCA:{data.get('ipca')}",
            "\n","="*20
            )

    except Exception as e:
        logger.error(f"ERRO ao tentar coletar os dados:{e}")
    
    finally:
        logger.info(f"TESTE FINALIZADO")

if __name__ == "__main__":
    asyncio.run(main())