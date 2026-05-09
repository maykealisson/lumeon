import yfinance as yf
import numpy as np

class ValuationEngine:

    def __init__(self, ticker):
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)
        self.info = self.stock.info

        # Detecta se é Brasil ou EUA
        self.is_brazil = ticker.endswith(".SA")

    def get_financials(self):
        cf = self.stock.cashflow
        bs = self.stock.balance_sheet

        # Cálculo mais preciso de FCF = Operating Cash Flow - CapEx
        try:
            fcf = cf.loc["Free Cash Flow"].iloc[0]
        except:
            try:
                ocf = cf.loc["Operating Cash Flow"].iloc[0]
                capex = cf.loc["Capital Expenditure"].iloc[0]
                fcf = ocf - abs(capex)  # CapEx é negativo
            except:
                fcf = cf.loc["Operating Cash Flow"].iloc[0]  # último fallback

        debt = bs.loc["Total Debt"].iloc[0] if "Total Debt" in bs.index else 0
        cash = bs.loc["Cash And Cash Equivalents"].iloc[0] if "Cash And Cash Equivalents" in bs.index else 0

        return fcf, debt, cash

    def _calculate_beta(self):
        """Calcula ou estima taxa de desconto baseada em risco"""
        beta = self.info.get("beta", 1.0)
        # CAPM simplificado: Rf (2.5%) + Beta * Rm (7%)
        risk_free = 0.025
        market_risk = 0.07
        return risk_free + beta * market_risk
    
    def assumptions(self):
        # Premissas mais realistas e ajustadas ao risco real
        if self.is_brazil:
            discount = 0.13  # Taxa de desconto para Brasil (risco maior)
            terminal_growth = 0.025
        else:
            # Para EUA, usar taxa dinâmica baseada em Beta
            discount = self._calculate_beta()
            discount = max(0.07, min(0.12, discount))  # Limitar entre 7% e 12%
            terminal_growth = 0.025
        
        return {
            "discount": discount,
            "terminal": terminal_growth
        }

    def dcf(self):
        fcf, debt, cash = self.get_financials()
        a = self.assumptions()

        discount = a["discount"]
        terminal = a["terminal"]
        
        # Validação básica
        if fcf <= 0:
            return None

        # Projeção com 10 anos e crescimento decrescente (mais realista)
        years = 10
        fcf_list = []
        
        # Crescimento decrescente: diminui a cada ano
        growth_schedule = [0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.025, 0.025]

        for i in range(1, years + 1):
            growth = growth_schedule[i - 1]
            fcf_future = fcf * (1 + growth) ** i
            fcf_discounted = fcf_future / (1 + discount) ** i
            fcf_list.append(fcf_discounted)

        # Valor terminal com crescimento perpétuo
        if discount > terminal:
            terminal_value = (fcf_list[-1] * (1 + terminal)) / (discount - terminal)
            terminal_discounted = terminal_value / (1 + discount) ** years
        else:
            terminal_discounted = 0

        enterprise_value = sum(fcf_list) + terminal_discounted

        equity_value = enterprise_value - debt + cash

        shares = self.info.get("sharesOutstanding", 1)
        
        if shares <= 0:
            return None

        fair_value = equity_value / shares

        return fair_value if fair_value > 0 else None

    def multiples(self):
        pe = self.info.get("trailingPE", None)
        price = self.info.get("currentPrice", 0)

        if not pe or price <= 0:
            return None

        # P/E justo mais realista baseado em qualidade
        roe = self.info.get("returnOnEquity", 0)
        
        if self.is_brazil:
            # Para Brasil: base 12, ajustado por ROE
            if roe > 0.15:
                fair_pe = 15
            elif roe > 0.10:
                fair_pe = 12
            else:
                fair_pe = 10
        else:
            # Para EUA: base 18-20, ajustado por ROE
            if roe > 0.15:
                fair_pe = 20
            elif roe > 0.10:
                fair_pe = 18
            else:
                fair_pe = 16
        
        fair_value = price * (fair_pe / pe)
        return fair_value

    def margin_of_safety(self, value):
        # Margem de segurança de 40% para investidor amador (mais conservador)
        return value * 0.60  # 40% de desconto

    def run(self):
        dcf_value = self.dcf()
        mult_value = self.multiples()

        values = [v for v in [dcf_value, mult_value] if v is not None]

        avg_value = np.mean(values)

        safe_value = self.margin_of_safety(avg_value)

        return {
            "Valor justo calculado pelo Fluxo de Caixa Descontado": dcf_value,
            "Valor estimado com base em comparações de mercado (P/L, EV/EBITDA etc.)": mult_value,
            "Valor Justo (Fair Value)": avg_value,
            "Preço de Compra (Margem de Segurança)": safe_value
        }

