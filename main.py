from valuation_engine import ValuationEngine
from score_engine import quality_score
import yfinance as yf



if __name__ == "__main__":
    ticker = input("Digite o ticker: ")
    engine = ValuationEngine(ticker)
    result = engine.run()

    # pega preço atual
    stock = yf.Ticker(ticker)
    current_price = stock.info.get("currentPrice", 0)
    result["Preço Atual (Current Price)"] = current_price

    print("\n--- VALUATION ---")
    for k, v in result.items():
        print(f"{k}: {v:.2f}")

    # calcula score de qualidade
    quality = quality_score(stock.info)
    print(f"\n--- QUALITY SCORE ---")
    print(f"Score: {quality}/8")
