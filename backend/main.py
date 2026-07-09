# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
import concurrent.futures
import multiprocessing

from core.logger import logger
# from api.routers import market 

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando Dashboard Financeiro - API...")
    workers = max(1, multiprocessing.cpu_count() - 2)
    app.state.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
    yield
    logger.info("Desligando ProcessPool...")
    app.state.process_pool.shutdown(wait=True, cancel_futures=True)

app = FastAPI(
    title="Dashboard Financeiro Inteligente",
    lifespan=lifespan
)

# 1. Criamos o Router Global que vai abraçar TUDO da API.
api_router = APIRouter(prefix="/api-financeira")

# 2. As rotas agora são penduradas no api_router, e não mais no app diretamente
@api_router.get("/health", tags=["Infraestrutura"])
async def health_check():
    return {
        "status": "operacional, banco de dados isolado", 
        "versao": "alpha"
        }

@api_router.get("/dashboard", tags=["Analytics"])
async def get_dashboard_metrics():
    # Simulando um payload
    return {
        "kpi_mensal_inventado": 14500.50, 
        "risco_sistemico": "baixo",
        "ativos_em_alta": ["AAPL", "GOOGL", "AMZN"]}

# 3. super-árvore de rotas na aplicação principal
app.include_router(api_router)