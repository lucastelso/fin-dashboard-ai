from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
import concurrent.futures
import multiprocessing

from fin_dashboard.services.scheduler import setup_scheduler, scheduler, job_ingestao_5m
from fin_dashboard.core.logger import logger
from fin_dashboard.core.database import engine
from fin_dashboard.models.market import Base
from fin_dashboard.api.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando Dashboard Financeiro - API...")
    
    # Cria tabelas caso não existam na inicialização
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Cria um ProcessPoolExecutor para tarefas pesadas e inicia ingestão de dados
    try:
        await job_ingestao_5m()
        logger.info("[BOOTSTRAP] Carga inicial concluída com sucesso.")
    except Exception as e:
        logger.error(f"[BOOTSTRAP] Falha crítica na carga inicial: {e}")
    
    workers = max(1, multiprocessing.cpu_count() - 2)
    app.state.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
    
    # Liga o Agendador de Ingestão em background
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler iniciado. Ingestão rodará de seg-sex, 10h-17h a cada 15m.")
    
    yield # HORA DO SHOW

    # Desliga o Scheduler e o ProcessPool na finalização da aplicação
    logger.info("Desligando ProcessPool e Scheduler...")
    scheduler.shutdown()
    app.state.process_pool.shutdown(wait=True, cancel_futures=True)

app = FastAPI(
    title="Dashboard Financeiro Inteligente",
    lifespan=lifespan
)

# Router Global que vai abraçar TUDO da API.
api_router = APIRouter(prefix="/api-financeira")

@api_router.get("/", tags=["greetings"])
async def greetings():
    return {
        "Greetings": "BOAS VINDAS AO ENDPOINT DO DASHBOARD FINANCEIRO INTELIGENTE"
    }

@api_router.get("/health", tags=["Infraestrutura"])
async def health_check():
    return {
        "status": "operacional, banco de dados isolado", 
        "versao": "alpha"
        }

# super-árvore de rotas na aplicação principal
api_router.include_router(dashboard_router)

# Routers
app.include_router(api_router)