# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import concurrent.futures
import multiprocessing
import asyncio

from core.logger import logger
# from api.routers import market  # Descomentaremos no próximo passo

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando Dashboard Financeiro - API...")
    
    workers = max(1, multiprocessing.cpu_count() - 2)
    app.state.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
    logger.info(f"ProcessPool instanciado com {workers} processos paralelos.")
    
    yield
    
    logger.info("Iniciando desligamento do ProcessPool. Aguardando workers finalizarem...")
    app.state.process_pool.shutdown(wait=True, cancel_futures=True)

app = FastAPI(
    title="Dashboard Financeiro - Analytics de Ativos",
    description="API de análise quantitativa e qualitativa (IA) de ativos de mercado",
    lifespan=lifespan
)

# Adicionamos o prefixo /api para casar com a regra de roteamento do Nginx
@app.get("/api/health", tags=["Infraestrutura"])
async def health_check():
    return {"status": "operacional"}

# Quando formos usar os routers separados, faremos assim:
# app.include_router(market.router, prefix="/api/v1/market", tags=["Market Data"])