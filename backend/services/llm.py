# backend/services/llm.py
import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from core.logger import logger

class AnalistaQualitativo:
    def __init__(self):
        # Inicializa o cliente usando o padrão unificado da SDK atual
        self.client = genai.Client()
        # Modelo de última geração validado empiricamente no cluster
        self.modelo = "gemini-3.5-flash"

    def gerar_sintese(self, dt_inicio: str, dt_fim: str, dados_quant: list, kpis_macro: dict, ativos: list | str) -> str:
        # Normalização: Se chegar como lista, planifica para string separada por vírgulas
        ativos_str = ", ".join(ativos) if isinstance(ativos, list) else ativos
        
        logger.info(f"Acionando Gemini para síntese focada no(s) ativo(s) {ativos_str} com Google Grounding...")

        # Prompt de Engenharia Quantitativa rigoroso e denso
        prompt = f"""
        Atue como um Analista Quantitativo e Estrategista de Alocação sênior.
        Analise estritamente os seguintes dados financeiros consolidados de {dt_inicio} a {dt_fim}:

        KPIs Macroeconômicos Globais:
        {kpis_macro}

        Série e Métricas do Ativo Analisado:
        {dados_quant}

        Identificador do Ativo: {ativos_str}

        Instruções operacionais:
        1. Cruze a volatilidade e o retorno do ativo com o cenário macroeconômico (Selic e IPCA).
        2. Utilize a busca do Google para correlacionar os movimentos matemáticos observados com fatos relevantes da empresa, divulgação de resultados trimestrais ou fatores geopolíticos/regulatórios no período.
        3. Escreva uma síntese executiva extremamente densa, limpa, sem introduções vazias ou obviedades textuais. Vá direto aos fundamentos de risco e retorno.
        """
        # Configuração do Grounding e controle de hiperparâmetros contra alucinação
        config = types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.15  # Baixa entropia para preservar o rigor matemático
        )

        # ARQUITETURA DE RESILIÊNCIA: RETRIES COM EXPONENTIAL BACKOFF
        max_tentativas = 4
        tempo_espera = 3  # Segundos iniciais de respiro para o cluster

        for tentativa in range(max_tentativas):
            try:
                resposta = self.client.models.generate_content(
                    model=self.modelo,
                    contents=prompt,
                    config=config
                )
                # Se obtiver sucesso, retorna imediatamente o relatório
                return resposta.text if resposta.text else "O modelo não retornou uma análise válida (possível bloqueio de segurança nos dados)."

            except APIError as e:
                # Captura o estouro de cota (Rate Limit)
                if e.code == 429:
                    logger.warning(
                        f"Rate limit atingido (429 RESOURCE_EXHAUSTED). "
                        f"Tentativa {tentativa + 1}/{max_tentativas}. "
                        f"Aplicando recuo exponencial de {tempo_espera}s..."
                    )
                    time.sleep(tempo_espera)
                    tempo_espera *= 2  # Dobra o tempo para a próxima janela
                else:
                    logger.error(f"Falha crítica controlada no Gateway da API: {e}")
                    raise e
            except Exception as e:
                logger.error(f"Erro inesperado no microsserviço de inteligência: {e}")
                raise e

        # GRACEFUL DEGRADATION: Se estourar todas as tentativas, não quebra o sistema
        logger.error("Exauridas todas as tentativas de bypass de cota do Free Tier do Google.")
        return (
            "Aviso: Limite de requisições por minuto do motor de IA temporariamente atingido. "
            "A análise fundamentalista baseada em notícias está congestionada no plano gratuito, "
            "mas os modelos quantitativos, séries temporais e clusters matemáticos continuam operando com total integridade."
        )