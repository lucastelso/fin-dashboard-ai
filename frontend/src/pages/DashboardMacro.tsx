import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Activity, TrendingUp, BarChart3, Calendar } from 'lucide-react';

export default function DashboardMacro() {
  // Estado global da tela (Filtro de Data)
  const [dataInicio, setDataInicio] = useState('2026-07-01');
  const [dataFim, setDataFim] = useState('2026-07-10');

  // Fetcher 1: KPIs Macroeconômicos (BCB)
  const { data: kpiData, isLoading: kpiLoading } = useQuery({
    queryKey: ['kpis-macro'],
    queryFn: async () => {
      const response = await apiClient.get('/dashboard-ativos/kpis-macro');
      return response.data;
    },
  });

  // Fetcher 2: Resumo Geral do Mercado (A Tabela)
  const { data: resumoData, isLoading: resumoLoading } = useQuery({
    queryKey: ['resumo-mercado', dataInicio, dataFim],
    queryFn: async () => {
      const response = await apiClient.get('/dashboard-ativos/resumo', {
        params: { dt_inicio: dataInicio, dt_fim: dataFim }
      });
      return response.data.dados;
    },
  });

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-900">
      {/* HEADER & FILTROS */}
      <header className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Inteligência de Mercado</h1>
          <p className="text-slate-500 mt-1">Visão Macro e Análise de Rentabilidade</p>
        </div>
        
        <div className="flex items-center gap-3 bg-white p-2 rounded-lg shadow-sm border border-slate-200">
          <Calendar className="w-5 h-5 text-slate-400 ml-2" />
          <input 
            type="date" 
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="bg-transparent border-none focus:ring-0 text-sm font-medium text-slate-700 outline-none"
          />
          <span className="text-slate-300">até</span>
          <input 
            type="date" 
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="bg-transparent border-none focus:ring-0 text-sm font-medium text-slate-700 outline-none pr-2"
          />
        </div>
      </header>

      {/* CARDS DE KPI */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Taxa Selic Meta</p>
            <h3 className="text-2xl font-bold">
              {kpiLoading ? '...' : `${kpiData?.selic}%`}
            </h3>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 flex items-center gap-4">
          <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">IPCA (12m)</p>
            <h3 className="text-2xl font-bold">
              {kpiLoading ? '...' : `${kpiData?.ipca}%`}
            </h3>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 flex items-center gap-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Ativos Rastreados</p>
            <h3 className="text-2xl font-bold">
              {resumoLoading ? '...' : resumoData?.length || 0}
            </h3>
          </div>
        </div>
      </div>

      {/* ÁREA INFERIOR: TABELA E GRÁFICO (WIP) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border border-slate-200 p-6 overflow-hidden flex flex-col h-[600px]">
          <h2 className="text-lg font-bold mb-4">Performance dos Ativos</h2>
          <div className="overflow-y-auto flex-1 pr-2">
            {resumoLoading ? (
              <p className="text-slate-500 text-sm">Carregando dados...</p>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 sticky top-0">
                  <tr>
                    <th className="py-2 px-3 font-medium text-slate-500">Ticker</th>
                    <th className="py-2 px-3 font-medium text-slate-500 text-right">Variação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {resumoData?.map((item: any) => (
                    <tr key={item.ativo} className="hover:bg-slate-50 cursor-pointer transition-colors">
                      <td className="py-3 px-3 font-semibold text-slate-700">{item.ativo}</td>
                      <td className={`py-3 px-3 text-right font-medium ${item.variacao_percentual >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {item.variacao_percentual > 0 ? '+' : ''}{item.variacao_percentual}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6 h-[600px] flex items-center justify-center">
          <p className="text-slate-400 font-medium">
            [ Área reservada para o Gráfico de Série Temporal (Recharts) ]
          </p>
        </div>
      </div>
    </div>
  );
}