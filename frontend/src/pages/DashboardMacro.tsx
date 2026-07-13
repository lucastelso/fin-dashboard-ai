import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Activity, TrendingUp, BarChart3, Calendar, BrainCircuit, Loader2 } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

// Dicionário Estático para mapear Tickers para Nomes Legíveis (Frontend Pattern)
const DICIONARIO_ATIVOS: Record<string, string> = {
  "PETR4.SA": "Petrobras PN", "PETR3.SA": "Petrobras ON", "VALE3.SA": "Vale ON",
  "ITUB4.SA": "Itaú Unibanco PN", "BBDC4.SA": "Bradesco PN", "BBDC3.SA": "Bradesco ON",
  "BBAS3.SA": "Banco do Brasil ON", "ABEV3.SA": "Ambev ON", "WEGE3.SA": "WEG ON",
  "SUZB3.SA": "Suzano ON", "RENT3.SA": "Localiza ON", "B3SA3.SA": "B3 ON",
  "RADL3.SA": "RaiaDrogasil ON", "JBSS3.SA": "JBS ON", "BPAC11.SA": "BTG Pactual Unit",
  "EQTL3.SA": "Equatorial ON", "VIVT3.SA": "Vivo PN", "RAIL3.SA": "Rumo ON",
  "SBSP3.SA": "Sabesp ON", "PRIO3.SA": "Prio ON", "BBSE3.SA": "BB Seguridade ON",
  "GGBR4.SA": "Gerdau PN", "CSNA3.SA": "CSN ON", "IVVB11.SA": "S&P 500 ETF", 
  "LVOL11.SA": "Low Volatility ETF", "DIVO11.SA": "Dividendos ETF", "BOVA11.SA": "Ibovespa ETF"
};

