import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import Dict, Any
import warnings

warnings.filterwarnings("ignore")

def executar_pipeline_kmeans(dados_quant: Dict[str, Any], n_clusters: int = 4) -> Dict[str, Any]:
    features = dados_quant.get("features_2d", [])
    # A série temporal para correlação não é mais necessária aqui
    
    if not features:
        return {"metricas": {}, "scatterplot": []}

    ativos = [f["ativo"] for f in features]
    X_kmeans = np.array([[f["retorno_acumulado"], f["volatilidade"]] for f in features])
    
    n_clusters = min(n_clusters, len(ativos))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(X_kmeans)
    
    sil_score = float(silhouette_score(X_kmeans, labels)) if n_clusters > 1 else 0.0

    scatterplot_data = [
        {
            "id": ativo,
            "x": features[i]["volatilidade"],
            "y": features[i]["retorno_acumulado"],
            "cluster": f"Grupo {labels[i]}"
        }
        for i, ativo in enumerate(ativos)
    ]

    # CÁLCULO DE CORRELAÇÃO REMOVIDO (O(N*M^2) eliminado pelo bem da otimização)

    return {
        "metricas": {
            "silhouette_score": round(sil_score, 3),
            "qtd_grupos": n_clusters,
            "qtd_ativos": len(ativos)
        },
        "scatterplot": scatterplot_data
    }