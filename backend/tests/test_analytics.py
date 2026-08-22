import asyncio

from fin_dashboard.services.analytics import IndicadoresAnaliticos
from fin_dashboard.core.database import AsyncSessionLocal
from fin_dashboard.core.logger import logger

async def main():
    logger.info("Iniciando teste de integração do Analytics (Resumo Macro)...")
    
    # Gerenciador de contexto assíncrono 
    async with AsyncSessionLocal() as session:
        # Instancia a regra de negócio com a sessão injetada
        analyzer = IndicadoresAnaliticos(session)
        
        try:
            # Chama o método
            resultado = await analyzer.get_resumo_mercado(
                dt_inicio='2026-07-02', 
                dt_fim='2026-07-09'
            )
            
            # Formatação amigável para leitura no terminal
            print(f"\nResumo Retornado ({len(resultado['dados'])} ativos encontrados):")
            for item in resultado['dados']:
                print(f"Ativo: {item['ativo']:<10} | "
                      f"Abertura: {item['preco_inicial']:>6.2f} | "
                      f"Fechamento: {item['preco_final']:>6.2f} | "
                      f"Variação: {item['variacao_percentual']:>6.2f}%")
                      
        except Exception as e:
            logger.error(f"ERRO durante o processamento analítico: {e}")

if __name__ == "__main__":
    asyncio.run(main())