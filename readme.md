
---
# Dashboard Financeiro Inteligente

## 1. Filosofia Arquitetural e Design de Sistema

O **Dashboard Financeiro Inteligente** é um projeto desenvolvido por Lucas Valoz Castellucci com a finalidade de unir Ciência de Dados e Engenharia de Software para oferecer um Dashboard interativo dos principais ativos financeiros da B3, com possibilidade de análise quantitativa, via análise de médias móveis exponenciais, variação percentual, avaliação de risco e retorno por investimento, e qualitativa, via integração com o Grande Modelo de Língua (LLM): _Google Gemini_.


O **Dashboard Financeiro Inteligente** foi concebido sob os preceitos que unem, em sua arquitetura de software, a separação estrita de responsabilidades (*Separation of Concerns*), isolando a camada de apresentação (SPA React), a camada de roteamento HTTP (FastAPI) e os motores de processamento analítico (Polars e Scikit-Learn).


A filosofia central do projeto baseia-se em **Resiliência e Desempenho**:

* **Processamento Assíncrono (Async I/O):** Toda a comunicação de rede (ingestão do Yahoo Finance, consultas ao PostgreSQL, chamadas à API do Gemini) é estritamente não-bloqueante, garantindo que o *Event Loop* do servidor nunca congele durante requisições pesadas.

* **Vetorização de Dados:** O processamento de séries temporais abandona iteradores e a biblioteca Pandas em favor do **Polars**, utilizando execução *multithreaded* em Rust para agregações e cálculos complexos em milissegundos.

* **Degradação Suave (*Graceful Degradation*) e *Exponential Backoff*:** Microsserviços dependentes de cotas externas (como APIs de LLMs) implementam lógicas de recuo exponencial e *fallback* (como *web scraping* nativo) para garantir que o sistema central continue operando mesmo sob falhas ou *Rate Limits* de provedores terceiros.

## 2. Stack Tecnológica

### Backend (Processamento e API)

* **Linguagem:** Python 3.12
* **Framework Web:** FastAPI (ASGI)
* **Motor de Dados:** Polars (Manipulação de DataFrames de alta performance com multithread)
* **Machine Learning:** Scikit-Learn (K-Means Clustering, Silhouette Score)
* **ORM e Banco de Dados:** SQLAlchemy 2.0 (Assíncrono com Asyncpg) integrado ao PostgreSQL.
* **Integração de IA:** Google GenAI SDK (Gemini 3.5 Flash) com injeção de contexto via RSS web scraping.
* **Agendador de Tarefas:** APScheduler (Cron jobs assíncronos).
* **Requisições HTTP:** httpx (Cliente assíncrono).

### Frontend (Interface de Usuário)

* **Linguagem:** TypeScript (com muito auxílio do _Gemini_ para compensar a falta de conhecimento de frontend do autor)
* **Framework:** React 19 executado sobre o *bundler* Vite.
* **Estilização:** Tailwind CSS v4.
* **Gerenciamento de Estado de Servidor:** TanStack React Query v5 (Cache dinâmico e revalidação de dados).
* **Visualização de Dados:** * Recharts (Séries Temporais).
* Nivo (Scatterplot e Boxplot com injeção de SVGs matemáticos customizados).
* **Renderização de Texto:** React-Markdown com suporte a tipografia matemática via KaTeX (`rehype-katex`, `remark-math`).


### Banco de Dados

* **PostgreSQL 17** (containerizado em Alpine Linux)

### Infraestrutura e DevOps

* **Containerização:** Docker e Docker Compose.
* **Servidor Web / Proxy Reverso:** Nginx.
---

## 3. Estrutura de Diretórios e Componentes

### 3.1. Diretório `src/`

Responsável por toda a lógica de negócios, acesso a dados e roteamento.

#### `api/routers/`

* `dashboard.py`: Router principal do sistema. Expõe os *endpoints* consumidos pelo *frontend*. Orquestra a injeção de dependências e delega o processamento pesado aos serviços competentes, garantindo que a camada HTTP permaneça limpa e focada em I/O. Herda dependências do FastAPI de `main.py`

#### `core/`

* `database.py`: Instanciação da *Engine* assíncrona do SQLAlchemy e configuração da fábrica de sessões (`AsyncSessionLocal`). Acessos ao banco de dados devem importar esse objeto e usá-lo com: `async with`

* `logger.py`: Configuração unificada do log do sistema, padronizando a saída (stdout) para facilidade de auditoria e monitoramento em *containers*.

