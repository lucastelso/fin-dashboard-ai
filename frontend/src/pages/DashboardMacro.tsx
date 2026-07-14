import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Activity, TrendingUp, BarChart3, BrainCircuit, Loader2, Search } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

const DICIONARIO_ATIVOS: Record<string, string> = {
  "PETR4.SA": "Petrobras PN", "PETR3.SA": "Petrobras ON", "VALE3.SA": "Vale ON",
  "ITUB4.SA": "Itaú Unibanco PN", "BBDC4.SA": "Bradesco PN", "BBDC3.SA": "Bradesco ON",
  "BBAS3.SA": "Banco do Brasil ON", "ABEV3.SA": "Ambev ON", "WEGE3.SA": "WEG ON",
  "SUZB3.SA": "Suzano ON", "RENT3.SA": "Localiza ON", "B3SA3.SA": "B3 ON",
  "RADL3.SA": "RaiaDrogasil ON", "JBSS3.SA": "JBS ON", "BPAC11.SA": "BTG Pactual Unit",
  "EQTL3.SA": "Equatorial ON", "VIVT3.SA": "Vivo PN", "RAIL3.SA": "Rumo ON",
  "SBSP3.SA": "Sabesp ON", "PRIO3.SA": "Prio ON", "BBSE3.SA": "BB Seguridade ON",
  "GGBR4.SA": "Gerdau PN", "CSNA3.SA": "CSN ON", "IVVB11.SA": "S&P 500 ETF", 
  "LVOL11.SA": "Low Volatility ETF", "DIVO11.SA": "Dividendos ETF", "BOVA11.SA": "Ibovespa ETF",
  "UGPA3.SA": "Ultrapar","CMIG4.SA": "Cemig", "CSAN3.SA": "Cosan","HYPE3.SA": "Hypera Pharma",
  "ENEV3.SA": "Eneva", "TIMS3.SA": "TIM", "TOTS3.SA": "TOTVS", "EGIE3.SA": "Engie Brasil",
  "KLBN11.SA": "Klabin",
  "ALPA4.SA": "Alpargatas",
  "SMAL11.SA": "iShares Small Cap ETF",
  "AZZA3.SA": "Azzas 2154",
  "BRAP4.SA": "Bradespar",
  "BRFS3.SA": "BRF",
  "BRKM5.SA": "Braskem",
  "CCRO3.SA": "CCR",
  "CPLE6.SA": "Copel",
  "CVCB3.SA": "CVC Brasil",
  "CYRE3.SA": "Cyrela",
  "ECOR3.SA": "EcoRodovias",
  "ELET3.SA": "Eletrobras",
  "EMBR3.SA": "Embraer",
  "ENGI11.SA": "Energisa",
  "EZTC3.SA": "EZTEC",
  "FLRY3.SA": "Fleury",
  "GOAU4.SA": "Metalúrgica Gerdau",
  "HAPV3.SA": "Hapvida",
  "IRBR3.SA": "IRB Brasil",
  "ITSA4.SA": "Itaúsa",
  "LREN3.SA": "Lojas Renner",
  "MGLU3.SA": "Magazine Luiza",
  "MRVE3.SA": "MRV",
  "MULT3.SA": "Multiplan",
  "NTCO3.SA": "Natura &Co",
  "SANB11.SA": "Santander Brasil",
  "TAEE11.SA": "Taesa",
  "USIM5.SA": "Usiminas",
  "VBBR3.SA": "Vibra Energia"
};

interface DashboardMacroProps {
  dataInicio: string;
  dataFim: string;
}

