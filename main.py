"""
Agent Fundament - CLI Interface
Para usar a API REST, execute: python -m uvicorn api:app --reload
"""
from valuation_engine import ValuationEngine
from score_engine import quality_score
import yfinance as yf


def main():
    print("\n" + "="*60)
    print("AGENT FUNDAMENT - ANÁLISE FUNDAMENTALISTA")
    print("="*60)
    print("\nPara usar a API REST, execute em outro terminal:")
    print("  python -m uvicorn api:app --reload")
    print("\nAcesse: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    ticker = input("Digite o ticker (ex: AAPL ou PETR4.SA): ").strip().upper()
    
    if not ticker:
        print("❌ Ticker inválido!")
        return
    
    try:
        # Validação rápida
        stock = yf.Ticker(ticker)
        if not stock.info or "longName" not in stock.info:
            print(f"❌ Ticker '{ticker}' não encontrado")
            return
        
        print(f"\n📊 Analisando {stock.info.get('longName', ticker)}...")
        
        # VALUATION
        engine = ValuationEngine(ticker)
        result = engine.run()
        current_price = stock.info.get("currentPrice", 0)
        
        print("\n" + "="*60)
        print("📈 VALUATION (PREÇO JUSTO)")
        print("="*60)
        
        dcf_value = result.get("Valor justo calculado pelo Fluxo de Caixa Descontado")
        mult_value = result.get("Valor estimado com base em comparações de mercado (P/L, EV/EBITDA etc.)")
        fair_value = result.get("Valor Justo (Fair Value)")
        buy_price = result.get("Preço de Compra (Margem de Segurança)")
        
        print(f"Preço Atual (Current Price):          ${current_price:.2f}")
        print(f"DCF Value (Fluxo de Caixa):           ${dcf_value:.2f}" if dcf_value else "DCF Value: N/A")
        print(f"Múltiplos Value (P/L):                ${mult_value:.2f}" if mult_value else "Múltiplos: N/A")
        print(f"Valor Justo (Fair Value):             ${fair_value:.2f}")
        print(f"Preço de Compra (Margem 40%):         ${buy_price:.2f}")
        
        # Análise de preço
        if current_price <= buy_price:
            discount = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0
            print(f"\n🟢 COMPRA FORTE! ({discount:.1f}% abaixo do preço justo)")
        elif current_price <= fair_value:
            discount = ((fair_value - current_price) / current_price * 100) if current_price > 0 else 0
            print(f"\n🟢 COMPRA ({discount:.1f}% abaixo)")
        elif current_price > fair_value:
            overpriced = ((current_price - fair_value) / fair_value * 100)
            print(f"\n🔴 VENDA ({overpriced:.1f}% acima do preço justo)")
        
        # QUALITY SCORE
        quality = quality_score(stock.info)
        
        print("\n" + "="*60)
        print("📊 QUALITY SCORE (0-100)")
        print("="*60)
        print(f"Score: {quality}/100")
        
        if quality >= 85:
            print("👑 EXCELENTE - Empresa de qualidade comprovada")
        elif quality >= 70:
            print("✓✓ MUITO BOM - Boa empresa, fundamentals sólidos")
        elif quality >= 50:
            print("✓ BOM - Empresa aceitável, alguns pontos de atenção")
        elif quality >= 30:
            print("⚠️ FRACO - Empresa com problemas, evitar")
        else:
            print("❌ PÉSSIMO - Alto risco, não comprar")
        
        # Detalhes
        print("\n📋 Métricas:")
        metrics = {
            "ROE (Rentabilidade)": stock.info.get("returnOnEquity", 0),
            "Current Ratio (Liquidez)": stock.info.get("currentRatio", 0),
            "Debt/Equity (Dívida)": stock.info.get("debtToEquity", 0),
            "Margem de Lucro": stock.info.get("profitMargins", 0),
            "Revenue Growth": stock.info.get("revenueGrowth", 0),
        }
        
        for name, value in metrics.items():
            print(f"  {name:.<40} {value:.2%}")
        
        # RECOMENDAÇÃO FINAL
        print("\n" + "="*60)
        print("💡 RECOMENDAÇÃO")
        print("="*60)
        
        if quality < 50:
            print("❌ NÃO COMPRAR - Score abaixo de 50 indica alto risco")
        elif current_price <= buy_price and quality >= 70:
            print("🟢 COMPRA RECOMENDADA")
            print(f"   Boa qualidade ({quality:.1f}/100) e preço abaixo da margem de segurança")
        elif current_price <= fair_value and quality >= 70:
            print("🟢 COMPRA - Boa qualidade e preço justo/abaixo")
        elif current_price > fair_value and quality >= 70:
            print("🟡 AGUARDE - Boa qualidade mas preço acima do justo")
        else:
            print("🔴 VENDA - Preço acima do justo ou qualidade fraca")
        
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Erro ao analisar: {e}")


if __name__ == "__main__":
    main()

