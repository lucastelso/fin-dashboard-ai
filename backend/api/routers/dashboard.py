# backend/api/routers/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import asyncio

from core.database import get_db
from core.logger import logger
from services.analytics import IndicadoresAnaliticos
from services.ml import executar_pipeline_kmeans
from services.macro_eco import MacroeconomiaAPI
from services.llm import AnalistaQualitativo
from services.macro_eco import MacroeconomiaAPI

# Definição do Router Modular com o prefixo unificado
router = APIRouter(
    prefix="/dashboard-ativos", 
    tags=['Analytics & Dashboard']
)
@router.get("/resumo")
async def resumo_mercado(
    # 'examples' no plural com uma lista para alinhar com o Pydantic V2
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
    

@router.get("/kpis-macro")
async def kpis_macroeconomicos() -> Dict[str, Any]:
    """
    ALIMENTA OS DADOS MACROECONOMICOS:
    Dados macroeconômicos que ficam no topo da tela (IPCA e SELIC)
    """
    try:
        dados = await MacroeconomiaAPI.get_kpis_gerais()
        return dados
    
    except Exception as e:
        logger.error(f"Erro no endpoint dos KPIs macroeconomicos")
        raise HTTPException(status_code=500, detail="Falha de comunicação com o Banco Central")

@router.get("/machine-learning")
async def analise_avancada_ml(
    request: Request,
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=["2026-07-10"]),
    ativos: Optional[List[str]] = Query(None, description="Tickers para clusterização. Vazio = Todos", alias="ativos"),
    n_clusters: int = Query(4, description="Quantidade de grupos desejada"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint de Machine Learning (Heavy Compute).
    """
    try:
        # A MAGIA DO FALLBACK: Se o usuário não enviou ativos,, pega a lista completa
        lista_ativos = ativos if ativos else IndicadoresAnaliticos.ATIVOS_B3

        analyzer = IndicadoresAnaliticos(session)
        matriz_retornos = await analyzer.get_features_ml(
            dt_inicio=dt_inicio, dt_fim=dt_fim, ativos=lista_ativos
        )
        
        if not matriz_retornos:
            raise HTTPException(status_code=404, detail="Sem dados suficientes para análise.")

        # Compute Bound: Despacha para um núcleo livre da CPU
        loop = asyncio.get_running_loop()
        pool = request.app.state.process_pool 
        
        resultado_ml = await loop.run_in_executor(
            pool, 
            executar_pipeline_kmeans, 
            matriz_retornos, 
            n_clusters
        )
        
        return resultado_ml

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro catastrófico no pipeline de ML: {e}")
        raise HTTPException(status_code=500, detail="Falha no modelo de Machine Learning.")
    

@router.get("/analise-qualitativa")
async def analise_qualitativa_ia(
    dt_inicio: str = Query(..., description="Data inicial YYYY-MM-DD", examples=["2026-07-01"]),
    dt_fim: str = Query(..., description="Data final YYYY-MM-DD", examples=["2026-07-10"]),
    ativos: List[str] = Query(None, description="Tickers alvo", alias="ativos"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Retorna um texto (Markdown) gerado por IA (Gemini) explicando os motivos 
    sociológicos e macroeconômicos por trás dos números do período.
    """
    try:
        lista_ativos = ativos if ativos else IndicadoresAnaliticos.ATIVOS_B3
        analyzer = IndicadoresAnaliticos(session)
        
        # Coleta a matemática (Usamos apenas as features 2D para economizar tokens na IA)
        dados_quantitativos = await analyzer.get_features_ml(dt_inicio, dt_fim, lista_ativos)
        features_2d = dados_quantitativos.get("features_2d", [])
        
        # Coleta o cenário Macro
        kpis_macro = await MacroeconomiaAPI.get_kpis_gerais()

        # Despacha para a IA (Como é uma chamada de rede I/O, o ideal é usar asyncio.to_thread para não travar o loop, ou o próprio SDK genai em modo async se disponível. Vamos usar to_thread por segurança).
        ia_service = AnalistaQualitativo()
        loop = asyncio.get_running_loop()
        
        # Roda a chamada da API do Gemini de forma segura
        sintese = await loop.run_in_executor(
            None, 
            ia_service.gerar_sintese, 
            dt_inicio, 
            dt_fim, 
            features_2d, 
            kpis_macro,
            lista_ativos
        )
        
        return {"texto_analise": sintese}

    except Exception as e:
        logger.error(f"Erro no endpoint /analise-qualitativa: {e}")
        raise HTTPException(status_code=500, detail="Falha ao gerar síntese da IA.")