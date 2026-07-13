# backend/services/ml.py
import numpy as np
from sklearn.cluster import KMeans
from typing import Dict, Any
import warnings

# Ignora warnings do scikit-learn sobre vazamento de memória em Windows
warnings.filterwarnings("ignore")

def executar_pipeline_quant(matriz_retornos: Dict[str, list], n_clusters: int = 4) -> Dict[str, Any]:
    """
    Função Compute-Bound isolada. 
    Recebe as séries de retornos e devolve os clusters e a matriz de correlação.
    """
    if not matriz_retornos:
        return {"clusters": {}, "correlacao": []}

    ativos = list(matriz_retornos.keys())
    
    # Monta a matriz X (n_samples, n_features)
    # No nosso caso matemático: samples = ativos, features = tempo (retornos)
    X = np.array([matriz_retornos[ativo] for ativo in ativos])
    
    # CLUSTERIZAÇÃO (K-MEANS)
    # Agrupa ações com comportamento temporal semelhante
    n_clusters = min(n_clusters, len(ativos)) # Proteção caso peçam mais clusters que ativos
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(X)
    
    clusters = {f"Grupo {i}": [] for i in range(n_clusters)}
    for ativo, label in zip(ativos, labels):
        clusters[f"Grupo {label}"].append(ativo)

    # MATRIZ DE CORRELAÇÃO DE PEARSON
    # np.corrcoef espera que cada linha seja uma variável (o que bate com nosso X)
    corr_matrix = np.corrcoef(X)
    
    # Formatação React-Friendly (Ideal para Heatmaps tipo Nivo, Recharts ou D3)
    correlacao_frontend = []
    for i in range(len(ativos)):
        for j in range(len(ativos)):
            correlacao_frontend.append({
                "ativo_1": ativos[i],
                "ativo_2": ativos[j],
                "valor": round(corr_matrix[i, j], 3) # Arredonda para 3 casas
            })

    return {
        "clusters": clusters,
        "correlacao": correlacao_frontend
    }