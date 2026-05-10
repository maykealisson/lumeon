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

### 2️⃣ **Quality Score v2.0** - Avaliação Fundamentalista (0-100)

Pontuação integrada que mede a qualidade fundamental da empresa em **10 critérios essenciais** com ponderação científica:

| #   | Critério                   | Peso | O que avalia                                        |
| --- | -------------------------- | ---- | --------------------------------------------------- |
| 1   | **Tempo em Bolsa**         | 5%   | Empresa listada há +5 anos (experiência)            |
| 2   | **Profitabilidade**        | 20%  | Lucro em todos os últimos 20 trimestres (5 anos)    |
| 3   | **Crescimento de Lucros**  | 15%  | Lucros crescentes nos últimos 5 anos (tendência)    |
| 4   | **Crescimento de Receita** | 10%  | Receita crescente nos últimos 5 anos (expansão)     |
| 5   | **Dividendos**             | 10%  | Yield >5% a.a. nos últimos 5 anos (rentabilidade)   |
| 6   | **ROE**                    | 15%  | Rentabilidade do patrimônio >10% (eficiência)       |
| 7   | **Dívida/Patrimônio**      | 10%  | Dívida < patrimônio (alavancagem controlada)        |
| 8   | **Liquidez Diária**        | 5%   | Volume >US$ 2M/dia (facilita compra/venda)          |
| 9   | **Liquidez Corrente**      | 5%   | Current Ratio adequado (paga contas no curto prazo) |
| 10  | **Margem de Lucro**        | 5%   | Quanto lucra em cada real vendido (eficiência)      |

#### **Critérios de Pontuação Detalhados**

**1. Tempo em Bolsa (5%)**

- ≥ 5 anos: 100 pontos ✓
- < 5 anos: 30 pontos (empresa jovem)

**2. Profitabilidade (20%)**

- Lucrativa em todos os 20Q: 100 pontos ⭐
- Lucrativa em 18-19Q: 80 pontos
- Lucrativa em 15-17Q: 60 pontos
- Lucrativa em <15Q: 30 pontos ❌

**3. Crescimento de Lucros (15%)**

- Lucro crescente 5Y: 100 pontos ⭐
- Lucro estagnado/decrescente: 20 pontos ❌

**4. Crescimento de Receita (10%)**

- Receita crescente 5Y: 100 pontos ⭐
- Receita estagnada/decrescente: 20 pontos ❌

**5. Dividendos (10%)**

- Yield ≥ 5% a.a.: 100 pontos ✓✓
- Yield 3-5%: 70 pontos ✓
- Yield < 3%: 40 pontos
- Sem dividendos: 20 pontos ❌

**6. ROE (15%) - Retorno sobre Patrimônio**

- > 20%: 100 pontos ⭐⭐⭐
- 15% - 20%: 85 pontos ⭐⭐
- 10% - 15%: 70 pontos ⭐
- 5% - 10%: 50 pontos
- < 5%: 20 pontos ❌

**7. Dívida/Patrimônio (10%)**

- < 50%: 100 pontos (excelente)
- 50% - 100%: 85 pontos ✓
- 100% - 150%: 50 pontos ⚠️
- > 150%: 20 pontos ❌❌

**8. Liquidez Diária (5%)**

- > US$ 2M/dia: 100 pontos ✓
- US$ 500K - 2M: 70 pontos
- < US$ 500K: 30 pontos ⚠️

**9. Current Ratio (5%) - Liquidez Corrente**

- ≥ 2.0: 100 pontos (excelente)
- 1.5 - 2.0: 85 pontos
- 1.0 - 1.5: 70 pontos ✓
- 0.8 - 1.0: 40 pontos ⚠️
- < 0.8: 10 pontos ❌❌

**10. Margem de Lucro (5%)**

- > 20%: 100 pontos ⭐
- 15% - 20%: 85 pontos
- 10% - 15%: 70 pontos
- 5% - 10%: 50 pontos
- < 5%: 20 pontos ❌

#### **Campo "Interpretation" - Insights Inteligentes**

O sistema retorna o **maior ponto positivo OU o maior alerta** específico da empresa:

**Exemplos de Interpretações Positivas:**

```
✓ Empresa com +5 anos em Bolsa
✓ ROE acima de 20%
✓ Dívida menor que 50% do patrimônio
✓ Receita em crescimento nos últimos 5 anos (+40%)
✓ Lucro em crescimento nos últimos 5 anos (+87%)
✓ Liquidez diária alta ($1,500M)
```

**Exemplos de Alertas:**

```
❌ Risco de insolvência (Current Ratio: 0.71)
⚠️ ROE baixo (6.8%)
⚠️ Margem de lucro baixa (7.3%)
⚠️ Sem histórico de dividendos recentes
❌ Receita decrescente ou estagnada
❌ Lucro decrescente ou instável
```

#### **Penalizações Severas**

Se a empresa tem:

- Current Ratio < 0.8 **OU** Debt/Equity > 200%
- → Score máximo fica **limitado a 35 pontos** (alto risco de solvência)

#### **Dados Coletados Automaticamente**

O sistema coleta dados históricos via yfinance:

- ✅ **5 anos de dados anuais**: receita, lucro líquido
- ✅ **20 trimestres de dados**: profitabilidade trimestral
- ✅ **Histórico de dividendos**: yield calculation
- ✅ **Dados de mercado**: IPO date, volume diário, preço

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

### **Interpretação do Quality Score v2.0**

```
85-100  👑 EXCELENTE    Empresa excelente com fundamentals robustos (Apple, Microsoft)
70-85   ✓✓ MUITO BOM    Boa empresa, qualidade comprovada
50-70   ✓  BOM          Empresa aceitável, alguns pontos de atenção
30-50   ⚠️ FRACO        Empresa com problemas significativos, avaliar bem
0-30    ❌ PÉSSIMO      Alto risco, evitar
```

**Campo "interpretation":**

- Se houver alertas críticos: exibe o alerta principal (ex: "❌ Risco de insolvência")
- Se houver apenas pontos positivos: exibe o principal diferencial (ex: "✓ ROE acima de 20%")

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

### Testar novo sistema de score

```bash
# Teste direto do score engine com múltiplas ações
python test_new_score.py

# Teste de integração da API completa
python test_api_integration.py
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

## 🎉 Novidades v2.0

**Quality Score System Melhorado:**

- ✅ Aumentado de 5 para **10 critérios** de avaliação
- ✅ Coleta automática de **dados históricos de 5 anos**
- ✅ Campo "interpretation" retorna **insights específicos** (maior positivo ou maior alerta)
- ✅ Análise de **20 trimestres** de profitabilidade
- ✅ Avaliação de **tendências de crescimento**
- ✅ Cálculo de **dividend yield** em 5 anos

**Veja:** [IMPROVEMENTS.md](IMPROVEMENTS.md) para detalhes técnicos das mudanças.

---

Esta ferramenta fornece análise fundamentalista educacional. Não é recomendação de investimento. Sempre consulte um assessor financeiro antes de tomar decisões de investimento.
