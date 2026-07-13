import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Loader2, ScatterChart as ScatterIcon, Layers, Settings2 } from 'lucide-react';
import { ResponsiveScatterPlot } from '@nivo/scatterplot';
import { ResponsiveBoxPlot } from '@nivo/boxplot';

interface DashboardMLProps {
  dataInicio: string;
  dataFim: string;
}

// CAMADA BLINDADA: Cálculo de Covariância Visual para o Scatterplot
const EllipseLayer = (props: any) => {
  try {
    const { nodes } = props;
    // Se o React ou o Nivo chamarem essa camada vazia durante o carregamento, ignoramos.
    if (!nodes || !Array.isArray(nodes) || nodes.length === 0) return null;
    
    const grupos: Record<string, { points: any[], color: string }> = {};
    
    nodes.forEach((n: any) => {
      const clusterId = n.serieId || (n.data && n.data.serieId);
      if (!clusterId) return;
      
      if (!grupos[clusterId]) {
        grupos[clusterId] = { points: [], color: n.style?.color || n.color || '#6366f1' };
      }
      // O Nivo já nos entrega as posições "x" e "y" em pixels (na tela)
      grupos[clusterId].points.push({ x: n.x, y: n.y }); 
    });

    return Object.entries(grupos).map(([clusterId, { points, color }]) => {
      // É impossível desenhar uma elipse estatística com menos de 3 nós.
      if (points.length < 3) return null; 
      
      const cx = points.reduce((acc, p) => acc + p.x, 0) / points.length;
      const cy = points.reduce((acc, p) => acc + p.y, 0) / points.length;
      
      // Multiplicador 1.8x para a elipse abraçar os outliers de forma mais orgânica visualmente
      const rx = Math.sqrt(points.reduce((acc, p) => acc + Math.pow(p.x - cx, 2), 0) / points.length) * 1.8;
      const ry = Math.sqrt(points.reduce((acc, p) => acc + Math.pow(p.y - cy, 2), 0) / points.length) * 1.8;

      return (
        <ellipse
          key={clusterId}
          cx={cx}
          cy={cy}
          rx={rx || 15} // Fallback se os dados caírem exatamente na mesma linha
          ry={ry || 15}
          fill={color}
          fillOpacity={0.15}
          stroke={color}
          strokeWidth={1.5}
          strokeDasharray="4 4"
          style={{ pointerEvents: 'none' }} // Fundamental para não travar o mouse over dos nós!
        />
      );
    });
  } catch (error) {
    console.error("Erro ignorado no desenho das elipses:", error);
    return null; // O gráfico não quebra mais se a matemática falhar.
  }
};