* `repository.py`: Padrão de repositório (*Repository Pattern*) que abstrai as queries SQL brutas, permitindo operações CRUD no banco de dados de forma desacoplada da Lógica de negócios. Possui o método `fetch_as_polars`, que padroniza a forma de manipular e disponibilizar os dados da query para o endpoint.

#### `models/`

* `market.py`: Modelos declarativos do SQLAlchemy. Define o esquema rigoroso das tabelas do banco de dados relacional (PostgreSQL), mapeando tipos SQL para tipos Python.

#### `schemas/`

* `market.py`: Contratos de validação do Pydantic. Assegura que todos os dados que entram (requisições) e saem (respostas JSON) da API estejam rigorosamente tipados, prevenindo erros em tempo de execução.

#### `services/`

A camada mais densa do sistema, contendo as regras de negócio e a matemática.

* `analytics.py`: Motor de agregações. Converte registros do banco para `Polars DataFrame`, trata dados ausentes (*drop_nulls*) e calcula métricas como log-retorno, volatilidade estatística e Média Móvel Exponencial (EMA).

* `db_upsert.py`: Lógica de persistência. Gerencia o comando `INSERT ON CONFLICT DO UPDATE` (Upsert), garantindo que a ingestão de preços intradiários não crie duplicatas de chave primária (*timestamp* + *ticker*).

* `fetch_yahoo.py`: Cliente de extração de dados brutos. Conecta-se à API V8 (Chart) do Yahoo Finance utilizando chamadas HTTP assíncronas e estruturando os retornos JSON em listas de dicionários padronizadas, considerando as idiossincrasias do *Call de Fechamento* da B3.

* `llm.py`: Conexão com o Grande Modelo de Língua (LLM) que vai gerar a análise qualitativa. Contém a classe `AnalistaQualitativo`. Emprega engenharia de *prompts* estritos. Implementa captura de notícias em tempo real via RSS (evitando bloqueios do *Google Grounding*) e gerencia *Rate Limits* através de algoritmos de *Exponential Backoff*.

* `macro_eco.py`: Serviço de comunicação com APIs governamentais (como o Banco Central do Brasil) para extração da meta da Taxa Selic e do IPCA acumulado (12 meses).

* `ml.py`: Algoritmos de Machine Learning não-supervisionado. Aplica Padronização (`StandardScaler`) aos dados de risco-retorno e executa o algoritmo *K-Means* dinamicamente. Calcula o *Silhouette Score* para aferir a qualidade da separação topológica dos *clusters*. Adicionalmente constrói a Matriz de Correlação de Pearson da carteira.

* `scheduler.py`: Motor de rotinas autônomas. Configura a arquitetura *Cron* do APScheduler para disparar o `fetch_yahoo.py` a cada 15 minutos, respeitando o fuso horário da B3 e aplicando o padrão *Semaphore* (limitação de concorrência) para evitar bloqueio de IP.

#### Raiz do Backend

* `main.py`: O ponto de entrada da aplicação (`Entrypoint`). Inicializa o *FastAPI*, gerencia os eventos de ciclo de vida (*startup/shutdown*) acionando o *scheduler* e o `ProcessPoolExecutor` para taferas computacionalmente intensas

* `Dockerfile`: Declaração de imagem baseada em Python *slim*, gerenciando a instalação segura do ecossistema e definindo o servidor Uvicorn.

* `requirements.in` / `requirements.txt`: Rastreabilidade determinística de dependências Python com uv pip, para garantir versões de dependências e das dependências das dependências.

### 3.2. Diretório `frontend/`

A aplicação *Single Page Application* reativa.

#### `src/pages/`

* `DashboardMacro.tsx`: Tela inicial. Consolida os KPIs macroeconômicos e realiza o cálculo matemático contínuo da Equação de Fisher em memória RAM para obtenção do Juro Real ($Juro Real = \left( \frac{1 + i}{1 + \pi} \right) - 1$). Inclui a barra de pesquisa rápida por *regex*/filtro e o gráfico paramétrico da Média Móvel Exponencial (Recharts). Também renderiza a resposta da IA (LLM) utilizando motores de conversão Markdown/LaTeX.

* `DashboardML.tsx`: Painel de inteligência quantitativa. Expõe hiperparâmetros ajustáveis para o *K-Means*. Utiliza o Nivo para a plotagem do espaço bidimensional Risco vs. Retorno, implementando uma camada customizada SVG (`EllipseLayer`) que calcula centroides e matriz de dispersão na interface gráfica. Inclui análises distribucionais baseadas em Boxplots estatísticos interativos.

