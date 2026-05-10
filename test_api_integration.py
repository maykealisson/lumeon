#!/usr/bin/env python3
"""
Script para testar a API completa com a nova lógica de score
"""

import requests
import json
import time

API_URL = "http://localhost:8000"

def test_api():
    print("\n" + "="*70)
    print("🧪 TESTE DE INTEGRAÇÃO - API AGENT FUNDAMENT")
    print("="*70)
    
    # Test 1: Health Check
    print("\n📋 1. Health Check")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ API está operacional")
            print(f"   Resposta: {response.json()}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Não foi possível conectar à API. Inicie o servidor com:")
        print("      python -m uvicorn api:app --reload")
        return
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return
    
    # Test 2: Quality Score
    print("\n📊 2. Quality Score (AAPL)")
    try:
        response = requests.get(f"{API_URL}/quality/AAPL", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Score: {data['score']}/100")
            print(f"   Interpretação: {data['interpretation']}")
            print(f"   Métricas principais:")
            for key, value in data['metrics'].items():
                if isinstance(value, float):
                    print(f"      - {key}: {value:.2f}")
                else:
                    print(f"      - {key}: {value}")
        else:
            print(f"   ❌ Erro: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # Test 3: Valuation
    print("\n💰 3. Valuation (MSFT)")
    try:
        response = requests.get(f"{API_URL}/valuation/MSFT", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Fair Value: ${data['fair_value']:.2f}")
            print(f"   Buy Price (40% desconto): ${data['buy_price']:.2f}")
            print(f"   Preço atual: ${data['current_price']:.2f}")
        else:
            print(f"   ❌ Erro: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # Test 4: Complete Analysis
    print("\n📈 4. Análise Completa (PETR4.SA)")
    try:
        response = requests.get(f"{API_URL}/analyze/PETR4.SA", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Ticker: {data['ticker']}")
            print(f"   Score: {data['quality']['score']}/100")
            print(f"   Interpretação: {data['quality']['interpretation']}")
            print(f"   Fair Value: ${data['valuation']['fair_value']:.2f}")
            print(f"   Recomendação: {data['recommendation']}")
        else:
            print(f"   ❌ Erro: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # Test 5: Comparison
    print("\n🔄 5. Comparação (AAPL, MSFT, PETR4.SA)")
    try:
        response = requests.get(f"{API_URL}/compare?tickers=AAPL,MSFT,PETR4.SA", timeout=20)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Comparação realizada:")
            for stock in data['comparison']:
                if 'error' not in stock:
                    print(f"      {stock['ticker']:8} | Score: {stock['quality_score']:6.1f} | Desconto: {stock['discount_percent']:6.2f}%")
                else:
                    print(f"      {stock['ticker']:8} | Erro: {stock['error']}")
        else:
            print(f"   ❌ Erro: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ Testes concluídos!")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n🚀 Iniciando testes da API...")
    print("Aguarde alguns segundos para cada requisição...")
    test_api()