export default function DashboardML({ dataInicio, dataFim }: DashboardMLProps) {
  const [nClusters, setNClusters] = useState(4);
  const [variavelBoxplot, setVariavelBoxplot] = useState<'retorno' | 'risco'>('retorno');

  const { data: mlData, isLoading: mlLoading } = useQuery({
    queryKey: ['ml-kmeans', dataInicio, dataFim, nClusters],
    queryFn: async () => {
      const res = await apiClient.get('/dashboard-ativos/machine-learning', {
        params: { dt_inicio: dataInicio, dt_fim: dataFim, n_clusters: nClusters }
      });
      return res.data;
    },
  });

  const dadosScatterplot = useMemo(() => {
    if (!mlData?.scatterplot) return [];
    const agrupamento: Record<string, any[]> = {};
    mlData.scatterplot.forEach((ponto: any) => {
      if (!agrupamento[ponto.cluster]) agrupamento[ponto.cluster] = [];
      agrupamento[ponto.cluster].push({ x: ponto.x, y: ponto.y, ativo: ponto.id });
    });
    return Object.keys(agrupamento).map(clusterName => ({
      id: clusterName,
      data: agrupamento[clusterName]
    }));
  }, [mlData]);

  const dadosBoxplot = useMemo(() => {
    if (!mlData?.scatterplot) return [];
    return mlData.scatterplot.map((ponto: any) => ({
      cluster: ponto.cluster,
      valor: variavelBoxplot === 'retorno' ? ponto.y : ponto.x
    }));
  }, [mlData, variavelBoxplot]);

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 rounded-xl p-4 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Settings2 className="w-5 h-5 text-slate-400" />
          <h2 className="text-white font-medium">Hiperparâmetros do K-Means</h2>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-400">Qtd. de Clusters (K):</label>
          <input 
            type="number" min="2" max="10"
            value={nClusters}
            onChange={(e) => setNClusters(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 w-20 text-center text-white outline-none focus:border-purple-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg"><Layers className="w-6 h-6" /></div>
          <div><p className="text-sm font-medium text-slate-400">Ativos Analisados</p><h3 className="text-2xl font-bold text-white">{mlLoading ? '...' : mlData?.metricas?.qtd_ativos || 0}</h3></div>
        </div>
        <div className="bg-slate-900 rounded-xl p-6 shadow-sm border border-slate-800 flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg"><ScatterIcon className="w-6 h-6" /></div>
          <div><p className="text-sm font-medium text-slate-400">Silhouette Score (Qualidade)</p><h3 className="text-2xl font-bold text-white">{mlLoading ? '...' : mlData?.metricas?.silhouette_score || 0}</h3></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GRÁFICO 1: SCATTERPLOT COM ELIPSES */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col h-[550px]">
          <h2 className="text-lg font-bold text-white mb-1">Agrupamento Espacial</h2>
          <p className="text-sm text-slate-500 mb-4">Eixo X: Risco (Volatilidade) | Eixo Y: Retorno Acumulado</p>
          
          <div className="flex-1 w-full min-h-0 bg-slate-950 rounded-lg border border-slate-800">
            {mlLoading ? (
              <div className="flex h-full items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-slate-600" /></div>
            ) : dadosScatterplot.length > 0 ? (
              <ResponsiveScatterPlot
                data={dadosScatterplot}
                margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
                xScale={{ type: 'linear', min: 'auto', max: 'auto' }}
                yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
                colors={{ scheme: 'set2' }}
                nodeSize={12}
                axisBottom={{ tickSize: 5, tickPadding: 5, legend: 'Volatilidade (%)', legendPosition: 'middle', legendOffset: 46 }}
                axisLeft={{ tickSize: 5, tickPadding: 5, legend: 'Retorno (%)', legendPosition: 'middle', legendOffset: -46 }}
                layers={['grid', 'axes', EllipseLayer, 'nodes', 'markers', 'mesh', 'legends']}
                tooltip={({ node }) => (
                  <div className="bg-slate-800 text-slate-100 p-3 rounded-lg shadow-xl text-sm border border-slate-700">
                    <strong className="text-white block mb-1">{node.data.ativo}</strong>
                    <span className="text-slate-400">Cluster: </span>{node.serieId}<br/>
                    <span className="text-slate-400">Risco: </span>{Number(node.data.x).toFixed(2)}%<br/>
                    <span className="text-slate-400">Retorno: </span>{Number(node.data.y).toFixed(2)}%
                  </div>
                )}
                theme={{ text: { fill: '#94a3b8' }, axis: { ticks: { text: { fill: '#94a3b8' } } }, grid: { line: { stroke: '#1e293b' } } }}
              />
            ) : (
               <div className="flex h-full items-center justify-center text-slate-500">Sem dados</div>
            )}
          </div>
        </div>

        {/* GRÁFICO 2: BOXPLOT DINÂMICO */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col h-[550px]">
           <div className="flex justify-between items-start mb-4">
             <div>
               <h2 className="text-lg font-bold text-white mb-1">Distribuição dos Clusters</h2>
               <p className="text-sm text-slate-500">Boxplot estatístico dos grupos formados</p>
             </div>
             <select 
               value={variavelBoxplot} 
               onChange={(e) => setVariavelBoxplot(e.target.value as 'retorno' | 'risco')}
               className="bg-slate-950 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 outline-none focus:border-indigo-500"
             >
               <option value="retorno">Analisar Retorno</option>
               <option value="risco">Analisar Risco (Volatilidade)</option>
             </select>
           </div>

           <div className="flex-1 w-full min-h-0 bg-slate-950 rounded-lg border border-slate-800">
             {mlLoading ? (
                <div className="flex h-full items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-slate-600" /></div>
             ) : dadosBoxplot.length > 0 ? (
            <ResponsiveBoxPlot
                  data={dadosBoxplot}
                  margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
                  groupBy="cluster"
                  value="valor"
                  quantiles={[0.1, 0.25, 0.5, 0.75, 0.9]}
                  padding={0.4}
                  colors={{ scheme: 'set2' }}
                  colorBy="group" // <--- FORÇA AS CORES DOS CLUSTERS
                  theme={{
                    text: { fill: '#94a3b8' },
                    axis: { ticks: { text: { fill: '#94a3b8' } } },
                    grid: { line: { stroke: '#1e293b' } },
                    // SOBRESCREVE O CSS INLINE DO NIVO PARA O DARK MODE
                    tooltip: {
                      container: {
                        background: '#0f172a',
                        color: '#f8fafc',
                        fontSize: '12px',
                        borderRadius: '8px',
                        border: '1px solid #1e293b'
                      }
                    }
                  } as any}
                  axisBottom={{ tickSize: 5, tickPadding: 5, tickRotation: 0, legend: 'Clusters', legendPosition: 'middle', legendOffset: 46 }}
                  axisLeft={{ tickSize: 5, tickPadding: 5, tickRotation: 0, legend: variavelBoxplot === 'retorno' ? 'Retorno (%)' : 'Volatilidade (%)', legendPosition: 'middle', legendOffset: -46 }}
                />
             ) : (
                <div className="flex h-full items-center justify-center text-slate-500">Sem dados</div>
             )}
           </div>
        </div>
      </div>
    </div>
  );
}