export default function DashboardMacro() {
  const [dataInicio, setDataInicio] = useState('2026-07-01');
  const [dataFim, setDataFim] = useState('2026-07-10');
  const [ativoSelecionado, setAtivoSelecionado] = useState('BOVA11.SA'); // Ibovespa como default

  // 1. Fetcher Macro
  const { data: kpiData } = useQuery({
    queryKey: ['kpis-macro'],
    queryFn: async () => (await apiClient.get('/dashboard-ativos/kpis-macro')).data,
  });

  // 2. Fetcher Resumo (Tabela)
  const { data: resumoData, isLoading: resumoLoading } = useQuery({
    queryKey: ['resumo-mercado', dataInicio, dataFim],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard-ativos/resumo', { params: { dt_inicio: dataInicio, dt_fim: dataFim } });
      return res.data.dados;
    },
  });

  // 3. Fetcher Série Temporal (Gráfico)
  const { data: serieData, isLoading: serieLoading } = useQuery({
    queryKey: ['serie-temporal', dataInicio, dataFim, ativoSelecionado],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard-ativos/series', {
        params: { dt_inicio: dataInicio, dt_fim: dataFim, ativos: [ativoSelecionado], janela: 20 }
      });
      return res.data.dados;
    },
  });

  // 4. Fetcher IA Qualitativa (Acionado apenas via botão)
  const { refetch: fetchIA, data: iaData, isFetching: iaLoading } = useQuery({
    queryKey: ['ia-analise', dataInicio, dataFim, ativoSelecionado],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard-ativos/analise-qualitativa', {
        params: { dt_inicio: dataInicio, dt_fim: dataFim, ativos: [ativoSelecionado] }
      });
      return res.data.texto_analise;
    },
    enabled: false, // Impede o auto-fetch
  });

  return (
    <div className="min-h-screen bg-slate-950 p-8 font-sans text-slate-100">
      {/* HEADER */}
      <header className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Dashboard Financeiro Inteligente</h1>
          <p className="text-slate-400 mt-1">Visão Macro e Análise de Rentabilidade</p>
        </div>
        
        <div className="flex items-center gap-3 bg-slate-900 p-2 rounded-lg shadow-sm border border-slate-800">
          <Calendar className="w-5 h-5 text-slate-500 ml-2" />
          <input 
            type="date" 
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="bg-transparent border-none focus:ring-0 text-sm font-medium text-slate-300 outline-none" style={{colorScheme: 'dark'}}
          />
          <span className="text-slate-600">até</span>
          <input 
            type="date" 
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="bg-transparent border-none focus:ring-0 text-sm font-medium text-slate-300 outline-none pr-2" style={{colorScheme: 'dark'}}
          />
        </div>
      </header>

      {/* CARDS KPI */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Taxa Selic Meta</p>
            <h3 className="text-2xl font-bold text-white">{kpiData ? `${kpiData.selic}%` : '...'}</h3>
          </div>
        </div>
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">IPCA (12m)</p>
            <h3 className="text-2xl font-bold text-white">{kpiData ? `${kpiData.ipca}%` : '...'}</h3>
          </div>
        </div>
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Ativos Rastreados</p>
            <h3 className="text-2xl font-bold text-white">{resumoData?.length || 0}</h3>
          </div>
        </div>
      </div>

      {/* ÁREA CENTRAL: Tabela e Gráfico */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        
        {/* Tabela de Ativos */}
        <div className="lg:col-span-1 bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col h-[500px]">
          <h2 className="text-lg font-bold text-white mb-4">Performance dos Ativos</h2>
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
                  {resumoData?.map((item: any) => (
                    <tr 
                      key={item.ativo} 
                      onClick={() => setAtivoSelecionado(item.ativo)}
                      className={`cursor-pointer transition-colors ${ativoSelecionado === item.ativo ? 'bg-slate-800/80' : 'hover:bg-slate-800/40'}`}
                    >
                      <td className="py-3 px-2">
                        <div className="font-bold text-slate-200">{item.ativo}</div>
                        <div className="text-xs text-slate-500">{DICIONARIO_ATIVOS[item.ativo] || 'Empresa B3'}</div>
                      </td>
                      <td className={`py-3 px-2 text-right font-bold ${item.variacao_percentual >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {item.variacao_percentual > 0 ? '+' : ''}{item.variacao_percentual}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

{/* Gráfico Recharts */}
        <div className="lg:col-span-2 bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col h-[500px]">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-white">Série Temporal: {ativoSelecionado}</h2>
              <p className="text-sm text-slate-500">Preço vs Média Móvel Exponencial (20 períodos)</p>
            </div>
          </div>
          
          {/* A correção do Flexbox está no min-h-0 e altura 100% explícita */}
          <div className="flex-1 w-full min-h-0">
            {serieLoading ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-slate-600" />
              </div>
            ) : !serieData || serieData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-slate-500">
                Sem dados suficientes para gerar a série neste período.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={serieData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis 
                    dataKey="data" 
                    stroke="#64748b" 
                    tick={{ fontSize: 12 }} 
                    /* Proteção: Garante que é string antes de dar split */
                    tickFormatter={(val) => val ? String(val).split(' ')[0] : ''} 
                    minTickGap={30} 
                  />
                  <YAxis 
                    domain={['auto', 'auto']} 
                    stroke="#64748b" 
                    tick={{ fontSize: 12 }} 
                    /* Proteção: Garante que é número e formata com 2 casas */
                    tickFormatter={(val) => `R$ ${Number(val).toFixed(2)}`} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc', borderRadius: '8px' }}
                    labelFormatter={(label) => `Data: ${label}`}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Line type="monotone" dataKey="fechamento" stroke="#3b82f6" strokeWidth={2} dot={false} name="Preço" />
                  <Line type="monotone" dataKey="ema_20" stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="5 5" name="EMA (20)" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* MÓDULO IA */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <BrainCircuit className="w-6 h-6 text-purple-400" />
            <h2 className="text-lg font-bold text-white">Síntese Qualitativa (Gemini 3.5 Flash)</h2>
          </div>
          <button 
            onClick={() => fetchIA()}
            disabled={iaLoading}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-800 disabled:text-slate-500 text-white px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer"
          >
            {iaLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Gerar Análise do Ativo'}
          </button>
        </div>
        
        <div className="bg-slate-950 rounded-lg p-5 border border-slate-800 min-h-[120px]">
          {iaLoading ? (
            <div className="animate-pulse flex space-x-4">
              <div className="flex-1 space-y-4 py-1">
                <div className="h-2 bg-slate-800 rounded w-3/4"></div>
                <div className="h-2 bg-slate-800 rounded"></div>
                <div className="h-2 bg-slate-800 rounded w-5/6"></div>
              </div>
            </div>
          ) : iaData ? (
            <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
              {iaData}
            </div>
          ) : (
            <p className="text-slate-500 italic text-sm">
              Clique no botão acima para cruzar a matemática do ativo selecionado com notícias da internet em tempo real.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}