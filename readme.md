# APP FINANCEIRO INTELIGENTE

Esse aplicativo foi desenvolvido com o objetivo de permitir o acompanhamento da ativos de renda variável e com a possibilidade:

- Permanencia de preços em banco de dados próprios;
- Análise de preços com modelos de séries temporais
- Análise do comportamento conjunto de ações e oportunidades de diversificação com k-means++
- Análise de conjuntura econômica com inteligência artificial generativa


## ROADMAP

O Roadmap de DesenvolvimentoA ordem aqui é crítica. Construir a interface antes de garantir a ingestão dos dados gera um retrabalho enorme de tipagem e contratos de API.

### 1. Fundação e Ingestão de Dados:

Foco: Garantir que os dados cheguem com qualidade.Criação do ambiente virtual com UV. Estruturação do repositório. Desenvolvimento dos scripts assíncronos que farão o fetch diário (OHLCV) de APIs gratuitas (como yfinance) e salvarão em DataFrames do Polars para validação de tipagem e dados nulos.

### 2. Persistência e Modelagem (PostgreSQL):

Foco: Desenhar o esquema do banco.Configuração do container Docker do PostgreSQL. Criação dos modelos declarativos no SQLAlchemy e configuração do asyncpg. Uso do Alembic para gerenciar as migrações do banco. Inserção dos dados processados pelo Polars nas tabelas do banco.

### 3. Motor Analítico (Quant & ML):

Foco: K-means e Estatística.Criação dos endpoints no FastAPI que puxam o histórico do banco de dados para o Polars. Implementação do algoritmo K-means no backend (usando scikit-learn interligado ao Polars) para clusterizar os ativos baseados nos retornos logarítmicos diários.

### 4. Integração Qualitativa (Gemini API):

Foco: O diferencial do seu projeto.Criação de um serviço que detecta variações de preço superiores a um desvio padrão ($\pm 2\sigma$). Para essas anomalias, o backend dispara um prompt estruturado para o Gemini via API pedindo o contexto das notícias daquele dia, e salva a string de resposta no banco, vinculada ao ticker e à data.

### 5. Desenvolvimento da API Restful:

Foco: Fechar o contrato de dados.Finalização dos routers do FastAPI. Implementação de rotas assíncronas limpas retornando JSONs estritos (validados pelo Pydantic) para o Frontend consumir (ex: /api/v1/assets/clusters, /api/v1/assets/{ticker}/insights).

### 6. Frontend Frontal (React + Vite):

Foco: Consumo e UI/UX.Criação do projeto React. Configuração do Axios/Fetch para consumir sua API. Implementação de gráficos de linha/candlestick e painéis laterais mostrando os "Insights da IA" e os clusters de ativos.

### 7. Orquestração (Docker Compose):

Foco: Deploy e DevOps.Empacotamento do backend, frontend e banco de dados em um docker-compose.yml unificado. Configuração de redes internas para que os containers conversem entre si com segurança e isolamento.

## Estrutura geral do repositorio

```plaintext
fin-dashboard-project/
├── backend/
│   ├── app/
│   │   ├── api/          # Routers do FastAPI (endpoints)
│   │   ├── core/         # Configurações, segurança, instâncias de banco
│   │   ├── models/       # SQLAlchemy models (Tabelas)
│   │   ├── schemas/      # Pydantic models (Validação de I/O)
│   │   ├── services/     # Regras de negócio (Polars, Gemini, K-means)
│   │   └── main.py       # Ponto de entrada do FastAPI
│   ├── alembic/          # Migrações do banco
│   ├── requirements.in   # Dependências abertas
│   ├── requirements.txt  # Dependências lockadas pelo UV
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/     # Chamadas para a sua API FastAPI
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
└── docker-compose.yml    # Orquestra Postgres, Backend e Frontend
```


### Passo 1 - Levantamento de requisitos e ambiente

Para implementar o prjeot, é necessário termos biblioteca web i/o e async, de machine learning, banco de dados, sql, api do yahoo finance e a api do gemini. 

Nós vamos coletar os dados da API do yahoo, mas não vamos utilizar yfinance, pois ele retorna uma série do pandas. Vamos evitar o pandas pois ele é single thread e bem mais lento e pesado do que o polars.

```.txt
# Web Framework & Async I/O
fastapi
uvicorn[standard]

# Database & ORM
sqlalchemy
asyncpg
alembic

# Data Processing & ML
polars
scikit-learn

# External Data & LLM
google-generativeai

# Utilities
python-dotenv
httpx
```


### Passo 2 - 

Criamos a conexão do banco de dados, as tabelas 

```
backend/
├── core/
│   └── database.py       # Gerenciamento da conexão e engine assíncrona
├── models/
│   └── market.py         # O mapeamento Declarativo (Tabelas)
└── services/
    ├── fetch_yahoo.py    # Coleta dos dados direto a API do Yahoo
    └── db_repository.py  # Funções de interação com o banco (Upsert)

```

### Passo 3 - Inserir os dados no banco 

A forma padrão de inserir os dados no banco de dados utilizando a nossa engine deve ser a seguinte:

```python
async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Iniciando transação de persistência assíncrona...")
        async with AsyncSessionLocal() as session:
            await upsert_asset_prices(session, master_df)
```

### Passo 4 - Criando uma classe de repositório

A Engine é uma fábrica de conexões global. Se você atrelar a classe à Engine, você quebra o ciclo de vida transacional (ACID). No FastAPI, usamos o princípio da Injeção de Dependência (Dependency Injection). O FastAPI abre uma Session quando o usuário faz a requisição (ex: clica no gráfico), passa essa sessão viva para a sua classe, a classe busca os dados, e o FastAPI fecha a sessão ao devolver a resposta. Isso evita vazamento de memória e deadlocks no banco

```python
# backend/repositories/base.py
import asyncio
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import polars as pl
from core.logger import logger

class BaseMarketRepository:
    """
    Classe Abstrata de repositório focada em performance bruta.
    Garante Injeção de Dependência da sessão assíncrona do FastAPI.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def fetch_as_polars(self, query_sql: str, params: dict[str, Any] | None = None) -> pl.DataFrame:
        """
        Executa SQL parametrizado assincronamente e vetoriza o resultado 
        para a memória C/Rust do Polars evitando o gargalo do SQLAlchemy ORM.
        """
        try:
            # 1. I/O Bound: Requisição de rede 100% não-bloqueante
            result = await self.session.execute(text(query_sql), params or {})
            
            columns = list(result.keys())
            raw_rows = result.fetchall()

            if not raw_rows:
                logger.warning("Query retornou vazia. Instanciando Polars vazio.")
                return pl.DataFrame(schema=columns)

            # 2. CPU Bound: Isolamento térmico da thread principal
            def _build_dataframe(rows, cols):
                pure_tuples = list(map(tuple, rows))
                return pl.DataFrame(pure_tuples, schema=cols, orient="row")

            df = await asyncio.to_thread(_build_dataframe, raw_rows, columns)
            return df
            
        except Exception as e:
            logger.error(f"Falha na extração vetorizada: {e}")
            raise e
```