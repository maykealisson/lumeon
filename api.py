from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import yfinance as yf
from valuation_engine import ValuationEngine
from score_engine import quality_score

app = FastAPI(
    title="Agent Fundament API",
    description="API para análise fundamentalista de ações",
    version="1.0.0"
)

# CORS para aceitar requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ MODELOS DE RESPOSTA ============

class ValuationResponse(BaseModel):
    ticker: str
    dcf_value: Optional[float]
    multiples_value: Optional[float]
    fair_value: Optional[float]
    buy_price: Optional[float]
    current_price: float


class QualityScoreResponse(BaseModel):
    ticker: str
    score: float
    interpretation: str
    metrics: Dict[str, Any]


class AnalysisResponse(BaseModel):
    ticker: str
    valuation: ValuationResponse
    quality: QualityScoreResponse
    recommendation: str


class HealthResponse(BaseModel):
    status: str
    message: str


# ============ ENDPOINTS ============

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Verifica se a API está funcionando"""
    return {
        "status": "healthy",
        "message": "API de análise fundamentalista está operacional"
    }


@app.get("/valuation/{ticker}", response_model=ValuationResponse, tags=["Análise"])
async def get_valuation(ticker: str):
    """
    Calcula o preço justo (Fair Value) de uma ação
    
    **Parâmetros:**
    - `ticker`: Símbolo da ação (ex: AAPL, PETR4.SA)
    
    **Retorna:**
    - DCF Value: Valor calculado via Fluxo de Caixa Descontado
    - Multiples Value: Valor via múltiplos de mercado
    - Fair Value: Média entre os dois
    - Buy Price: Preço com margem de segurança de 40%
    """
    try:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        
        # Valida se o ticker existe
        if not stock.info or "longName" not in stock.info:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker '{ticker}' não encontrado"
            )
        
        engine = ValuationEngine(ticker)
        result = engine.run()
        current_price = stock.info.get("currentPrice", 0)
        
        return {
            "ticker": ticker,
            "dcf_value": result.get("Valor justo calculado pelo Fluxo de Caixa Descontado"),
            "multiples_value": result.get("Valor estimado com base em comparações de mercado (P/L, EV/EBITDA etc.)"),
            "fair_value": result.get("Valor Justo (Fair Value)"),
            "buy_price": result.get("Preço de Compra (Margem de Segurança)"),
            "current_price": current_price
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/quality/{ticker}", response_model=QualityScoreResponse, tags=["Análise"])
async def get_quality_score(ticker: str):
    """
    Calcula o score de qualidade fundamentalista (0-100)
    
    **Parâmetros:**
    - `ticker`: Símbolo da ação (ex: AAPL, PETR4.SA)
    
    **Retorna:**
    - Score: 0-100 pontos
    - Interpretation: Classificação (Péssimo até Excelente)
    - Metrics: Detalhamento de cada métrica
    """
    try:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        
        if not stock.info or "longName" not in stock.info:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker '{ticker}' não encontrado"
            )
        
        score = quality_score(stock.info)
        
        # Interpretação
        if score >= 85:
            interpretation = "👑 EXCELENTE - Empresa de qualidade comprovada"
        elif score >= 70:
            interpretation = "✓✓ MUITO BOM - Boa empresa, fundamentals sólidos"
        elif score >= 50:
            interpretation = "✓ BOM - Empresa aceitável, alguns pontos de atenção"
        elif score >= 30:
            interpretation = "⚠️ FRACO - Empresa com problemas, evitar"
        else:
            interpretation = "❌ PÉSSIMO - Alto risco, não comprar"
        
        # Métricas
        metrics = {
            "roe": stock.info.get("returnOnEquity", 0),
            "current_ratio": stock.info.get("currentRatio", 0),
            "debt_to_equity": stock.info.get("debtToEquity", 0),
            "profit_margin": stock.info.get("profitMargins", 0),
            "revenue_growth": stock.info.get("revenueGrowth", 0),
        }
        
        return {
            "ticker": ticker,
            "score": score,
            "interpretation": interpretation,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/analyze/{ticker}", response_model=AnalysisResponse, tags=["Análise"])
async def analyze_stock(ticker: str):
    """
    Análise completa de uma ação (Valuation + Quality Score)
    
    **Parâmetros:**
    - `ticker`: Símbolo da ação (ex: AAPL, PETR4.SA)
    
    **Retorna:**
    - Valuation: Fair Value e preços
    - Quality: Score e métricas
    - Recommendation: Sugestão de compra/venda
    """
    try:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        
        if not stock.info or "longName" not in stock.info:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker '{ticker}' não encontrado"
            )
        
        # Valuation
        engine = ValuationEngine(ticker)
        valuation_result = engine.run()
        current_price = stock.info.get("currentPrice", 0)
        
        valuation = {
            "ticker": ticker,
            "dcf_value": valuation_result.get("Valor justo calculado pelo Fluxo de Caixa Descontado"),
            "multiples_value": valuation_result.get("Valor estimado com base em comparações de mercado (P/L, EV/EBITDA etc.)"),
            "fair_value": valuation_result.get("Valor Justo (Fair Value)"),
            "buy_price": valuation_result.get("Preço de Compra (Margem de Segurança)"),
            "current_price": current_price
        }
        
        # Quality Score
        score = quality_score(stock.info)
        
        if score >= 85:
            score_interpretation = "👑 EXCELENTE - Empresa de qualidade comprovada"
        elif score >= 70:
            score_interpretation = "✓✓ MUITO BOM - Boa empresa, fundamentals sólidos"
        elif score >= 50:
            score_interpretation = "✓ BOM - Empresa aceitável, alguns pontos de atenção"
        elif score >= 30:
            score_interpretation = "⚠️ FRACO - Empresa com problemas, evitar"
        else:
            score_interpretation = "❌ PÉSSIMO - Alto risco, não comprar"
        
        quality = {
            "ticker": ticker,
            "score": score,
            "interpretation": score_interpretation,
            "metrics": {
                "roe": stock.info.get("returnOnEquity", 0),
                "current_ratio": stock.info.get("currentRatio", 0),
                "debt_to_equity": stock.info.get("debtToEquity", 0),
                "profit_margin": stock.info.get("profitMargins", 0),
                "revenue_growth": stock.info.get("revenueGrowth", 0),
            }
        }
        
        # Recomendação
        fair_value = valuation["fair_value"]
        buy_price = valuation["buy_price"]
        
        if score < 50:
            recommendation = "❌ NÃO COMPRAR - Score abaixo de 50 indica alto risco"
        elif current_price <= buy_price and score >= 70:
            recommendation = "🟢 COMPRA RECOMENDADA - Boa qualidade e preço abaixo da margem de segurança"
        elif current_price <= fair_value and score >= 70:
            recommendation = "🟢 COMPRA - Boa qualidade e preço justo/abaixo"
        elif current_price > fair_value and score >= 70:
            recommendation = "🟡 AGUARDE - Boa qualidade mas preço acima do justo"
        else:
            recommendation = "🔴 VENDA - Preço acima do justo ou qualidade fraca"
        
        return {
            "ticker": ticker,
            "valuation": valuation,
            "quality": quality,
            "recommendation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/compare", tags=["Análise"])
async def compare_stocks(tickers: str = Query(..., description="Tickers separados por vírgula (ex: AAPL,MSFT,PETR4.SA)")):
    """
    Compara múltiplas ações lado a lado
    
    **Parâmetros:**
    - `tickers`: Símbolos separados por vírgula
    
    **Retorna:**
    Lista com análise de cada ação para comparação
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    
    if len(ticker_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="Máximo de 10 tickers por comparação"
        )
    
    results = []
    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            if not stock.info or "longName" not in stock.info:
                results.append({"ticker": ticker, "error": "Não encontrado"})
                continue
            
            engine = ValuationEngine(ticker)
            valuation_result = engine.run()
            score = quality_score(stock.info)
            current_price = stock.info.get("currentPrice", 0)
            
            results.append({
                "ticker": ticker,
                "company_name": stock.info.get("longName", ""),
                "current_price": current_price,
                "fair_value": valuation_result.get("Valor Justo (Fair Value)"),
                "buy_price": valuation_result.get("Preço de Compra (Margem de Segurança)"),
                "quality_score": score,
                "discount_percent": round(
                    ((valuation_result.get("Valor Justo (Fair Value)", 1) - current_price) / current_price * 100) 
                    if current_price > 0 else 0, 2
                )
            })
        except Exception as e:
            results.append({"ticker": ticker, "error": str(e)})
    
    return {"comparison": results}


# ============ EXECUÇÃO ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
