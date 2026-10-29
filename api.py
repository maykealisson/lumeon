from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import yfinance as yf
from valuation_engine import ValuationEngine
from score_engine import quality_score
from database import get_session, init_db
from analise_parser import AnaliseInvalidaError, parse_analise
import analise_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Agent Fundament API",
    description="API para análise fundamentalista de ações",
    version="1.1.0",
    lifespan=lifespan,
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


class AnaliseUploadRequest(BaseModel):
    conteudo: str = Field(..., min_length=1, max_length=500_000, description="Conteúdo do arquivo .md da análise")
    nome_arquivo: Optional[str] = Field(None, max_length=255)


class AnaliseResumoResponse(BaseModel):
    id: int
    ticker: str
    empresa: Optional[str]
    data_analise: str
    periodo_referencia: Optional[str]
    preco: Optional[float]
    valor_intrinseco: Optional[float]
    margem_seguranca: Optional[float]
    nota_checklist: Optional[float]
    veredito_qualidade: Optional[str]
    veredito_preco: Optional[str]
    tese: Optional[str]
    nome_arquivo: Optional[str]
    criado_em: Optional[str]


class AnaliseUploadResponse(AnaliseResumoResponse):
    substituida: bool = Field(description="True quando já existia análise do ticker nessa data e ela foi substituída")


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
    - Interpretation: Maior ponto positivo ou maior alerta
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
        
        score, criteria_results, top_positive, top_alert = quality_score(stock.info, ticker)
        
        # Interpretação: maior ponto positivo OU maior alerta
        if top_alert:
            interpretation = f"{top_alert}"
        else:
            interpretation = top_positive
        
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
        score, criteria_results, top_positive, top_alert = quality_score(stock.info, ticker)
        
        # Interpretação: maior ponto positivo OU maior alerta
        if top_alert:
            score_interpretation = f"{top_alert}"
        else:
            score_interpretation = top_positive
        
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
    except HTTPException:
        raise
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
            score, _, _, _ = quality_score(stock.info, ticker)
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


# ============ ANÁLISES ENVIADAS (.md) ============

@app.post("/ativos/{ticker}/analises", response_model=AnaliseUploadResponse, status_code=201, tags=["Análises"])
def enviar_analise(ticker: str, request: AnaliseUploadRequest, session: Session = Depends(get_session)):
    """
    Recebe o conteúdo de um arquivo de análise (.md com frontmatter YAML), extrai as
    informações e grava no banco. Cada data de análise gera um registro; reenviar o
    mesmo ticker + data substitui o registro anterior.
    """
    try:
        dados = parse_analise(request.conteudo)
    except AnaliseInvalidaError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if dados.ticker != ticker.upper():
        raise HTTPException(
            status_code=422,
            detail=f"O arquivo é do ticker {dados.ticker}, mas foi enviado para {ticker.upper()}",
        )
    analise, substituida = analise_service.salvar_analise(session, dados, request.conteudo, request.nome_arquivo)
    return {**analise_service.resumo(analise), "substituida": substituida}


@app.get("/ativos/{ticker}/analises", response_model=List[AnaliseResumoResponse], tags=["Análises"])
def listar_analises(ticker: str, session: Session = Depends(get_session)):
    """Lista as análises gravadas do ticker, da mais recente para a mais antiga."""
    return [analise_service.resumo(a) for a in analise_service.listar_analises(session, ticker)]


@app.get("/ativos/{ticker}/relatorio", tags=["Análises"])
def gerar_relatorio(
    ticker: str,
    margem_desejada: float = Query(20.0, ge=0, le=90, description="Margem de segurança exigida (%)"),
    session: Session = Depends(get_session),
):
    """
    Processa as análises gravadas do ticker junto com os dados de mercado de hoje:
    preço atual, preço justo, margem de segurança, múltiplos no preço atual,
    pontos positivos e de atenção, riscos, gatilhos de saída e evolução entre análises.
    """
    relatorio = analise_service.gerar_relatorio(session, ticker, margem_desejada)
    if relatorio is None:
        raise HTTPException(status_code=404, detail=f"Nenhuma análise cadastrada para {ticker.upper()}")
    return relatorio


@app.get("/analises/{analise_id}", tags=["Análises"])
def detalhar_analise(analise_id: int, session: Session = Depends(get_session)):
    """Todos os dados extraídos de uma análise."""
    analise = analise_service.buscar_analise(session, analise_id)
    if analise is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return analise_service.detalhe(analise)


@app.delete("/analises/{analise_id}", status_code=204, tags=["Análises"])
def remover_analise(analise_id: int, session: Session = Depends(get_session)):
    analise = analise_service.buscar_analise(session, analise_id)
    if analise is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    analise_service.remover_analise(session, analise)


# ============ EXECUÇÃO ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
