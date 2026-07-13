# backend/api/routers/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from core.database import get_db
from core.logger import logger
from services.analytics import IndicadoresAnaliticos

# Definição do Router Modular com o prefixo unificado
router = APIRouter(
    prefix="/dashboard-ativos", 
    tags=['Analytics & Dashboard']
)
@router.get("/resumo")
async def resumo_mercado(
    # Usamos 'examples' (plural) com uma lista para alinhar com o Pydantic V2
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=["2026-07-10"]),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    ALIMENTA A TABELA GERAL (Macro):    
    Retorna o primeiro preço, o último preço e a variação percentual de TODOS 
    os ativos da base no período selecionado, em uma única chamada de banco.
    """
    try:
        analyzer = IndicadoresAnaliticos(session)
        resultado = await analyzer.get_resumo_mercado(dt_inicio=dt_inicio, dt_fim=dt_fim)
        
        if not resultado['dados']:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado para o período filtrado.")
            
        return resultado  # Já segue o contrato {"dados": [...]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Falha crítica no endpoint /resumo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento macro dos ativos.")


@router.get("/series")
async def serie_temporal_ativos(
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=["2026-07-10"]),
    ativos: List[str] = Query(..., description="Lista de tickers para o gráfico", alias="ativos"),
    janela: int = Query(20, description="Janela de períodos para EMA/Volatilidade"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    ALIMENTA O GRÁFICO DINÂMICO (Micro):
    Retorna a série temporal cronológica com preço de fechamento, EMA 
    e volatilidade calculados via Polars para os ativos selecionados.
    """
    try:
        analyzer = IndicadoresAnaliticos(session)
        resultado = await analyzer.get_serie_temporal_features(
            dt_inicio=dt_inicio,
            dt_fim=dt_fim,
            ativos=ativos,
            janela=janela
        )
        
        if not resultado['dados']:
            raise HTTPException(status_code=404, detail="Nenhum dado disponível para o(s) ativo(s) selecionado(s).")
            
        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Falha crítica no endpoint /series: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no cálculo quantitativo da série temporal.")