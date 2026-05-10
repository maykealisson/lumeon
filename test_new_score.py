#!/usr/bin/env python3
"""
Script para testar a nova lógica de score de qualidade
"""

import yfinance as yf
from score_engine import quality_score

def test_ticker(ticker):
    """Testa o score para um ticker específico"""
    print(f"\n{'='*70}")
    print(f"🔍 Analisando: {ticker}")
    print(f"{'='*70}")
    
    try:
        stock = yf.Ticker(ticker)
        
        if not stock.info or "longName" not in stock.info:
            print(f"❌ Ticker '{ticker}' não encontrado")
            return
        
        print(f"Nome: {stock.info.get('longName', 'N/A')}")
        
        # Calcula score com os novos critérios
        score, criteria_results, top_positive, top_alert = quality_score(stock.info, ticker)
        
        print(f"\n📊 SCORE FINAL: {score}/100")
        print(f"   Interpretação: {top_positive}")
        if criteria_results.get('alerts'):
            print(f"   ⚠️ Alertas: {criteria_results['alerts']}")
        
        print(f"\n📋 DETALHAMENTO DOS CRITÉRIOS:")
        scores = criteria_results.get('scores', {})
        for criterion, score_val in scores.items():
            status = "✓" if score_val >= 70 else "⚠️" if score_val >= 50 else "❌"
            print(f"   {status} {criterion:20} {score_val:6.1f}")
        
        print(f"\n💡 PONTOS POSITIVOS:")
        for positive in criteria_results.get('positives', []):
            print(f"   {positive}")
        
        if criteria_results.get('alerts'):
            print(f"\n🚨 ALERTAS:")
            for alert in criteria_results.get('alerts', []):
                print(f"   {alert}")
        
    except Exception as e:
        print(f"❌ Erro ao analisar {ticker}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Testa com algumas ações populares
    tickers = ["AAPL", "MSFT", "PETR4.SA", "VALE3.SA"]
    
    for ticker in tickers:
        test_ticker(ticker)
    
    print(f"\n{'='*70}")
    print("✅ Testes concluídos!")
    print(f"{'='*70}\n")
