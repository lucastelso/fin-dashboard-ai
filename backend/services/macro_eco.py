import httpx
from typing import Dict, Any
from core.logger import logger

class MacroeconomiaAPI:
    """
    Cliente para integração com a API do Banco Central do Brasil (SGS).
    """
    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados/ultimos/1?formato=json"

    # Dicionário de Séries Oficiais do BCB
    SERIES = {
        "selic_meta": 432,   # Taxa Selic Meta (% a.a.)
        "ipca_12m": 13522    # IPCA Acumulado 12 meses (%)
    }

    @classmethod
    async def _fetch_serie(cls, codigo: int) -> float:
        """
        Executa a chamada assíncrona com timeout estrito para evitar travamento de rota.
        """
        url = cls.BASE_URL.format(codigo)
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
                
                if payload and len(payload) > 0:
                    return float(payload[0]["valor"])
                    
            except httpx.HTTPError as e:
                logger.error(f"[MACRO API] Falha na rede ao buscar série {codigo}: {e}")
            except (KeyError, ValueError, IndexError) as e:
                logger.error(f"[MACRO API] Payload corrompido na série {codigo}: {e}")
                
        return 0.0 # Fallback seguro para o front-end não quebrar

    @classmethod
    async def get_kpis_gerais(cls) -> Dict[str, float]:
        """
        Gera o payload para os Cards do cabeçalho do Dashboard.
        """
        # Aqui é possível usar o asyncio.gather se adicionarmos muitas séries no futuro
        selic = await cls._fetch_serie(cls.SERIES["selic_meta"])
        ipca = await cls._fetch_serie(cls.SERIES["ipca_12m"])

        return {
            "selic": selic,
            "ipca": ipca
        }