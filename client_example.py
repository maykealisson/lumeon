"""
Cliente Python para Agent Fundament API
Exemplo de uso: python client_example.py
"""

import requests
from typing import List, Dict, Optional
import json


class AgentFundamentClient:
    """Cliente para interagir com Agent Fundament API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict:
        """Verifica se a API está funcionando"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_valuation(self, ticker: str) -> Dict:
        """Obtém valuation de uma ação"""
        response = self.session.get(f"{self.base_url}/valuation/{ticker}")
        response.raise_for_status()
        return response.json()
    
    def get_quality_score(self, ticker: str) -> Dict:
        """Obtém quality score de uma ação"""
        response = self.session.get(f"{self.base_url}/quality/{ticker}")
        response.raise_for_status()
        return response.json()
    
    def analyze(self, ticker: str) -> Dict:
        """Análise completa de uma ação"""
        response = self.session.get(f"{self.base_url}/analyze/{ticker}")
        response.raise_for_status()
        return response.json()
    
    def compare(self, tickers: List[str]) -> Dict:
        """Compara múltiplas ações"""
        ticker_str = ",".join(tickers)
        response = self.session.get(f"{self.base_url}/compare?tickers={ticker_str}")
        response.raise_for_status()
        return response.json()


# ============ EXEMPLOS DE USO ============

