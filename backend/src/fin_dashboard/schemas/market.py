from typing import Generic, TypeVar, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Variável de tipo genérico para a a estrutura da resposta da API
T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Esquema genérico para a estrutura padrão de stats: resposta, dados: []"""
    status: str
    dados: List[T]

class KPIsMAcro(BaseModel):
    selic: float
    ipca: float

class Resumo(BaseModel):
    ativo: str
    preco_inicial: float
    preco_final: float
    variacao_percentual: float

class Series(BaseModel):
    ativo: str
    data: datetime
    fechamento: float
    ma: float
    ema: float
    log_return: float
    volatilidade: float

class MLMetricas(BaseModel):
    silhouette_score: float = Field(ge=-1.0, le=1.0)
    qtd_grupos: int = Field(gt=0)
    qtd_ativos: int = Field(gt=0)

class MLScatter(BaseModel):
    id: str
    x: float
    y: float
    cluster: str

class MLClusteringResult(BaseModel):
    metricas: MLMetricas
    scatterplot: List[MLScatter]

class AnaliseQualitativa(BaseModel):
    texto_analise: str



