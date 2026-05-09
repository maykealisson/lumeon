# Agent Fundament - Análise Fundamentalista de Investimentos

Ferramenta para análise fundamentalista de ações com cálculo de preço justo (Fair Value) e score de qualidade baseado em métricas reais de mercado.

---

## 📋 Configuração Inicial

### Criar ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

### Ativar ambiente (toda vez que for usar o projeto)

```bash
source .venv/bin/activate
```

### Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 🚀 Uso Rápido

### Opção 1: CLI (Interativo)

```bash
python main.py
```

Digite o ticker (ex: AAPL, PETR4.SA) e receba a análise completa.

### Opção 2: API REST (Recomendado)

```bash
python -m uvicorn api:app --reload
```

Acesse a documentação interativa em: **http://localhost:8000/docs**

### Opção 3: Cliente Python

```bash
python client_example.py
```

Menu interativo com 6 exemplos de uso.

---

## 🌐 API REST

A API oferece endpoints para análise de ações:

| Endpoint              | Método | Descrição                |
| --------------------- | ------ | ------------------------ |
| `/health`             | GET    | Status da API            |
| `/valuation/{ticker}` | GET    | Preço justo              |
| `/quality/{ticker}`   | GET    | Quality score            |
| `/analyze/{ticker}`   | GET    | Análise completa         |
| `/compare`            | GET    | Comparar múltiplas ações |

### Exemplo de uso

```bash
# Análise completa
curl http://localhost:8000/analyze/AAPL

# Comparar ações
curl "http://localhost:8000/compare?tickers=AAPL,MSFT,GOOGL"
```

📖 **Documentação completa**: [API.md](API.md)

---

## 🎯 Como Funciona

Este projeto utiliza dois engines principais:

### 1️⃣ **Valuation Engine** - Cálculo do Preço Justo

Estima o valor intrínseco da ação usando duas metodologias:

#### **A) Fluxo de Caixa Descontado (DCF)**

**Princípio**: Uma ação vale a soma de todos os fluxos de caixa futuros trazidos a valor presente.

**Regras aplicadas:**

- **Projeção**: 10 anos de crescimento de fluxo de caixa livre
- **Crescimento decrescente**:
  - Anos 1-2: 10% e 9% (fase de expansão)
  - Anos 3-5: 8%, 7%, 6% (maturação)
  - Anos 6-10: 5%, 4%, 3%, 2.5%, 2.5% (estabilização)
- **Taxa de desconto (dinâmica):**
  - **EUA**: Calculada via CAPM (Beta × Prêmio de risco), limitada entre 7% e 12%
  - **Brasil**: Fixa em 13% (risco-país maior)
- **Crescimento perpétuo**: 2.5% (perpetuidade após ano 10)

- **Cálculo de FCF corrigido**:
  ```
  FCF = Operating Cash Flow - Capital Expenditure
  ```
  (Evita superestimar caixa disponível)

#### **B) Múltiplos de Mercado (P/L comparativo)**

**Princípio**: Comparar com empresas similares e ajustar por qualidade.

**Regras aplicadas:**

- **P/E justo base:**
  - 🇺🇸 EUA: 16-20x (ajustado por ROE)
  - 🇧🇷 Brasil: 10-15x (ajustado por ROE)
- **Ajuste por qualidade (ROE):**
  - ROE > 15%: Use P/E máximo (20 EUA / 15 Brasil)
  - ROE > 10%: Use P/E médio (18 EUA / 12 Brasil)
  - ROE ≤ 10%: Use P/E mínimo (16 EUA / 10 Brasil)

#### **Fair Value Final**

```
Fair Value = Média(DCF, Múltiplos)
Buy Price = Fair Value × 0.60  (40% de desconto para margem de segurança)
```

**Margem de Segurança de 40%** = Você só compra se a ação está 40% mais barata que o valor justo (proteção contra erros de análise).

---

### 2️⃣ **Quality Score** - Avaliação Fundamentalista (0-100)

Pontuação integrada que mede a qualidade fundamental da empresa em 5 dimensões:

| Métrica             | Peso | O que avalia                                                             |
| ------------------- | ---- | ------------------------------------------------------------------------ |
| **ROE**             | 25%  | Rentabilidade do patrimônio (quanto lucra com o dinheiro dos acionistas) |
| **Liquidez**        | 20%  | Current Ratio (consegue pagar contas no curto prazo?)                    |
| **Endividamento**   | 20%  | Debt/Equity (qual proporção de dívida vs patrimônio?)                    |
| **Margem de Lucro** | 15%  | Quanto lucra em cada real vendido?                                       |
| **Crescimento**     | 10%  | Revenue Growth (receita está crescendo?)                                 |

#### **Critérios de Pontuação por Métrica**

**ROE (Retorno sobre Patrimônio)**

- > 20%: 100 pontos ⭐⭐⭐
- 15% - 20%: 85 pontos ⭐⭐
- 10% - 15%: 70 pontos ⭐
- 5% - 10%: 50 pontos
- < 5%: 20 pontos ❌