def example_1_single_analysis():
    """Exemplo 1: Analisar uma ação"""
    print("\n" + "="*70)
    print("EXEMPLO 1: Análise Completa de Uma Ação")
    print("="*70 + "\n")
    
    client = AgentFundamentClient()
    
    try:
        # Verificar se API está online
        health = client.health_check()
        print(f"✅ API Status: {health['message']}\n")
        
        # Analisar AAPL
        analysis = client.analyze("AAPL")
        
        val = analysis['valuation']
        qual = analysis['quality']
        
        print(f"📊 {analysis['ticker']}")
        print(f"   Preço Atual:      ${val['current_price']:.2f}")
        print(f"   Preço Justo:      ${val['fair_value']:.2f}")
        print(f"   Preço de Compra:  ${val['buy_price']:.2f}")
        print(f"\n   Quality Score:    {qual['score']:.1f}/100")
        print(f"   Interpretação:    {qual['interpretation']}")
        print(f"\n💡 Recomendação: {analysis['recommendation']}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def example_2_valuation_only():
    """Exemplo 2: Apenas valuation"""
    print("\n" + "="*70)
    print("EXEMPLO 2: Apenas Valuation (Preço Justo)")
    print("="*70 + "\n")
    
    client = AgentFundamentClient()
    
    try:
        val = client.get_valuation("MSFT")
        
        print(f"📈 {val['ticker']}")
        print(f"   DCF Value:        ${val['dcf_value']:.2f}")
        print(f"   Multiples Value:  ${val['multiples_value']:.2f}")
        print(f"   Fair Value:       ${val['fair_value']:.2f}")
        print(f"   Buy Price (40%):  ${val['buy_price']:.2f}")
        print(f"   Current Price:    ${val['current_price']:.2f}")
        
        discount = ((val['fair_value'] - val['current_price']) / val['current_price'] * 100) if val['current_price'] > 0 else 0
        print(f"\n   Desconto:         {discount:.2f}%")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def example_3_quality_score():
    """Exemplo 3: Apenas quality score"""
    print("\n" + "="*70)
    print("EXEMPLO 3: Apenas Quality Score")
    print("="*70 + "\n")
    
    client = AgentFundamentClient()
    
    try:
        qual = client.get_quality_score("GOOGL")
        
        print(f"📊 {qual['ticker']}")
        print(f"   Score: {qual['score']:.1f}/100 - {qual['interpretation']}")
        print(f"\n   Métricas:")
        
        metrics = qual['metrics']
        print(f"      ROE:              {metrics['roe']:.2%}")
        print(f"      Current Ratio:    {metrics['current_ratio']:.2f}")
        print(f"      Debt/Equity:      {metrics['debt_to_equity']:.2f}")
        print(f"      Profit Margin:    {metrics['profit_margin']:.2%}")
        print(f"      Revenue Growth:   {metrics['revenue_growth']:.2%}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def example_4_compare():
    """Exemplo 4: Comparar múltiplas ações"""
    print("\n" + "="*70)
    print("EXEMPLO 4: Comparação de Ações")
    print("="*70 + "\n")
    
    client = AgentFundamentClient()
    
    try:
        tickers = ["AAPL", "MSFT", "GOOGL"]
        comparison = client.compare(tickers)
        
        stocks = comparison['comparison']
        
        # Cabeçalho
        print(f"{'Ticker':<10} {'Preço':<12} {'Fair Value':<12} {'Score':<8} {'Desconto':<10}")
        print("-" * 60)
        
        # Dados
        for stock in stocks:
            if 'error' not in stock:
                print(f"{stock['ticker']:<10} ${stock['current_price']:<11.2f} ${stock['fair_value']:<11.2f} {stock['quality_score']:<7.1f} {stock['discount_percent']:<9.2f}%")
            else:
                print(f"{stock['ticker']:<10} {stock['error']}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def example_5_monitor():
    """Exemplo 5: Monitorar ações em tempo real"""
    print("\n" + "="*70)
    print("EXEMPLO 5: Monitorar Ações (Simulado)")
    print("="*70 + "\n")
    
    client = AgentFundamentClient()
    tickers = ["AAPL", "MSFT"]
    
    print(f"Monitorando: {', '.join(tickers)}\n")
    
    try:
        import time
        
        for i in range(2):  # Apenas 2 iterações para demo
            print(f"\n⏰ Atualização #{i+1} - {time.strftime('%H:%M:%S')}")
            print("-" * 60)
            
            for ticker in tickers:
                analysis = client.analyze(ticker)
                val = analysis['valuation']
                qual = analysis['quality']
                
                if val['current_price'] <= val['fair_value']:
                    status = "🟢 COMPRA"
                else:
                    status = "🔴 VENDA"
                
                print(f"{status} | {ticker:6} | Score: {qual['score']:5.1f} | Preço: ${val['current_price']:8.2f} vs Fair: ${val['fair_value']:8.2f}")
            
            if i < 1:
                print("Aguardando próxima atualização em 10 segundos...\n")
                time.sleep(10)
        
    except Exception as e:
        print(f"❌ Erro: {e}")


def example_6_batch_analysis():
    """Exemplo 6: Análise em lote"""
    print("\n" + "="*70)
    print("EXEMPLO 6: Análise em Lote")
    print("="*70 + "\n")
    
    client = AgentFundamentClient()
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    
    results = []
    
    print("Analisando portfólio...\n")
    
    for ticker in tickers:
        try:
            analysis = client.analyze(ticker)
            results.append(analysis)
            print(f"✅ {ticker} analisado")
        except Exception as e:
            print(f"❌ {ticker}: {e}")
    
    # Resumo
    print(f"\n{'='*70}")
    print("RESUMO DO PORTFÓLIO")
    print(f"{'='*70}\n")
    
    if results:
        # Classificar por score
        results_sorted = sorted(results, key=lambda x: x['quality']['score'], reverse=True)
        
        print(f"{'Ticker':<10} {'Score':<8} {'Recomendação':<40} {'Desconto':<10}")
        print("-" * 70)
        
        for r in results_sorted:
            val = r['valuation']
            qual = r['quality']
            discount = ((val['fair_value'] - val['current_price']) / val['current_price'] * 100) if val['current_price'] > 0 else 0
            
            rec = r['recommendation'][:38]
            print(f"{r['ticker']:<10} {qual['score']:<7.1f} {rec:<40} {discount:<9.2f}%")


def main():
    """Menu principal"""
    print("\n" + "="*70)
    print("🚀 AGENT FUNDAMENT - CLIENTE PYTHON")
    print("="*70)
    print("\nEscolha um exemplo para executar:")
    print("1. Análise completa de uma ação")
    print("2. Apenas valuation")
    print("3. Apenas quality score")
    print("4. Comparar múltiplas ações")
    print("5. Monitorar ações (demo)")
    print("6. Análise em lote (portfólio)")
    print("0. Sair")
    
    choice = input("\nOpção: ").strip()
    
    if choice == "1":
        example_1_single_analysis()
    elif choice == "2":
        example_2_valuation_only()
    elif choice == "3":
        example_3_quality_score()
    elif choice == "4":
        example_4_compare()
    elif choice == "5":
        example_5_monitor()
    elif choice == "6":
        example_6_batch_analysis()
    elif choice == "0":
        print("Até logo!")
        return
    else:
        print("Opção inválida!")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