export default function DashboardMacro({ dataInicio, dataFim }: DashboardMacroProps) {
  const [ativoSelecionado, setAtivoSelecionado] = useState('BOVA11.SA');
  const [janelaEma, setJanelaEma] = useState(20);
  const [termoBusca, setTermoBusca] = useState('');

  const { data: kpiData } = useQuery({
    queryKey: ['kpis-macro'],
    queryFn: async () => (await apiClient.get('/dashboard-ativos/kpis-macro')).data,
  });

  const { data: resumoData, isLoading: resumoLoading } = useQuery({
    queryKey: ['resumo-mercado', dataInicio, dataFim],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard-ativos/resumo', { params: { dt_inicio: dataInicio, dt_fim: dataFim } });
      return res.data.dados;
    },
  });

  const { data: serieData, isLoading: serieLoading } = useQuery({
    queryKey: ['serie-temporal', dataInicio, dataFim, ativoSelecionado, janelaEma],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard-ativos/series', {
        params: { dt_inicio: dataInicio, dt_fim: dataFim, ativos: ativoSelecionado, janela: janelaEma }
      });
      return res.data.dados;
    },
  });

  const { refetch: fetchIA, data: iaData, isFetching: iaLoading } = useQuery({
    queryKey: ['ia-analise', dataInicio, dataFim, ativoSelecionado],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard-ativos/analise-qualitativa', {
        params: { dt_inicio: dataInicio, dt_fim: dataFim, ativos: ativoSelecionado }
      });
      return res.data.texto_analise;
    },
    enabled: false, 
  });

  // Motor de busca em memória RAM (Case Insensitive) para Ticker e Nome
  const ativosFiltrados = resumoData?.filter((item: any) => {
    const nomeEmpresa = DICIONARIO_ATIVOS[item.ativo] || '';
    const termo = termoBusca.toLowerCase();
    return (
      item.ativo.toLowerCase().includes(termo) || 
      nomeEmpresa.toLowerCase().includes(termo)
    );
  }) || [];

  // INJEÇÃO MATEMÁTICA: Cálculo do Juro Real ex-post (Equação de Fisher)
  const selicDecimal = kpiData?.selic ? kpiData.selic / 100 : 0;
  const ipcaDecimal = kpiData?.ipca ? kpiData.ipca / 100 : 0;
  const juroReal = kpiData ? (((1 + selicDecimal) / (1 + ipcaDecimal)) - 1) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* KPIs Macro (Expandido para 4 colunas) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg"><Activity className="w-6 h-6" /></div>
          <div><p className="text-sm font-medium text-slate-400">Taxa Selic Meta</p><h3 className="text-2xl font-bold text-white">{kpiData ? `${kpiData.selic}%` : '...'}</h3></div>
        </div>
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg"><TrendingUp className="w-6 h-6" /></div>
          <div><p className="text-sm font-medium text-slate-400">Inflação (IPCA 12m)</p><h3 className="text-2xl font-bold text-white">{kpiData ? `${kpiData.ipca}%` : '...'}</h3></div>
        </div>
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg"><Activity className="w-6 h-6" /></div>
          <div><p className="text-sm font-medium text-slate-400">Juro Real (Prêmio de Risco)</p><h3 className="text-2xl font-bold text-white">{kpiData ? `${juroReal.toFixed(2)}%` : '...'}</h3></div>
        </div>
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg"><BarChart3 className="w-6 h-6" /></div>
          <div><p className="text-sm font-medium text-slate-400">Ativos Rastreados</p><h3 className="text-2xl font-bold text-white">{resumoData?.length || 0}</h3></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Painel Esquerdo: Busca e Tabela */}
        <div className="lg:col-span-1 bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col h-[500px]">
          <h2 className="text-lg font-bold text-white mb-3">Performance dos Ativos</h2>
          
          <div className="flex items-center gap-2 mb-4 bg-slate-950 px-3 py-2 rounded-lg border border-slate-800">
            <Search className="w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              placeholder="Buscar ativo ou empresa..." 
              value={termoBusca}
              onChange={(e) => setTermoBusca(e.target.value)}
              className="bg-transparent border-none text-sm text-slate-200 outline-none w-full placeholder-slate-600 focus:ring-0"
            />
          </div>

          <div className="overflow-y-auto flex-1 pr-2 custom-scrollbar">
            {resumoLoading ? <p className="text-slate-500">Buscando dados...</p> : (
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900 sticky top-0 border-b border-slate-800 z-10">
                  <tr>
                    <th className="py-3 px-2 font-medium text-slate-500">Ativo</th>
                    <th className="py-3 px-2 font-medium text-slate-500 text-right">Variação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {ativosFiltrados.map((item: any) => (
                    <tr key={item.ativo} onClick={() => setAtivoSelecionado(item.ativo)} className={`cursor-pointer transition-colors ${ativoSelecionado === item.ativo ? 'bg-slate-800/80' : 'hover:bg-slate-800/40'}`}>
                      <td className="py-3 px-2"><div className="font-bold text-slate-200">{item.ativo}</div><div className="text-xs text-slate-500">{DICIONARIO_ATIVOS[item.ativo] || 'Empresa B3'}</div></td>
                      <td className={`py-3 px-2 text-right font-bold ${item.variacao_percentual >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{item.variacao_percentual > 0 ? '+' : ''}{item.variacao_percentual}%</td>
                    </tr>
                  ))}
                  {ativosFiltrados.length === 0 && (
                    <tr>
                      <td colSpan={2} className="py-8 text-center text-slate-500 text-sm">Nenhum ativo encontrado.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Painel Direito: Série Temporal com EMA Dinâmica */}
        <div className="lg:col-span-2 bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col h-[500px]">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-white">Série Temporal: {ativoSelecionado}</h2>
              <p className="text-sm text-slate-500">Preço vs Média Móvel Exponencial</p>
            </div>
            
            <div className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-lg border border-slate-800">
              <label className="text-xs text-slate-400 font-medium ml-2">Períodos (EMA):</label>
              <input 
                type="number" min="2" max="50"
                value={janelaEma} 
                onChange={(e) => setJanelaEma(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 rounded p-1 w-14 text-sm text-center text-white outline-none focus:border-blue-500" 
              />
            </div>
          </div>
          
          <div className="flex-1 w-full min-h-0">
            {serieLoading ? (
              <div className="flex h-full items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-slate-600" /></div>
            ) : !serieData || serieData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-slate-500">Sem dados suficientes (Aumente o filtro de data para a EMA).</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={serieData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="data" stroke="#64748b" tick={{ fontSize: 12 }} tickFormatter={(val) => val ? String(val).split(' ')[0] : ''} minTickGap={30} />
                  <YAxis domain={['auto', 'auto']} stroke="#64748b" tick={{ fontSize: 12 }} tickFormatter={(val) => `R$ ${Number(val).toFixed(2)}`} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc', borderRadius: '8px' }} labelFormatter={(label) => `Data: ${label}`} />
                  <Legend verticalAlign="top" height={36} />
                  <Line type="monotone" dataKey="fechamento" stroke="#3b82f6" strokeWidth={2} dot={false} name="Preço" />
                  <Line type="monotone" dataKey={`ema_${janelaEma}`} stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="5 5" name={`EMA (${janelaEma})`} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Módulo de Inteligência Artificial */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <BrainCircuit className="w-6 h-6 text-purple-400" />
            <h2 className="text-lg font-bold text-white">Síntese Qualitativa (Gemini)</h2>
          </div>
          <button onClick={() => fetchIA()} disabled={iaLoading} className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-800 disabled:text-slate-500 text-white px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer">
            {iaLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Gerar Análise do Ativo'}
          </button>
        </div>
        <div className="bg-slate-950 rounded-lg p-5 border border-slate-800 min-h-[120px]">
          {iaLoading ? (
             <p className="text-slate-400">Processando cruzamento de dados com eventos recentes do mercado...</p>
        ) : iaData ? (
            <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {iaData}
              </ReactMarkdown>
            </div>
        ) : (
            <p className="text-slate-500 italic text-sm">Clique no botão para cruzar a matemática do ativo com notícias em tempo real.</p>
          )}
        </div>
      </div>
    </div>
  );
}