**Current Ratio (Liquidez)**

- ≥ 2.0: 100 pontos (excelente saúde de caixa)
- 1.5 - 2.0: 85 pontos
- 1.0 - 1.5: 70 pontos (saudável)
- 0.8 - 1.0: 40 pontos ⚠️ (risco)
- < 0.8: 10 pontos ❌❌ (pode falir)

**Debt/Equity (Alavancagem)**

- < 30%: 100 pontos (muito conservadora)
- 30% - 50%: 85 pontos
- 50% - 100%: 70 pontos (normal)
- 100% - 150%: 40 pontos ⚠️ (endividada)
- > 150%: 10 pontos ❌❌ (alta exposição ao risco)

**Margem de Lucro**

- > 20%: 100 pontos (excelente eficiência)
- 15% - 20%: 85 pontos
- 10% - 15%: 70 pontos
- 5% - 10%: 50 pontos
- < 5%: 20 pontos (margem apertada)

**Revenue Growth (Crescimento)**

- > 20%: 100 pontos (crescimento forte)
- 10% - 20%: 85 pontos
- 5% - 10%: 70 pontos
- 0% - 5%: 50 pontos (crescimento lento)
- < 0%: 30 pontos ❌ (estagnação/queda)

#### **Penalizações Severas**

Se a empresa tem:

- Current Ratio < 0.8 **OU** Debt/Equity > 200%
- → Score máximo fica **limitado a 35 pontos** (alto risco de solvência)

---

## 📊 Como Interpretar o Retorno

### **Saída do Sistema**

```
Valor justo calculado pelo Fluxo de Caixa Descontado: $150.50
Valor estimado com base em comparações de mercado: $145.75
Valor Justo (Fair Value): $148.13
Preço de Compra (Margem de Segurança): $88.88

Quality Score: 72.5/100
```

### **Interpretação do Fair Value**

| Preço Atual | Fair Value | Recomendação        | Sinal                            |
| ----------- | ---------- | ------------------- | -------------------------------- |
| $50         | $148       | **COMPRA FORTE** 🟢 | 66% abaixo = Grande oportunidade |
| $85         | $148       | **COMPRA** 🟢       | 42% abaixo = Boa margem          |
| $100        | $148       | **TALVEZ** 🟡       | 32% abaixo = Esperar desconto    |
| $148        | $148       | **JUSTO** ⚪        | Preço correto                    |
| $160        | $148       | **VENDA** 🔴        | 8% acima = Sobrepreço            |
| $200        | $148       | **VENDA FORTE** 🔴  | 35% acima = Bolha                |

### **Interpretação do Quality Score**

```
85-100  👑 EXCELENTE    Empresa de qualidade comprovada (Apple, Coca-Cola)
70-85   ✓✓ MUITO BOM    Boa empresa, fundamentals sólidos
50-70   ✓  BOM          Empresa aceitável, alguns pontos de atenção
30-50   ⚠️ FRACO        Empresa com problemas, evitar
0-30    ❌ PÉSSIMO      Alto risco, não comprar
```

### **Estratégia de Decisão**

```
1. Score ≥ 70 E Preço ≤ Buy Price → COMPRA RECOMENDADA ✅
2. Score ≥ 70 E Preço > Fair Value → AGUARDE desconto
3. Score < 50 → NÃO COMPRAR, independente do preço
4. Score ≥ 50 E Current Ratio < 0.8 → EVITAR (risco de falência)
5. Score ≥ 50 E Debt/Equity > 200% → RISCO ALTO, cauteloso
```

---

## 🚀 Uso Prático

### Executar análise via CLI

```bash
python main.py
```

### Iniciar API REST

```bash
python -m uvicorn api:app --reload
```

Acesse a documentação interativa em: **http://localhost:8000/docs**

### Testar com cliente Python

```bash
python client_example.py
```

---

## 🏗️ Docker

### Build local

```bash
docker build -t agent-fundament .
docker run -p 8000:8000 agent-fundament
```

### Docker Compose (Recomendado)

```bash
docker-compose up
```

A API ficará disponível em: http://localhost:8000

### Parar container

```bash
docker-compose down
```

### Gerar imagem para publicar

```bash
docker buildx build --platform=linux/arm64/v8 -t maykealisson/agent-fundament:{{VERSION}} .
docker push maykealisson/agent-fundament:{{VERSION}}
```

---

## 📚 Referências Conceituais

- **DCF (Descounted Cash Flow)**: Benjamin Graham, "The Intelligent Investor"
- **Margem de Segurança**: 40-50% é recomendado para investidores amadores
- **P/E Justo**: Varia por setor, ROE e crescimento esperado
- **CAPM**: Modelo de precificação de ativos de capital
- **Current Ratio**: Métrica clássica de liquidez (> 1.0 é seguro)

---

## ⚠️ Disclaimer

Esta ferramenta fornece análise fundamentalista educacional. Não é recomendação de investimento. Sempre consulte um assessor financeiro antes de tomar decisões de investimento.
