import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd


def quality_score(info, ticker=None):
    """
    Calcula score de qualidade fundamental (0-100) com ponderação melhorada.
    Considera 10 critérios de qualidade.
    
    Escala: 0-30 (Péssimo) | 30-50 (Fraco) | 50-70 (Bom) | 70-85 (Muito Bom) | 85-100 (Excelente)
    
    Retorna: (score, criteria_results, top_positive, top_alert)
    """
    scores = {}
    criteria_results = {}
    alerts = []
    positives = []
    
    # ====== CRITÉRIO 1: Empresa com mais de 5 anos na Bolsa ======
    try:
        if ticker:
            stock = yf.Ticker(ticker)
            # Tenta obter data de IPO do histórico ou info
            ipo_date = stock.info.get("ipoDate")
            
            if not ipo_date:
                # Alternativa: verificar os dados históricos
                hist = stock.history(period="max", interval="1d")
                if hist is not None and len(hist) > 0:
                    ipo_date = hist.index.min()
            
            if ipo_date:
                if isinstance(ipo_date, str):
                    ipo_date = pd.to_datetime(ipo_date)
                years_listed = (datetime.now() - ipo_date.replace(tzinfo=None)).days / 365.25
                if years_listed >= 5:
                    scores["years_listed"] = 100
                    positives.append("✓ Empresa com +5 anos em Bolsa")
                else:
                    scores["years_listed"] = 30
                    alerts.append(f"⚠️ Empresa com apenas {years_listed:.1f} anos em Bolsa")
            else:
                scores["years_listed"] = 60  # Assume que provavelmente tem 5+ anos
        else:
            scores["years_listed"] = 50
    except Exception as e:
        scores["years_listed"] = 60
    
    # ====== CRITÉRIO 5: ROE acima de 10% ======
    roe = info.get("returnOnEquity", 0)
    if roe > 0.20:
        scores["roe"] = 100
        positives.append("✓ ROE acima de 20%")
    elif roe > 0.15:
        scores["roe"] = 85
        positives.append("✓ ROE entre 15-20%")
    elif roe > 0.10:
        scores["roe"] = 70
        positives.append("✓ ROE acima de 10%")
    elif roe > 0.05:
        scores["roe"] = 50
        alerts.append(f"⚠️ ROE baixo ({roe:.1%})")
    else:
        scores["roe"] = 20
        alerts.append(f"❌ ROE muito baixo ou negativo ({roe:.1%})")
    
    # ====== CRITÉRIO 6: Dívida menor que patrimônio (D/E < 100%) ======
    debt_to_equity = info.get("debtToEquity", 100)
    if debt_to_equity < 50:
        scores["debt"] = 100
        positives.append("✓ Dívida menor que 50% do patrimônio")
    elif debt_to_equity < 100:
        scores["debt"] = 85
        positives.append("✓ Dívida menor que patrimônio")
    elif debt_to_equity < 150:
        scores["debt"] = 50
        alerts.append(f"⚠️ Dívida acima do patrimônio (D/E: {debt_to_equity:.0f}%)")
    else:
        scores["debt"] = 20
        alerts.append(f"❌ Dívida muito alta (D/E: {debt_to_equity:.0f}%)")
    
    # ====== Liquidez (Current Ratio) ======
    current_ratio = info.get("currentRatio", 0)
    if current_ratio >= 2.0:
        scores["liquidity"] = 100
        positives.append("✓ Excelente liquidez (Current Ratio ≥ 2.0)")
    elif current_ratio >= 1.5:
        scores["liquidity"] = 85
        positives.append("✓ Boa liquidez (Current Ratio ≥ 1.5)")
    elif current_ratio >= 1.0:
        scores["liquidity"] = 70
    elif current_ratio >= 0.8:
        scores["liquidity"] = 40
        alerts.append(f"⚠️ Liquidez baixa (Current Ratio: {current_ratio:.2f})")
    else:
        scores["liquidity"] = 10
        alerts.append(f"❌ Risco de insolvência (Current Ratio: {current_ratio:.2f})")
    
    # ====== Margem de Lucro ======
    profit_margin = info.get("profitMargins", 0)
    if profit_margin > 0.20:
        scores["margin"] = 100
        positives.append("✓ Margem de lucro acima de 20%")
    elif profit_margin > 0.15:
        scores["margin"] = 85
        positives.append("✓ Boa margem de lucro (15-20%)")
    elif profit_margin > 0.10:
        scores["margin"] = 70
    elif profit_margin > 0.05:
        scores["margin"] = 50
        alerts.append(f"⚠️ Margem de lucro baixa ({profit_margin:.1%})")
    else:
        scores["margin"] = 20
        alerts.append(f"❌ Margem de lucro muito baixa ({profit_margin:.1%})")
    
    # ====== CRITÉRIO 9: Liquidez diária acima de US$ 2M ======
    try:
        daily_volume = info.get("volume", 0)
        current_price = info.get("currentPrice", 0)
        daily_liquidity = (daily_volume * current_price) if daily_volume and current_price else 0
        
        if daily_liquidity > 2_000_000:
            scores["daily_liquidity"] = 100
            positives.append(f"✓ Liquidez diária alta (${daily_liquidity/1_000_000:.1f}M)")
        elif daily_liquidity > 500_000:
            scores["daily_liquidity"] = 70
        else:
            scores["daily_liquidity"] = 30
            alerts.append(f"⚠️ Liquidez diária baixa (${daily_liquidity/1_000_000:.2f}M)")
    except:
        scores["daily_liquidity"] = 50
    
    # ====== Dados históricos: crescimento, lucros e dividendos ======
    revenue_growth_5y = None
    profit_growth_5y = None
    profitable_quarters = None
    total_quarters = None
    dividend_yield = 0
    
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            
            # Tenta obter dados financeiros anuais
            try:
                financials = stock.financials
                if financials is not None and len(financials.columns) >= 5:
                    recent_5y = financials.iloc[:, :5]  # Últimos 5 anos
                    
                    # Crescimento de receita (5 anos)
                    if 'Total Revenue' in financials.index:
                        revenues = recent_5y.loc['Total Revenue'].dropna()
                        if len(revenues) >= 2:
                            revenue_growth_5y = (revenues.iloc[-1] - revenues.iloc[0]) / abs(revenues.iloc[0]) if revenues.iloc[0] != 0 else 0
                    
                    # Crescimento de lucro (5 anos)
                    if 'Net Income' in financials.index:
                        net_incomes = recent_5y.loc['Net Income'].dropna()
                        if len(net_incomes) >= 2:
                            profit_growth_5y = (net_incomes.iloc[-1] - net_incomes.iloc[0]) / abs(net_incomes.iloc[0]) if net_incomes.iloc[0] != 0 else 0
            except:
                pass
            
            # Tenta obter dados trimestrais para profitabilidade
            try:
                quarterly = stock.quarterly_financials
                if quarterly is not None and len(quarterly.columns) >= 20:
                    recent_20q = quarterly.iloc[:, :20]  # Últimos 20 trimestres
                    
                    if 'Net Income' in quarterly.index:
                        net_incomes = recent_20q.loc['Net Income'].dropna()
                        if len(net_incomes) > 0:
                            profitable_quarters = (net_incomes > 0).sum()
                            total_quarters = len(net_incomes)
            except:
                pass
            
            # Tenta obter dividendos
            try:
                dividends = stock.dividends
                if dividends is not None and len(dividends) > 0:
                    current_price = info.get("currentPrice", 1)
                    five_years_ago = datetime.now() - timedelta(days=365*5)
                    recent_divs = dividends[dividends.index >= five_years_ago]
                    
                    if len(recent_divs) > 0:
                        annual_dividend = recent_divs.sum()
                        dividend_yield = (annual_dividend / current_price) if current_price > 0 else 0
            except:
                pass
        except:
            pass
    
    # ====== CRITÉRIO 7: Crescimento de receita (5 anos) ======
    if revenue_growth_5y is not None:
        if revenue_growth_5y > 0:
            scores["revenue_growth_5y"] = 100
            positives.append(f"✓ Receita em crescimento nos últimos 5 anos (+{revenue_growth_5y:.0%})")
        else:
            scores["revenue_growth_5y"] = 20
            alerts.append("❌ Receita decrescente ou estagnada")
    else:
        scores["revenue_growth_5y"] = 60  # Não tem dados, assume mediano
    
    # ====== CRITÉRIO 8: Crescimento de lucro (5 anos) ======
    if profit_growth_5y is not None:
        if profit_growth_5y > 0:
            scores["profit_growth_5y"] = 100
            positives.append(f"✓ Lucro em crescimento nos últimos 5 anos (+{profit_growth_5y:.0%})")
        else:
            scores["profit_growth_5y"] = 20
            alerts.append("❌ Lucro decrescente ou instável")
    else:
        scores["profit_growth_5y"] = 60  # Não tem dados, assume mediano
    
    # ====== CRITÉRIO 2 & 3: Lucro em todos os últimos 20 trimestres ======
    if profitable_quarters is not None and total_quarters is not None:
        if profitable_quarters == total_quarters:
            scores["profitability"] = 100
            positives.append("✓ Lucrativa em todos os últimos 20 trimestres")
        elif profitable_quarters >= 18:
            scores["profitability"] = 80
            positives.append(f"✓ Lucrativa em {profitable_quarters}/20 trimestres")
        elif profitable_quarters >= 15:
            scores["profitability"] = 60
        else:
            scores["profitability"] = 30
            alerts.append(f"⚠️ Lucro apenas em {profitable_quarters}/20 trimestres")
    else:
        scores["profitability"] = 60  # Não tem dados, assume mediano
    
    # ====== CRITÉRIO 4: Dividendos +5% a.a. (5 anos) ======
    if dividend_yield >= 0.05:
        scores["dividends"] = 100
        positives.append(f"✓ Dividendo acima de 5% a.a. ({dividend_yield:.1%})")
    elif dividend_yield >= 0.03:
        scores["dividends"] = 70
        positives.append(f"✓ Bom dividend yield ({dividend_yield:.1%})")
    elif dividend_yield > 0:
        scores["dividends"] = 40
        alerts.append(f"⚠️ Dividend yield baixo ({dividend_yield:.1%})")
    else:
        scores["dividends"] = 20
        alerts.append("⚠️ Sem histórico de dividendos recentes ou yield = 0")
    
    # ====== Valores padrão se métrica não existir ======
    default_metrics = {
        "years_listed": 60,
        "roe": 50,
        "debt": 50,
        "liquidity": 50,
        "margin": 50,
        "daily_liquidity": 50,
        "revenue_growth_5y": 60,
        "profit_growth_5y": 60,
        "profitability": 60,
        "dividends": 40,
    }
    
    for key in default_metrics:
        if key not in scores:
            scores[key] = default_metrics[key]
    
    # ====== Ponderação final ======
    weights = {
        "years_listed": 0.05,          # 5%
        "profitability": 0.20,         # 20%
        "profit_growth_5y": 0.15,      # 15%
        "revenue_growth_5y": 0.10,     # 10%
        "dividends": 0.10,             # 10%
        "roe": 0.15,                   # 15%
        "debt": 0.10,                  # 10%
        "daily_liquidity": 0.05,       # 5%
        "liquidity": 0.05,             # 5%
        "margin": 0.05,                # 5%
    }
    
    final_score = sum(scores.get(key, 50) * weight for key, weight in weights.items())
    
    # ====== Penalizações severas ======
    if current_ratio < 0.8 or debt_to_equity > 200:
        final_score = min(final_score, 35)
    
    # Seleciona o maior positivo e o maior alerta
    top_positive = positives[0] if positives else "ℹ️ Análise incompleta"
    top_alert = alerts[0] if alerts else None
    
    # Armazena resultados dos critérios para debug
    criteria_results = {
        "scores": scores,
        "weights": weights,
        "positives": positives,
        "alerts": alerts,
    }
    
    return round(final_score, 1), criteria_results, top_positive, top_alert