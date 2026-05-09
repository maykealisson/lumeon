def quality_score(info):
    """
    Calcula score de qualidade fundamental (0-100) com ponderação.
    Escala: 0-30 (Péssimo) | 30-50 (Fraco) | 50-70 (Bom) | 70-85 (Muito Bom) | 85-100 (Excelente)
    """
    scores = {}
    
    # ====== ROE (Rentabilidade do Patrimônio) - 25% da pontuação ======
    roe = info.get("returnOnEquity", 0)
    if roe > 0.20:
        scores["roe"] = 100
    elif roe > 0.15:
        scores["roe"] = 85
    elif roe > 0.10:
        scores["roe"] = 70
    elif roe > 0.05:
        scores["roe"] = 50
    else:
        scores["roe"] = 20  # Penaliza ROE baixo
    
    # ====== Liquidez (Current Ratio) - 20% da pontuação ======
    current_ratio = info.get("currentRatio", 0)
    if current_ratio >= 2.0:
        scores["liquidity"] = 100
    elif current_ratio >= 1.5:
        scores["liquidity"] = 85
    elif current_ratio >= 1.0:
        scores["liquidity"] = 70
    elif current_ratio >= 0.8:
        scores["liquidity"] = 40  # Alerta: liquidez baixa
    else:
        scores["liquidity"] = 10  # Penaliza muito: risco de insolvência
    
    # ====== Endividamento (Debt-to-Equity) - 20% da pontuação ======
    debt_to_equity = info.get("debtToEquity", 100)
    if debt_to_equity < 30:
        scores["debt"] = 100
    elif debt_to_equity < 50:
        scores["debt"] = 85
    elif debt_to_equity < 100:
        scores["debt"] = 70
    elif debt_to_equity < 150:
        scores["debt"] = 40  # Alerta: dívida alta
    else:
        scores["debt"] = 10  # Penaliza muito: empresa endividada
    
    # ====== Margem de Lucro - 15% da pontuação ======
    profit_margin = info.get("profitMargins", 0)
    if profit_margin > 0.20:
        scores["margin"] = 100
    elif profit_margin > 0.15:
        scores["margin"] = 85
    elif profit_margin > 0.10:
        scores["margin"] = 70
    elif profit_margin > 0.05:
        scores["margin"] = 50
    else:
        scores["margin"] = 20  # Margem muito baixa
    
    # ====== Crescimento de Receita - 10% da pontuação ======
    revenue_growth = info.get("revenueGrowth", 0)
    if revenue_growth > 0.20:
        scores["growth"] = 100
    elif revenue_growth > 0.10:
        scores["growth"] = 85
    elif revenue_growth > 0.05:
        scores["growth"] = 70
    elif revenue_growth > 0:
        scores["growth"] = 50
    else:
        scores["growth"] = 30  # Crescimento negativo ou zero
    
    # ====== Ponderação final ======
    weights = {
        "roe": 0.25,
        "liquidity": 0.20,
        "debt": 0.20,
        "margin": 0.15,
        "growth": 0.10
    }
    
    # Valores padrão se métrica não existir
    for key in weights:
        if key not in scores:
            scores[key] = 50  # Neutro
    
    # Calcula score ponderado
    final_score = sum(scores[key] * weights[key] for key in weights)
    
    # Penalização adicional: se Current Ratio < 0.8 OU Debt > 200%, máximo 40
    if current_ratio < 0.8 or debt_to_equity > 200:
        final_score = min(final_score, 35)
    
    return round(final_score, 1)