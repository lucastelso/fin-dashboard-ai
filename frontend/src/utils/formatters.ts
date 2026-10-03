export const formatBRL = (value: number | undefined | null): string => {
  if (value == null || isNaN(value)) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};

export const formatPercent = (value: number | undefined | null, decimals = 2): string => {
  if (value == null || isNaN(value)) return '0,00%';
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value) + '%';
};

export const formatDateBR = (dateString: string | undefined | null): string => {
  if (!dateString) return '--/--/----';
  const d = new Date(dateString);
  // Garante o formato DD/MM/YYYY
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(d);
};

export const formatDateTimeBR = (dateString: string | undefined | null): string => {
  if (!dateString) return '--/--/---- --:--';
  const d = new Date(dateString);
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  }).format(d);
};