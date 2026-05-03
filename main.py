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

        try:
            fcf = cf.loc["Free Cash Flow"].iloc[0]
        except:
            fcf = cf.loc["Operating Cash Flow"].iloc[0]  # fallback

        debt = bs.loc["Total Debt"].iloc[0] if "Total Debt" in bs.index else 0
        cash = bs.loc["Cash And Cash Equivalents"].iloc[0] if "Cash And Cash Equivalents" in bs.index else 0

        return fcf, debt, cash

    def assumptions(self):
        # Premissas conservadoras
        if self.is_brazil:
            return {
                "growth": 0.05,
                "discount": 0.12,
                "terminal": 0.03
            }
        else:
            return {
                "growth": 0.04,
                "discount": 0.08,
                "terminal": 0.025
            }

    def dcf(self):
        fcf, debt, cash = self.get_financials()
        a = self.assumptions()

        growth = a["growth"]
        discount = a["discount"]
        terminal = a["terminal"]

        years = 5
        fcf_list = []

        for i in range(1, years + 1):
            fcf_future = fcf * (1 + growth) ** i
            fcf_discounted = fcf_future / (1 + discount) ** i
            fcf_list.append(fcf_discounted)

        # Valor terminal
        terminal_value = (fcf_list[-1] * (1 + terminal)) / (discount - terminal)
        terminal_discounted = terminal_value / (1 + discount) ** years

        enterprise_value = sum(fcf_list) + terminal_discounted

        equity_value = enterprise_value - debt + cash

        shares = self.info.get("sharesOutstanding", 1)

        fair_value = equity_value / shares

        return fair_value

    def multiples(self):
        pe = self.info.get("trailingPE", None)

        if not pe:
            return None

        # P/L justo conservador
        fair_pe = 15 if not self.is_brazil else 10

        price = self.info.get("currentPrice", 0)

        fair_value = price * (fair_pe / pe)

        return fair_value

    def margin_of_safety(self, value):
        return value * 0.7  # 30% de desconto estilo Graham

    def run(self):
        dcf_value = self.dcf()
        mult_value = self.multiples()

        values = [v for v in [dcf_value, mult_value] if v is not None]

        avg_value = np.mean(values)

        safe_value = self.margin_of_safety(avg_value)

        return {
            "DCF": dcf_value,
            "Multiples": mult_value,
            "Fair Value": avg_value,
            "Buy Price (Margin Safety)": safe_value
        }


if __name__ == "__main__":
    ticker = input("Digite o ticker: ")

    engine = ValuationEngine(ticker)
    result = engine.run()

    print("\n--- Resultado ---")
    for k, v in result.items():
        print(f"{k}: {v:.2f}")