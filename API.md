# 🚀 Agent Fundament API - Documentação

API REST para análise fundamentalista de ações com cálculo de preço justo e score de qualidade.

---

## 📋 Índice

- [Instalação](#instalação)
- [Iniciar a API](#iniciar-a-api)
- [Endpoints](#endpoints)
- [Exemplos](#exemplos)
- [Resposta de Erro](#resposta-de-erro)

---

## 📦 Instalação

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Dependências necessárias

O arquivo `requirements.txt` contém:

- `fastapi` - Framework para API REST
- `uvicorn` - Servidor ASGI
- `pydantic` - Validação de dados
- `yfinance` - Dados de ações
- `pandas`, `numpy`, `requests`

---

## 🚀 Iniciar a API

### Iniciar servidor

```bash
python -m uvicorn api:app --reload
```

Saída esperada:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Acessar documentação interativa

Abra no navegador:

```
http://localhost:8000/docs
```

Ou use Swagger UI:

```
http://localhost:8000/swagger-ui
```

---

## 📡 Endpoints

### 1. Health Check

**GET** `/health`

Verifica se a API está funcionando.

**Resposta:**

```json
{
  "status": "healthy",
  "message": "API de análise fundamentalista está operacional"
}
```

**cURL:**

```bash
curl http://localhost:8000/health
```

---

### 2. Valuation (Preço Justo)

**GET** `/valuation/{ticker}`

Calcula o preço justo de uma ação usando DCF e múltiplos.

**Parâmetros:**

- `ticker` (string, obrigatório): Símbolo da ação
  - Exemplo: `AAPL` (Apple)
  - Exemplo: `PETR4.SA` (Petrobras)

**Resposta:**

```json
{
  "ticker": "AAPL",
  "dcf_value": 150.5,
  "multiples_value": 145.75,
  "fair_value": 148.13,
  "buy_price": 88.88,
  "current_price": 180.5
}
```

**Campos:**

- `dcf_value`: Valor calculado via Fluxo de Caixa Descontado
- `multiples_value`: Valor via múltiplos de mercado (P/L, etc)
- `fair_value`: Média dos dois métodos
- `buy_price`: Preço com 40% de margem de segurança
- `current_price`: Preço atual na bolsa

**cURL:**

```bash
curl http://localhost:8000/valuation/AAPL
```

**Python:**

```python
import requests

response = requests.get("http://localhost:8000/valuation/AAPL")
data = response.json()
print(f"Fair Value: ${data['fair_value']}")
print(f"Preço Atual: ${data['current_price']}")
```

---

### 3. Quality Score (Score Fundamentalista)

**GET** `/quality/{ticker}`

Calcula o score de qualidade fundamental (0-100) com base em 10 critérios essenciais.

**Resposta:**

```json
{
  "ticker": "AAPL",
  "score": 72.5,
  "interpretation": "✓ Empresa com +5 anos em Bolsa",
  "metrics": {
    "roe": 0.85,
    "current_ratio": 1.54,
    "debt_to_equity": 2.16,
    "profit_margin": 0.29,
    "revenue_growth": 0.06
  }
}
```

**Critérios Avaliados:**

O score leva em consideração 10 pontos fundamentais:

1. **Empresa com mais de 5 anos em Bolsa** - 5% da pontuação
2. **Nunca deu prejuízo (ano fiscal)** - Incluso na profitabilidade
3. **Lucro nos últimos 20 trimestres (5 anos)** - 20% da pontuação
4. **Pagou +5% de dividendos/ano (últimos 5 anos)** - 10% da pontuação
5. **ROE acima de 10%** - 15% da pontuação
6. **Dívida menor que patrimônio** - 10% da pontuação
7. **Crescimento de receita (últimos 5 anos)** - 10% da pontuação
8. **Crescimento de lucros (últimos 5 anos)** - 15% da pontuação
9. **Liquidez diária acima de US$ 2M** - 5% da pontuação
10. **Liquidez corrente (current ratio)** - 5% da pontuação

**Interpretação do Score:**

- **85-100**: 👑 EXCELENTE - Empresa excelente, qualidade comprovada
- **70-85**: ✓✓ MUITO BOM - Boa empresa, fundamentals sólidos
- **50-70**: ✓ BOM - Empresa aceitável, alguns pontos de atenção
- **30-50**: ⚠️ FRACO - Empresa com problemas, evitar
- **0-30**: ❌ PÉSSIMO - Alto risco, não comprar

**Campo "interpretation":**

O campo retorna o **maior ponto positivo** ou o **maior alerta** identificado na análise:

- Se houver alertas: exibe o alerta mais crítico
- Se não houver alertas: exibe o maior ponto positivo

**Exemplo de Interpretações:**

```
✓ Empresa com +5 anos em Bolsa
✓ ROE acima de 20%
❌ Risco de insolvência (Current Ratio: 0.71)
⚠️ Sem histórico de dividendos recentes ou yield = 0
✓ Receita em crescimento nos últimos 5 anos (+40%)
✓ Lucro em crescimento nos últimos 5 anos (+87%)
```

**cURL:**

```bash
curl http://localhost:8000/quality/AAPL
```

---

### 4. Análise Completa

**GET** `/analyze/{ticker}`

Análise integrada: valuation + quality score + recomendação.

**Resposta:**

```json
{
  "ticker": "AAPL",
  "valuation": {
    "ticker": "AAPL",
    "dcf_value": 150.5,
    "multiples_value": 145.75,
    "fair_value": 148.13,
    "buy_price": 88.88,
    "current_price": 180.5
  },
  "quality": {
    "ticker": "AAPL",
    "score": 85.5,
    "interpretation": "👑 EXCELENTE - Empresa de qualidade comprovada",
    "metrics": {
      "roe": 0.85,
      "current_ratio": 1.54,
      "debt_to_equity": 2.16,
      "profit_margin": 0.29,
      "revenue_growth": 0.06
    }
  },
  "recommendation": "🟡 AGUARDE - Boa qualidade mas preço acima do justo"
}
```

**Recomendações:**

- 🟢 COMPRA RECOMENDADA: Score ≥ 70 + Preço ≤ Buy Price
- 🟡 AGUARDE: Score ≥ 70 + Preço > Fair Value
- ❌ NÃO COMPRAR: Score < 50
- 🔴 VENDA: Preço muito acima + Score baixo

**cURL:**

```bash
curl http://localhost:8000/analyze/AAPL
```

**Python:**

```python
import requests

response = requests.get("http://localhost:8000/analyze/AAPL")
analysis = response.json()

print(f"Ticker: {analysis['ticker']}")
print(f"Score: {analysis['quality']['score']}")
print(f"Recomendação: {analysis['recommendation']}")
```

---

### 5. Comparação de Ações

**GET** `/compare?tickers=AAPL,MSFT,PETR4.SA`

Compara múltiplas ações lado a lado.

**Parâmetros:**

- `tickers` (string, obrigatório): Símbolos separados por vírgula
  - Máximo: 10 tickers por requisição

**Resposta:**

```json
{
  "comparison": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "current_price": 180.5,
      "fair_value": 148.13,
      "buy_price": 88.88,
      "quality_score": 85.5,
      "discount_percent": -21.86
    },
    {
      "ticker": "MSFT",
      "company_name": "Microsoft Corporation",
      "current_price": 380.5,
      "fair_value": 350.0,
      "buy_price": 210.0,
      "quality_score": 82.3,
      "discount_percent": 8.1
    }
  ]
}
```

**cURL:**

```bash
curl "http://localhost:8000/compare?tickers=AAPL,MSFT,PETR4.SA"
```

**Python:**

```python
import requests

tickers = "AAPL,MSFT,PETR4.SA"
response = requests.get(f"http://localhost:8000/compare?tickers={tickers}")
comparison = response.json()

for stock in comparison['comparison']:
    print(f"{stock['ticker']:8} | Score: {stock['quality_score']:5.1f} | Desconto: {stock['discount_percent']:6.2f}%")
```

---

## 💡 Exemplos

### Exemplo 1: Analisar uma ação via Python

```python
import requests

def analyze_stock(ticker):
    response = requests.get(f"http://localhost:8000/analyze/{ticker}")

    if response.status_code == 200:
        data = response.json()

        val = data['valuation']
        qual = data['quality']

        print(f"\n{'='*60}")
        print(f"📊 {data['ticker']}")
        print(f"{'='*60}")
        print(f"\nPreço Atual:        ${val['current_price']:.2f}")
        print(f"Preço Justo:        ${val['fair_value']:.2f}")
        print(f"Preço de Compra:    ${val['buy_price']:.2f}")
        print(f"\nQuality Score:      {qual['score']:.1f}/100")
        print(f"Interpretação:      {qual['interpretation']}")
        print(f"\n💡 {data['recommendation']}")
        print(f"{'='*60}\n")
    else:
        print(f"Erro: {response.json()}")

# Testar
analyze_stock("AAPL")
```

### Exemplo 2: Comparar múltiplas ações

```python
import requests
import pandas as pd

def compare_stocks(tickers):
    response = requests.get(f"http://localhost:8000/compare?tickers={','.join(tickers)}")

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data['comparison'])

        # Ordenar por score descendente
        df = df.sort_values('quality_score', ascending=False)

        print("\n📊 COMPARAÇÃO DE AÇÕES\n")
        print(df[['ticker', 'current_price', 'fair_value', 'quality_score', 'discount_percent']].to_string(index=False))
    else:
        print(f"Erro: {response.json()}")

# Testar
compare_stocks(["AAPL", "MSFT", "GOOGL"])
```

### Exemplo 3: Monitorar múltiplas ações

```python
import requests
import time

def monitor_stocks(tickers, interval=300):
    """Monitora ações a cada 5 minutos"""

    while True:
        print(f"\n⏰ Atualização: {time.strftime('%H:%M:%S')}\n")

        for ticker in tickers:
            response = requests.get(f"http://localhost:8000/analyze/{ticker}")

            if response.status_code == 200:
                data = response.json()
                val = data['valuation']
                qual = data['quality']

                status = "🟢" if val['current_price'] <= val['fair_value'] else "🔴"
                print(f"{status} {ticker:10} | Preço: ${val['current_price']:8.2f} | Fair: ${val['fair_value']:8.2f} | Score: {qual['score']:5.1f}")

        print(f"\nPróxima atualização em {interval}s...")
        time.sleep(interval)

# Testar
# monitor_stocks(["AAPL", "MSFT", "PETR4.SA"])
```

---

## ❌ Resposta de Erro

Quando ocorre um erro, a API retorna:

```json
{
  "detail": "Ticker 'INVALID' não encontrado"
}
```

**Códigos HTTP:**

- `200`: Sucesso
- `400`: Erro na requisição (ticker inválido, sem dados)
- `404`: Recurso não encontrado
- `500`: Erro interno do servidor

**Exemplos de erro:**

Ticker não encontrado:

```bash
curl http://localhost:8000/valuation/INVALIDTICKER
# {"detail":"Ticker 'INVALIDTICKER' não encontrado"}
```

Muitos tickers na comparação:

```bash
curl "http://localhost:8000/compare?tickers=AAPL,MSFT,GOOGL,AMZN,TSLA,META,NVDA,AMD,NFLX,GOOG,INTC"
# {"detail":"Máximo de 10 tickers por comparação"}
```

---

## 🔌 Integração com Terceiros

### Exemplo com JavaScript/Node.js

```javascript
async function getAnalysis(ticker) {
  const response = await fetch(`http://localhost:8000/analyze/${ticker}`);
  const data = await response.json();

  console.log(`Ticker: ${data.ticker}`);
  console.log(`Score: ${data.quality.score}/100`);
  console.log(`Recomendação: ${data.recommendation}`);

  return data;
}

// Uso
getAnalysis("AAPL").then((data) => console.log(data));
```

### Exemplo com Shell Script

```bash
#!/bin/bash

TICKER=$1
API_URL="http://localhost:8000/analyze/${TICKER}"

echo "Analisando $TICKER..."

curl -s "$API_URL" | jq '{
  ticker: .ticker,
  current_price: .valuation.current_price,
  fair_value: .valuation.fair_value,
  quality_score: .quality.score,
  recommendation: .recommendation
}'
```

---

## 📚 Deployment

### Docker

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Executar com Docker

```bash
docker build -t agent-fundament .
docker run -p 8000:8000 agent-fundament
```

---

## ⚠️ Disclaimer

Esta API fornece análise fundamentalista educacional. Não é recomendação de investimento. Sempre consulte um assessor financeiro antes de tomar decisões de investimento.
