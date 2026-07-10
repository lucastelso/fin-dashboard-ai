from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

# Não precisa de sys.path.append se o PYTHONPATH estiver correto no Docker/Linux
from core.database import get_db
from core.logger import logger
from services.analytics import IndicadoresAnaliticos

router = APIRouter()

@router.get("/dashboard-ativos", tags=['dashboard'])
async def get_dashboard(
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint de Analytics: Entrega dados processados quantitativamente para o Frontend.
    """
    try:
        analyzer = IndicadoresAnaliticos(session) 
        
        # Await aguarda o cálculo voltar do motor Polars
        resultado = await analyzer.get_media_movel(
            dt_inicio='2026-07-01',
            dt_fim='2026-07-10',
            ativo='LVOL11.SA'
        )
        
        # Se voltar vazio, retorna um 404
        if not resultado['dados']:
            raise HTTPException(status_code=404, detail="Sem dados para este ativo no período.")
            
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no cálculo analítico da rota: {e}")
        raise HTTPException(status_code=500, detail="Falha no processamento matemático.")