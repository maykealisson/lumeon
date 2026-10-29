# Agent Fundament - Análise Fundamentalista de Investimentos

Ferramenta para análise fundamentalista de ações com cálculo de preço justo (Fair Value) e score de qualidade baseado em métricas reais de mercado (dados via [yfinance](https://github.com/ranaroussi/yfinance)).

Pode ser usada de três formas: **API REST** (FastAPI), **CLI interativo** ou **cliente Python**.

---

## 📦 Pré-requisitos

| Ferramenta         | Versão  | Observação                                            |
| ------------------ | ------- | ----------------------------------------------------- |
| Python             | 3.11+   | Testado com 3.12.2 (pyenv)                            |
| Docker + Compose   | recente | Apenas se for subir via Docker                        |
| Acesso à internet  | —       | Os dados vêm do Yahoo Finance em tempo real           |

---

## ⚙️ Configuração local

```bash
# 1. Criar o ambiente virtual (só na primeira vez)
python -m venv .venv

# 2. Ativar o ambiente (toda vez que abrir um terminal novo)
source .venv/bin/activate

# 3. Instalar / atualizar dependências (repita sempre que o requirements.txt mudar)
pip install -r requirements.txt
```

---

## 🚀 Subindo o projeto

### Opção 1: API REST local (recomendado para desenvolvimento)

```bash
source .venv/bin/activate
cp .env.example .env   # só na primeira vez; preencha MYSQL_PASSWORD
python -m uvicorn api:app --reload
```

> O MySQL do liberty precisa estar de pé: a API cria o banco `fundament` e as tabelas na subida.

Saída esperada:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

- Swagger (documentação interativa): **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

Para usar outra porta: `python -m uvicorn api:app --reload --port 8001`.

### Opção 2: Docker Compose

```bash
docker compose up --build
```

Sobe a API em http://localhost:8000.

> Use `--build` sempre que o `requirements.txt` mudar: o código é montado como volume, mas as dependências ficam na imagem.

```bash
docker compose down   # parar
```

### Opção 3: Docker sem Compose

```bash
docker build -t agent-fundament .
docker run -p 8000:8000 agent-fundament
```

### Opção 4: CLI interativo

```bash
python main.py
```

Digite o ticker (ex: `AAPL`, `PETR4.SA`) e receba a análise completa no terminal.

### Opção 5: Cliente Python de exemplo

Com a API rodando:

```bash
python client_example.py
```

Menu interativo com 6 exemplos de uso.

---

## 🌐 Endpoints

Base URL local: `http://localhost:8000`

| Endpoint              | Método | Descrição                          |
| --------------------- | ------ | ---------------------------------- |
| `/health`             | GET    | Status da API                      |
| `/valuation/{ticker}` | GET    | Preço justo (DCF + múltiplos)      |
| `/quality/{ticker}`   | GET    | Quality score (0-100)              |
| `/analyze/{ticker}`   | GET    | Valuation + quality + recomendação |
| `/compare?tickers=`   | GET    | Compara até 10 ações lado a lado   |
| `/ativos/{ticker}/analises` | POST | Envia uma análise em Markdown (.md) e grava no banco |
| `/ativos/{ticker}/analises` | GET | Lista as análises gravadas do ticker |
| `/ativos/{ticker}/relatorio` | GET | Processa as análises gravadas + cotação de hoje |
| `/analises/{id}`      | GET / DELETE | Detalhe completo / remoção de uma análise |

**Tickers:** ações americanas usam o símbolo puro (`AAPL`, `MSFT`); ações brasileiras usam o sufixo `.SA` (`PETR4.SA`, `ITUB4.SA`).

### `GET /health`

```bash
curl http://localhost:8000/health
```

```json
{ "status": "healthy", "message": "API de análise fundamentalista está operacional" }
```

### `GET /valuation/{ticker}`

```bash
curl http://localhost:8000/valuation/AAPL
```

```json
{
  "ticker": "AAPL",
  "dcf_value": 65.55,
  "multiples_value": 174.4,
  "fair_value": 119.97,
  "buy_price": 71.98,
  "current_price": 343.83
}
```

### `GET /quality/{ticker}`

```bash
curl http://localhost:8000/quality/PETR4.SA
```

```json
{
  "ticker": "PETR4.SA",
  "score": 76.0,
  "interpretation": "⚠️ Liquidez baixa (Current Ratio: 0.85)",
  "metrics": {
    "roe": 0.30274,
    "current_ratio": 0.854,
    "debt_to_equity": 76.067,
    "profit_margin": 0.24317,
    "revenue_growth": 0.423
  }
}
```

### `GET /analyze/{ticker}`

```bash
curl http://localhost:8000/analyze/AAPL
```

```json
{
  "ticker": "AAPL",
  "valuation": { "ticker": "AAPL", "dcf_value": 65.55, "multiples_value": 174.4, "fair_value": 119.97, "buy_price": 71.98, "current_price": 343.83 },
  "quality": { "ticker": "AAPL", "score": 71.0, "interpretation": "⚠️ Sem histórico de dividendos recentes ou yield = 0", "metrics": { "...": "..." } },
  "recommendation": "🟡 AGUARDE - Boa qualidade mas preço acima do justo"
}
```

### `GET /compare`

```bash
curl "http://localhost:8000/compare?tickers=AAPL,MSFT,PETR4.SA"
```

```json
{
  "comparison": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "current_price": 343.83,
      "fair_value": 119.97,
      "buy_price": 71.98,
      "quality_score": 71.0,
      "discount_percent": -65.11
    }
  ]
}
```

Tickers inválidos na comparação aparecem como `{"ticker": "XXX", "error": "Não encontrado"}` sem derrubar a requisição.

### Erros

| Status | Quando                                       | Exemplo de corpo                                  |
| ------ | -------------------------------------------- | ------------------------------------------------- |
| 404    | Ticker não existe                            | `{"detail": "Ticker 'XXX' não encontrado"}`       |
| 400    | Falha ao calcular / erro do Yahoo Finance    | `{"detail": "<mensagem do erro>"}`                |
| 422    | Parâmetro obrigatório ausente (`/compare`)   | validação do FastAPI                              |

📖 Mais detalhes: [API.md](API.md)

---

## 📝 Análises em Markdown

O front (tela de detalhe do ativo) envia, via gateway, o conteúdo de um arquivo de análise no
formato `TICKER_AAAA-MM-DD.md`: frontmatter YAML (`schema_version: 1`) seguido do texto da análise.
Exemplo completo em [`tests/fixtures/ITSA4_2026-10-29.md`](tests/fixtures/ITSA4_2026-10-29.md).

### Banco de dados

Usa o **mesmo servidor MySQL do liberty** (`liberty/docker-compose.yaml`), mas em um banco próprio,
`fundament`. Na subida, a API cria o banco (`CREATE DATABASE IF NOT EXISTS`) e as tabelas que faltarem;
o MySQL precisa estar de pé e o usuário precisa ter permissão de criar banco (o `root` tem).

Configuração por variáveis de ambiente (veja [`.env.example`](.env.example)):

| Variável | Padrão |
| --- | --- |
| `MYSQL_HOST` | `localhost` (no Docker Compose: `host.docker.internal`) |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | vazio — use a mesma senha do MySQL do liberty |
| `MYSQL_DATABASE` | `fundament` |
| `DATABASE_URL` | opcional; URL completa do SQLAlchemy, tem precedência |

```bash
cp .env.example .env   # preencha MYSQL_PASSWORD (o .env é lido automaticamente)
python -m uvicorn api:app --reload
```

Não há ferramenta de migração: `create_all` só cria tabelas novas. Se mudar colunas de uma tabela
existente, altere o banco manualmente (ou recrie o banco `fundament`).

| Tabela | Conteúdo |
| --- | --- |
| `analise` | Uma linha por ticker + `data_analise`: preço, valor intrínseco, margem, vereditos, nota do checklist, tese, texto de mudanças e o `.md` original |
| `analise_indicador` | Indicadores não nulos dos grupos `indicadores` e `setor_financeiro` |
| `analise_historico` | Série anual (`historico`) |
| `analise_checklist` | Respostas do checklist |
| `analise_ponto` | Itens do corpo: `POSITIVO`, `ATENCAO`, `RISCO`, `GATILHO_SAIDA`, `CONFERIR` |
| `analise_fonte` | URLs das fontes |

Reenviar o mesmo ticker com a mesma `data_analise` substitui o registro anterior.

### `POST /ativos/{ticker}/analises`

```json
{ "conteudo": "---\nschema_version: 1\nticker: ITSA4\n...", "nome_arquivo": "ITSA4_2026-10-29.md" }
```

Retorna `201` com o resumo e `substituida: true|false`. Retorna `422` se o arquivo não tiver
frontmatter, `ticker` ou `data_analise`, ou se o ticker do arquivo for diferente do da URL.

### `GET /ativos/{ticker}/relatorio?margem_desejada=20`

Usa a análise mais recente (e as anteriores, para evolução) e busca a cotação de hoje no Yahoo
Finance (o sufixo `.SA` é adicionado quando a moeda é BRL). Principais blocos da resposta:

- `preco`: atual, da análise, variação desde a análise, mínima/máxima de 52 semanas.
- `preco_justo`: valor intrínseco da análise, margem de segurança no preço de hoje
  (`1 − preço / valor intrínseco`), preço teto para a margem desejada, Graham, Bazin (DY 6%) e o
  valuation quantitativo das engines do projeto.
- `recomendacao`: `COMPRAR`, `ACUMULAR_COM_CAUTELA`, `AGUARDAR`, `CARO` ou `EVITAR`.
- `value_investing`: P/L, P/VP, DY e earnings yield da análise reajustados pelo preço de hoje,
  prêmio sobre a taxa de juros, ROE/ROIC contra o custo de capital, payout, CAGR, dívida.
- `pontos_positivos` / `pontos_atencao`: os da análise (`origem: analise`) mais os gerados no
  processamento (`origem: processamento`), como preço acima do justo ou análise desatualizada.
- `riscos`, `gatilhos_saida`, `dados_a_conferir`, `comparacao_anterior`, `evolucao`, `historico`.
- `avisos`: falhas parciais (ex: sem cotação; nesse caso usa o preço da análise).

> Os dividendos do yfinance para ações brasileiras são pouco confiáveis, por isso DY e Bazin vêm da análise.

---

## 🐳 Imagem Docker (produção)

Em produção a API sobe pelo `docker-compose.yaml` do **liberty** (serviço `agent-fundament`), na mesma
rede do MySQL (`MYSQL_HOST=mysql`). O gateway acessa via `URL_AGENT_FUNDAMENT=http://agent-fundament:8000`.

### Gerando imagem

```bash
docker buildx build --platform=linux/arm64/v8 -t maykealisson/agent-fundament:{VERSION} .
```

### Subindo imagem

```bash
docker push maykealisson/agent-fundament:{VERSION}
```

Ao publicar uma versão nova, atualize a tag em `liberty/docker-compose.yaml`.

---

## 🧪 Testes

```bash
# Testes automatizados (parser, banco e relatório; sem acesso à internet)
python -m pytest tests

# Score engine com múltiplas ações
python test_new_score.py

# Integração da API completa
python test_api_integration.py
```

---

## 🛠️ Troubleshooting

### `ImportError: ... Library not loaded: /opt/homebrew/opt/openssl@3/lib/libssl.3.dylib`

O Python instalado pelo pyenv foi compilado contra o `openssl@3` do Homebrew, e um `brew upgrade` o removeu (trocando por `openssl@4`). Sem SSL, nada que acesse a internet funciona (yfinance, pip). Corrija com:

```bash
brew install openssl@3
```

Ou recompile o Python: `pyenv uninstall 3.12.2 && pyenv install 3.12.2` (depois recrie o `.venv`).

### `ModuleNotFoundError: No module named '...'`

Dependências novas no `requirements.txt` que ainda não foram instaladas no venv:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

No Docker: `docker compose up --build`.

### `Address already in use` na porta 8000

Outra aplicação já usa a porta. Rode em outra porta: `python -m uvicorn api:app --reload --port 8001`.

### Requisições lentas / `Too Many Requests`

Os dados vêm do Yahoo Finance a cada chamada. Muitas chamadas seguidas podem ser limitadas pelo Yahoo; aguarde alguns minutos.

---

## 📤 Publicar imagem

```bash
docker buildx build --platform=linux/arm64/v8 -t maykealisson/agent-fundament:{{VERSION}} .
docker push maykealisson/agent-fundament:{{VERSION}}
```

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

---

Esta ferramenta fornece análise fundamentalista educacional. Não é recomendação de investimento. Sempre consulte um assessor financeiro antes de tomar decisões de investimento.
