# backend/services/llm.py
import os
import time
import urllib.request
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types
from google.genai.errors import APIError

from fin_dashboard.core.logger import logger

class AnalistaQualitativo:
    def __init__(self):
        self.client = genai.Client()
        self.modelo = "gemini-3.5-flash"

    def _buscar_noticias_recentes(self, ticker: str) -> str:
        """
        Bypass de Grounding: Busca notícias recentes do ativo via RSS do Google News
        sem consumir cota da API do Gemini.
        """
        logger.info(f"Buscando notícias recentes via Web Scraper para o ativo {ticker}...")
        try:
            # URL do RSS do Google News focado no ticker do ativo
            url = f"https://news.google.com/rss/search?q={ticker}+mercado+financeiro&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
            
            # Parseia o XML do RSS
            root = ET.fromstring(xml_data)
            noticias = []
            
            # Captura as 5 notícias mais recentes relevantes
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text if item.find('title') is not None else "" # type: ignore
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "" # type: ignore
                noticias.append(f"- {title} (Publicado em: {pub_date})")
            
            if noticias:
                logger.info("Noticias encontras. Jutando e repassando ao modelo")
                return "\n".join(noticias)
            return "Nenhuma notícia relevante encontrada nas últimas horas."
            
        except Exception as e:
            logger.warning(f"Falha ao obter notícias externas para o prompt: {e}")
            return "Não foi possível obter notícias em tempo real devido a oscilações no servidor de feed."

    def gerar_sintese(self, dt_inicio: str, dt_fim: str, dados_quant: list, kpis_macro: dict, ativos: list | str) -> str:
        ativos_str = ", ".join(ativos) if isinstance(ativos, list) else ativos
        
        # Faz o Grounding na camada de aplicação (Web scraping leve)
        noticias_mercado = self._buscar_noticias_recentes(ativos_str)

        logger.info(f"Acionando Gemini para síntese focada no(s) ativo(s) {ativos_str}...")

        # Injeta as notícias raspadas diretamente no contexto do prompt
        prompt = f"""
        Atue como um Analista Quantitativo e Estrategista de Alocação sênior.
        Analise estritamente os seguintes dados financeiros consolidados de {dt_inicio} a {dt_fim}:

        KPIs Macroeconômicos Globais:
        {kpis_macro}

        Série e Métricas do Ativo Analisado:
        {dados_quant}

        Identificador do Ativo: {ativos_str}

        Notícias Recentes Coletadas na Web sobre {ativos_str}:
        {noticias_mercado}

        Instruções operacionais:
        1. Cruze a volatilidade e o retorno do ativo com o cenário macroeconômico (Selic e IPCA).
        2. Correlacione os movimentos matemáticos observados com as notícias coletadas na web sobre o ativo.
        3. Escreva uma síntese executiva extremamente densa, limpa, sem introduções vazias ou obviedades textuais. Vá direto aos fundamentos de risco e retorno.
        """

        # Configuração pura, sem tools (Bypassa o limitador do Free Tier do Google)
        config = types.GenerateContentConfig(
            temperature=0.15
        )

        max_tentativas = 3
        tempo_espera = 2

        for tentativa in range(max_tentativas):
            try:
                resposta = self.client.models.generate_content(
                    model=self.modelo,
                    contents=prompt,
                    config=config
                )
                return resposta.text if resposta.text else "O modelo não retornou uma análise válida (possível bloqueio de segurança nos dados)."

            except APIError as e:
                if e.code == 429:
                    logger.warning(f"Rate limit atingido. Tentativa {tentativa + 1}/{max_tentativas}. Aguardando {tempo_espera}s...")
                    time.sleep(tempo_espera)
                    tempo_espera *= 2
                else:
                    logger.error(f"Falha no Gateway da API: {e}")
                    raise e
            except Exception as e:
                logger.error(f"Erro inesperado: {e}")
                raise e

        return "Aviso: Limite de requisições por minuto do motor de IA atingido."