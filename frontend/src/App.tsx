import { useState } from 'react';
import { Calendar, LayoutDashboard, BrainCircuit } from 'lucide-react';
import DashboardMacro from './pages/DashboardMacro';
import DashboardML from './pages/DashboardML';

export default function App() {
  const [dataInicio, setDataInicio] = useState('2026-06-01');
  const [dataFim, setDataFim] = useState('2026-07-10');
  const [abaAtiva, setAbaAtiva] = useState<'macro' | 'ml'>('macro');

  return (
    <div className="min-h-screen bg-slate-950 p-8 font-sans text-slate-100">
      <header className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Dashboard Financeiro Inteligente</h1>
          <p className="text-slate-400 mt-1">Visão Macro e Análise Quantitativa</p>
        </div>
        
        <div className="flex gap-4 items-center flex-wrap">
          <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800">
            <button 
              onClick={() => setAbaAtiva('macro')} 
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer ${abaAtiva === 'macro' ? 'bg-slate-800 text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <LayoutDashboard className="w-4 h-4" /> Visão Macro
            </button>
            <button 
              onClick={() => setAbaAtiva('ml')} 
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer ${abaAtiva === 'ml' ? 'bg-slate-800 text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <BrainCircuit className="w-4 h-4" /> Inteligência (ML)
            </button>
          </div>

          <div className="flex items-center gap-3 bg-slate-900 p-2 rounded-lg shadow-sm border border-slate-800">
            <Calendar className="w-5 h-5 text-slate-500 ml-2" />
            <input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} className="bg-transparent border-none text-sm font-medium text-slate-300 outline-none" style={{colorScheme: 'dark'}} />
            <span className="text-slate-600">até</span>
            <input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} className="bg-transparent border-none text-sm font-medium text-slate-300 outline-none pr-2" style={{colorScheme: 'dark'}} />
          </div>
        </div>
      </header>

      {abaAtiva === 'macro' ? <DashboardMacro dataInicio={dataInicio} dataFim={dataFim} /> : <DashboardML dataInicio={dataInicio} dataFim={dataFim} />}
    </div>
  );
}