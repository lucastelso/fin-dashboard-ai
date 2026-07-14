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