import httpx
from datetime import datetime, timezone
import sys
sys.path.append("backend")
from core.logger import logger

async def fetch_yahoo_json_async(
        ticker: str, 
        start_timestamp: int, 
        end_timestamp: int
        ) -> list[dict] | None:
    """
    Substitui a yfinance.Bate na API crua do Yahoo e extrai apenas a 
    lista de dicionários (Python nativo). Utiliza httpx assíncrono 
    para não travar a thread principal.

    ### Parâmetros
    - **`ticker`**: Símbolo do ativo (ex: "AAPL", "GOOG", "MSFT").
    - **`start_timestamp`**: Timestamp Unix de início (em segundos).
    - **`end_timestamp`**: Timestamp Unix de fim (em segundos).

    ### Retorno
    - Lista de dicionários com os dados históricos do ativo, ou None em caso de erro.

    
    """
    # A API V8 do Yahoo para gráficos históricos (retorna JSON puro)
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
    
    # O Yahoo exige timestamps Unix
    params = {
        "period1": start_timestamp,
        "period2": end_timestamp,
        "interval": "5m",
        "events": "history"
    }
    
    # Headers para emular um navegador padrão (evita rate limit rápido)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # httpx é assíncrono e não trava a thread principal
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            
            if response.status_code != 200:
                logger.error(f"Erro {response.status_code} para {ticker}")
                return None
            
            data = response.json()
            
            # Navegando pela estrutura feia do JSON do Yahoo
            result = data.get("chart", {}).get("result", [])
            if not result:
                logger.warning(f"Sem dados no JSON para {ticker}")
                return None
                
            chart_data = result[0]
            timestamps = chart_data.get("timestamp", [])
            indicators = chart_data.get("indicators", {}).get("quote", [{}])[0]
            
            # Alguns dados ajustados vêm em outra chave, mas para nossa base, os "quotes" já servem
            opens = indicators.get("open", [])
            highs = indicators.get("high", [])
            lows = indicators.get("low", [])
            closes = indicators.get("close", [])
            volumes = indicators.get("volume", [])
            
            # Zipping arrays em dicionários (100% Python nativo)
            records = []
            for i, ts in enumerate(timestamps):
                # O Yahoo pode ter lacunas (Nones) nos dados de preço durante feriados parciais
                if closes[i] is not None: 
                    records.append({
                        "ticker": ticker,
                        # Converte timestamp Unix para datetime seguro
                        "date": datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None),
                        "open": opens[i],
                        "high": highs[i],
                        "low": lows[i],
                        "close": closes[i],
                        "volume": volumes[i]
                    })
                    
            return records

    except Exception as e:
        logger.error(f"Falha na conexão direta para {ticker}: {e}")
        return None