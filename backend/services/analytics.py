import sys 

sys.path.append("backend")
from core.repository import BaseMarketRepository
from core.logger import logger

class IndicadoresAnaliticos(BaseMarketRepository):
    """Repositorio com os métodos relacionados ao Analytics de ativos financeiros"""

    async def media_movel(self, dt_inicio: str, dt_fim: str, ativo: str):
        """Retorna a média móvel de um ativo financeiro. 
        
        ### Parametros
        - **dt_inicio (str)**: data de inicio
        - **dt_fim (str)**: data final 
        - **ativo (str)**: nome do ativo
        
        ### Retorna
        Dicionário python padronizado para o endpoint do dashboard

        """