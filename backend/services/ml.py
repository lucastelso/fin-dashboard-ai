import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import Dict, Any
import warnings

warnings.filterwarnings("ignore")

def executar_pipeline_kmeans(dados_quant: Dict[str, Any], n_clusters: int = 4) -> Dict[str, Any]:
    """
    Pipeline Compute-Bound.
    Calcula K-Means em 2D (Retorno x Risco) e Correlação de Pearson.
    """
    features = dados_quant.get("features_2d", [])
    series = dados_quant.get("series_temporais", {})

    if not features or not series:
        return {"metricas": {}, "scatterplot": [], "correlacao": []}

    ativos = [f["ativo"] for f in features]
    
    X_kmeans = np.array([[f["retorno_acumulado"], f["volatilidade"]] for f in features])
    
    # K-MEANS + MÉTRICAS
    n_clusters = min(n_clusters, len(ativos))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(X_kmeans)
    
    # Calcula o Silhouette Score (se houver mais de 1 cluster)
    sil_score = float(silhouette_score(X_kmeans, labels)) if n_clusters > 1 else 0.0

    # Estrutura os dados para o Scatterplot do React
    scatterplot_data = []
    for i, ativo in enumerate(ativos):
        scatterplot_data.append({
            "id": ativo,
            "x": features[i]["volatilidade"],
            "y": features[i]["retorno_acumulado"],
            "cluster": f"Grupo {labels[i]}"
        })

    # Matriz para a correlação cruzada de comportamento
    X_corr = np.array([series[ativo] for ativo in ativos])
    corr_matrix = np.corrcoef(X_corr)
    
    correlacao_data = []
    for i in range(len(ativos)):
        for j in range(len(ativos)):
            correlacao_data.append({
                "x": ativos[i],
                "y": ativos[j],
                "valor": round(corr_matrix[i, j], 3)
            })

    return {
        "metricas": {
            "silhouette_score": round(sil_score, 3),
            "qtd_grupos": n_clusters,
            "qtd_ativos": len(ativos)
        },
        "scatterplot": scatterplot_data,
        "correlacao": correlacao_data
    }