#### `src/api/` e Root

* `client.ts`: Instância isolada do Axios para roteamento seguro de API.

* `App.tsx`: Gerenciador de contexto e estado global da aplicação. Hospeda o controle temporal base (Data de Início/Fim) e o fluxo de transição entre abas da SPA, passando estados via *Props* nativas do React.
* `index.html`: *Template* injetável do Vite, com meta-tags otimizadas.
* `package.json`: Manifesto determinístico de ecossistema Node.js para garantir reprodutibilidade irrestrita em múltiplos sistemas operacionais.

### 3.3. Infraestrutura (`/nginx` e Docker)

* `nginx.conf`: Configuração do servidor *Proxy Reverso*. Otimiza a entrega estática dos artefatos JavaScript/CSS compilados pelo Vite e encaminha requisições da rota `/api` internamente para a porta 8000 do *container* FastAPI no *backend*, solucionando impasses de CORS nativamente via rede local Docker.

* `docker-compose.yml`: Topologia da infraestrutura. Levanta simultaneamente o banco PostgreSQL persistente (com *volumes* mapeados), o ambiente Python com Uvicorn e o nó Nginx servindo a compilação do React.

---

## 4. Endpoints e Rotas da API

Todas as rotas partem do prefixo `/api` no Nginx, redirecionado ao roteador interno `/dashboard-ativos/`.

* `GET /kpis-macro`: Retorna métricas macroeconômicas instantâneas (Selic, IPCA). Resposta em taxa percentual bruta.

* `GET /resumo`: Recebe os parâmetros `dt_inicio` e `dt_fim`. Retorna uma matriz de variação de preços logarítmicos e absolutos para todo o *pool* de ativos.

* `GET /series`: Endpoint analítico. Recebe `dt_inicio`, `dt_fim`, `ativos` (String tipada) e `janela` (Int). Retorna a série temporal purificada com o fechamento ajustado e o cálculo do vetor de EMA respectivo à janela solicitada.

* `GET /machine-learning`: Recebe período temporal e `n_clusters` (K do K-Means). Retorna matrizes de espalhamento bidimensional, métricas de *Silhouette* e Matriz de Correlação cruzada.

* `GET /analise-qualitativa`: Recebe cenário quantitativo consolidado, ativo alvo e matriz macro. Retorna uma `String` processada por Modelos Fundacionais (LLMs) com *web scraping* interno anexado.

## 5. Pipeline de Dados e Ingestão

O fluxo de dados da aplicação obedece a um rito temporal voltado para a bolsa brasileira (B3).

O módulo `scheduler.py` contém rotinas agendadas (CRON) configuradas para execução exclusiva entre 10h e 17h, ignorando finais de semana. A arquitetura de extração intradiária assíncrona captura micro-tendências em velas (candles) de 5 minutos.

A arquitetura garante imunidade matemática ao *Call de Fechamento* das 16h55 às 17h00 da B3, ignorando o leilão em formação para evitar anomalias de volatilidade espúria no cálculo dos desvios padrões do espaço latente da aplicação (Scikit-Learn). O banco de dados relacional é garantido contra duplicidade através das *Constraints* no nível de repositório.

## 6. Integração com Inteligência Artificial (LLM)

O sistema utiliza os modelos fundacionais de alta latência do Google (Série Flash) acoplados sob a perspectiva de um Engenheiro Quantitativo. Para contornar as limitações de cota rígida (limites de RPM/TPM - Erro `429 RESOURCE_EXHAUSTED`), implementamos os seguintes protocolos:

1. **Bypass de Grounding via Web Scraping:** Desacoplamos a ferramenta nativa de buscas da Google (que eleva drasticamente o consumo do modelo) em favor de um raspador de RSS limpo via Python nativo. Os textos brutos de mercado alimentam diretamente o *prompt* do LLM no contêiner.

2. **Resiliência e Timeout:** Implementação mandatória de tentativa/erro (*try-catch* com *loop* paramétrico), garantindo o *Exponential Backoff* (espera gradual de 2s, 4s, 8s) se o gargalo da camada de API externa rejeitar a conexão.

3. **Graceful Degradation:** Em cenário de total inviabilidade da API remota, a função entrega estritamente um texto de aviso estruturado ao *frontend*, mantendo os painéis estatísticos, *pipelines* de dados e gráficos operando com rigor analítico absoluto e sem impacto na experiência de navegação (ausência de *White Screens of Death*).