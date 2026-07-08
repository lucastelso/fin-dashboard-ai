# backend/schemas/market.py
""" 
Essa seção contém os schemas Pydantic para validação e 
serialização de dados relacionados ao mercado financeiro.

A ideia é garantir que o que é entregue à API React seja,
de fato, aquilo que foi prometido pela API.

"""

from pydantic import BaseModel, ConfigDict
from datetime import date

class AssetHistoryResponse(BaseModel):
    ativo: str
    data: date
    abertura: float
    fechamento: float
    volume: int

    # Configuração para permitir que o Pydantic leia direto de Dicionários/Objetos
    model_config = ConfigDict(from_attributes=True)

# EXEMPLO DE K-MEANS
# class KMeansClusterResponse(BaseModel):
#     ativo: str
#     cluster_id: int
#     risco_volatilidade: float