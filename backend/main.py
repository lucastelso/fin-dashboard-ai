# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import concurrent.futures
import multiprocessing

from core.logger import logger
# from api.routers import market  # Descomentaremos no próximo passo

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Aloca recursos pesados (como o Process Pool para ML) na inicialização
    e destrói graciosamente no encerramento.
    """
    logger.info("Inicializando Dashboard Financeiro - API...")
    
    # Descobre quantos núcleos físicos temos e reserva para o Machine Learning
    # Evita usar 100% da máquina para não travar o SO
    workers = max(1, multiprocessing.cpu_count() - 1)
    
    # Criamos um Process Pool (não Thread Pool) para bypassar o GIL em tarefas CPU-Bound
    app.state.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
    logger.info(f"Compute Plane instanciado com {workers} processos paralelos.")
    
    yield
    
    logger.info("Desligando API. Encerrando Process Pool...")
    app.state.process_pool.shutdown(wait=True)

app = FastAPI(
    title="Dashboard Financeiro - Analytics de Ativos",
    description="API de análise quantitativa e qualitativa (IA) de ativos de mercado",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Ajustar em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Infraestrutura"])
async def health_check():
    return {"status": "operacional"}

# app.include_router(market.router, prefix="/api/v1/market", tags=["Market Data"])