import asyncio
from typing import Any, Dict, List, Union
from datetime import datetime

from fin_dashboard.core.repository import BaseMarketRepository
from fin_dashboard.services.scheduler import TICKERS_B3
from fin_dashboard.services.utils import (
    _processar_resumo_mercado_cpu,
    _processar_serie_temporal_cpu,
    _processar_features_ml_cpu
)

class IndicadoresAnaliticos(BaseMarketRepository):
    """        
    Repositório orquestrador de Analytics.
    Delega processamento matricial para Worker Threads a fim de proteger o Event Loop do FastAPI.
    """
    
    ATIVOS_B3 = TICKERS_B3

    async def get_resumo_mercado(self, dt_inicio: str, dt_fim: str) -> Dict[str, Any]:
        query = """
            SELECT p.ativo, q.date as data, q.close as fechamento
            FROM dim_ativos as p
            INNER JOIN series_ativos as q 
                ON p.id_dim_ativo = q.id_dim_ativo
            WHERE q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
        """
        data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
        data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

        df = await self.fetch_as_polars(query, params={'dt_inicio': data_start, 'dt_fim': data_end})


        dados_processados = await asyncio.to_thread(_processar_resumo_mercado_cpu, df)
        
        return {'status': 'sucesso', "dados": dados_processados}


    async def get_serie_temporal_features(
              self, dt_inicio: str, dt_fim: str, ativos: Union[str, List[str]], janela: int = 5
        ) -> Dict[str, Any]:
        if isinstance(ativos, str):
            ativos = [ativos]

        query = """
            SELECT p.ativo, q.date as data, q.close as fechamento
            FROM dim_ativos as p
            INNER JOIN series_ativos as q 
                ON p.id_dim_ativo = q.id_dim_ativo
            WHERE p.ativo = ANY(:ativos)
                AND q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
            ORDER BY p.ativo ASC, q.date ASC 
        """
        
        data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
        data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

        df = await self.fetch_as_polars(query, params={'dt_inicio': data_start, 'dt_fim': data_end, 'ativos': ativos})

        if df.is_empty():
            return {'status': 'df vazio', "dados": []}

        # Regras de negócio de downsampling estabelecidas
        dias_intervalo = (data_end - data_start).days
        rule = None
        if dias_intervalo > 365:
            rule = "1d"   # Mais de 1 ano: diário
        elif dias_intervalo > 90:
            rule = "1h"  

        dados_processados = await asyncio.to_thread(_processar_serie_temporal_cpu, df, janela, rule)
        
        if not dados_processados:
            return {'status': 'df vazio', 'dados': []}

        return {'status': 'sucesso', "dados": dados_processados}


    async def get_features_ml(self, dt_inicio: str, dt_fim: str, ativos: List[str]) -> Dict[str, Any]:
        query = """
            SELECT p.ativo, q.date as data, q.close as fechamento
            FROM dim_ativos as p
            INNER JOIN series_ativos as q 
                ON p.id_dim_ativo = q.id_dim_ativo
            WHERE p.ativo = ANY(:ativos)
                AND q.date BETWEEN CAST(:dt_inicio AS TIMESTAMP) AND CAST(:dt_fim AS TIMESTAMP)
        """
        data_start = datetime.strptime(f"{dt_inicio} 00:00:00", "%Y-%m-%d %H:%M:%S")
        data_end = datetime.strptime(f"{dt_fim} 23:59:59", "%Y-%m-%d %H:%M:%S")

        df = await self.fetch_as_polars(
            query, params={'dt_inicio': data_start, 'dt_fim': data_end, 'ativos': ativos}
        )

       
        dados_processados = await asyncio.to_thread(_processar_features_ml_cpu, df)

        return dados_processados