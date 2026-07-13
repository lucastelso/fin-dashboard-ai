# backend/services/llm.py
import os
import json
from google import genai
from google.genai import types
from core.logger import logger
from typing import List

class AnalistaQualitativo:
    """
    IA GENERATIVA para síntese de mercado. 
    Usa o Gemini com Grounding (Busca no Google) para cruzar dados matemáticos com notícias do mundo real.
    """
    def __init__(self):
        self.client = genai.Client()
        self.modelo = "gemini-2.5-flash"

    def gerar_sintese(
            self, 
            dt_inicio: str, 
            dt_fim: str, 
            dados_quant: dict, 
            kpis_macro: dict,
            ativos_alvo: List[str] # Adicionado para direcionar a busca da IA
        ) -> str:
        """
        Gera o prompt otimizado em tokens focado nos ativos selecionados e aciona a API do Gemini.
        """
        # ENGENHARIA DE PROMPT (Foco Cirúrgico nos Ativos Alvo)
        prompt = f"""
        Você é um analista quantitativo e macroeconômico sênior atuando no mercado brasileiro.
        Analise o comportamento do mercado brasileiro entre {dt_inicio} e {dt_fim}, focando especificamente nestes ativos: {', '.join(ativos_alvo)}.

        [CONTEXTO MACROECONÔMICO]
        - Taxa Selic Atual: {kpis_macro.get('selic', 'N/A')}%
        - IPCA (12m): {kpis_macro.get('ipca', 'N/A')}%

        [DADOS QUANTITATIVOS DOS ATIVOS SELECIONADOS]
        Aqui estão as métricas consolidadas (Retorno Acumulado e Volatilidade) para as ações analisadas:
        {json.dumps(dados_quant, indent=2)}

        [SUA TAREFA]
        1. Avalie o desempenho dos ativos informados com base nos dados quantitativos fornecidos.
        2. UTILIZE A BUSCA DO GOOGLE para rastrear fatos relevantes, relatórios de resultados, decisões políticas ou dinâmicas de commodities que impactaram DIRETAMENTE essas empresas ({', '.join(ativos_alvo)}) entre as datas {dt_inicio} e {dt_fim}.
        3. Escreva um relatório executivo conciso, de 2 a 3 parágrafos, conectando os dados matemáticos aos eventos reais de mercado. Seja extremamente técnico, objetivo e direto ao ponto, sem preâmbulos ou conclusões genéricas.
        """

        try:
            logger.info(f"Acionando Gemini para síntese focada em {len(ativos_alvo)} ativos com Google Grounding...")
            
            response = self.client.models.generate_content(
                model=self.modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                    temperature=0.2 # Reduzido para maior aderência factual e menor variabilidade
                )
            )
            return response.text if response.text else "O modelo não retornou uma análise válida (possível bloqueio de segurança nos dados)."
            
        except Exception as e:
            logger.error(f"Falha na comunicação com o Gemini: {e}")
            return "Indisponibilidade momentânea no motor de síntese qualitativa. Tente novamente mais tarde."