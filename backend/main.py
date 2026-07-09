# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
import concurrent.futures
import multiprocessing

from services.scheduler import setup_scheduler, scheduler
from core.logger import logger
from core.database import engine
from models.market import Base

# from api.routers import market 

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando Dashboard Financeiro - API...")
    
    # 1. Cria tabelas caso não existam na inicialização
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Cria um ProcessPoolExecutor para tarefas pesadas, como ingestão de dados
    workers = max(1, multiprocessing.cpu_count() - 2)
    app.state.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
    
    # 3. Liga o Agendador de Ingestão em background
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler iniciado. Ingestão rodará de seg-sex, 10h-17h a cada 15m.")
    
    yield # HORA DO SHOW

    # 4. Desliga o Scheduler e o ProcessPool na finalização da aplicação
    logger.info("Desligando ProcessPool e Scheduler...")
    scheduler.shutdown()
    app.state.process_pool.shutdown(wait=True, cancel_futures=True)

app = FastAPI(
    title="Dashboard Financeiro Inteligente",
    lifespan=lifespan
)

# Router Global que vai abraçar TUDO da API.
api_router = APIRouter(prefix="/api-financeira")

# As rotas agora são penduradas no api_router, e não mais no app diretamente
@api_router.get("/health", tags=["Infraestrutura"])
async def health_check():
    return {
        "status": "operacional, banco de dados isolado", 
        "versao": "alpha"
        }

# super-árvore de rotas na aplicação principal
app.include_router(api_router)
# rota do dashboard
# roda do ml