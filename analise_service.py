"""
Regras das análises enviadas em Markdown: gravação e relatório de value investing.

O relatório cruza a análise mais recente (e as anteriores) com dados de mercado de
hoje (yfinance + engines de valuation/score já existentes no projeto).
"""
import math
from datetime import date
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from analise_parser import AnaliseParseada
from database import (
    Analise,
    AnaliseChecklist,
    AnaliseFonte,
    AnaliseHistorico,
    AnaliseIndicador,
    AnalisePonto,
)

CHECKLIST_PERGUNTAS = {
    "entende_negocio": "Entendo o negócio?",
    "receita_cresce_real": "Receita cresce consistente (real)?",
    "lucro_previsivel": "Lucro cresce e é previsível?",
    "margens_estaveis": "Margens estáveis?",
    "roic_acima_custo_capital": "ROIC acima do custo de capital?",
    "divida_controlada": "Dívida controlada?",
    "gera_caixa": "Gera caixa de verdade?",
    "nao_dilui_aloca_bem": "Não dilui / aloca bem?",
    "moat_claro": "Moat claro?",
    "governanca_confiavel": "Governança confiável?",
    "margem_seguranca": "Margem de segurança?",
    "riscos_aceitaveis": "Riscos aceitáveis?",
}

# Indicadores comparados entre a análise atual e a anterior
INDICADORES_EVOLUCAO = [
    "roe",
    "roic",
    "p_l",
    "p_vp",
    "ev_ebit",
    "dividend_yield",
    "payout",
    "earnings_yield",
    "fcf_yield",
    "divida_liquida",
    "divida_liquida_ebitda",
    "margem_liquida",
    "lucro_liquido_ttm",
    "lucro_liquido_recorrente_ttm",
    "cagr_lucro_5a",
    "cagr_receita_5a",
]

ORDEM_QUALIDADE = {"baixa": 0, "media": 1, "média": 1, "alta": 2}
ORDEM_PRECO = {"caro": 0, "justo": 1, "barato": 2}

DIAS_ANALISE_DESATUALIZADA = 120
VARIACAO_PRECO_RELEVANTE = 10.0


# ============ GRAVAÇÃO ============


def salvar_analise(
    session: Session, dados: AnaliseParseada, conteudo: str, nome_arquivo: Optional[str] = None
) -> tuple[Analise, bool]:
    """Grava a análise. Reenvio do mesmo ticker + data substitui o registro anterior."""
    existente = session.scalar(
        select(Analise).where(Analise.ticker == dados.ticker, Analise.data_analise == dados.data_analise)
    )
    substituida = existente is not None
    if existente:
        session.delete(existente)
        session.flush()

    analise = Analise(
        schema_version=dados.schema_version,
        ticker=dados.ticker,
        empresa=dados.empresa,
        setor=dados.setor,
        tipo=dados.tipo,
        moeda=dados.moeda,
        data_analise=dados.data_analise,
        periodo_referencia=dados.periodo_referencia,
        preco=dados.preco,
        acoes_total_milhoes=dados.acoes_total_milhoes,
        market_cap=dados.market_cap,
        valuation_metodo=dados.valuation_metodo,
        valuation_premissas=dados.valuation_premissas,
        valor_intrinseco=dados.valor_intrinseco,
        margem_seguranca=dados.margem_seguranca,
        nota_checklist=dados.nota_checklist,
        veredito_qualidade=dados.veredito_qualidade,
        veredito_preco=dados.veredito_preco,
        tese=dados.tese,
        mudancas=dados.mudancas,
        nome_arquivo=nome_arquivo,
        conteudo_md=conteudo,
    )
    analise.indicadores = [AnaliseIndicador(grupo=g, nome=n, valor=v) for g, n, v in dados.indicadores]
    analise.historico = [AnaliseHistorico(**h) for h in dados.historico]
    analise.checklist = [AnaliseChecklist(item=i, resposta=r) for i, r in dados.checklist]
    analise.fontes = [AnaliseFonte(url=u) for u in dados.fontes]
    analise.pontos = [
        AnalisePonto(tipo=tipo, ordem=ordem, texto=texto)
        for tipo, textos in dados.pontos.items()
        for ordem, texto in enumerate(textos)
    ]
    session.add(analise)
    session.commit()
    session.refresh(analise)
    return analise, substituida


def listar_analises(session: Session, ticker: str) -> List[Analise]:
    return list(
        session.scalars(
            select(Analise).where(Analise.ticker == ticker.upper()).order_by(Analise.data_analise.desc())
        )
    )


def buscar_analise(session: Session, analise_id: int) -> Optional[Analise]:
    return session.get(Analise, analise_id)


def remover_analise(session: Session, analise: Analise) -> None:
    session.delete(analise)
    session.commit()


# ============ SERIALIZAÇÃO ============


def resumo(analise: Analise) -> Dict[str, Any]:
    return {
        "id": analise.id,
        "ticker": analise.ticker,
        "empresa": analise.empresa,
        "data_analise": analise.data_analise.isoformat(),
        "periodo_referencia": analise.periodo_referencia,
        "preco": analise.preco,
        "valor_intrinseco": analise.valor_intrinseco,
        "margem_seguranca": analise.margem_seguranca,
        "nota_checklist": analise.nota_checklist,
        "veredito_qualidade": analise.veredito_qualidade,
        "veredito_preco": analise.veredito_preco,
        "tese": analise.tese,
        "nome_arquivo": analise.nome_arquivo,
        "criado_em": analise.criado_em.isoformat() if analise.criado_em else None,
    }


def _pontos(analise: Analise, tipo: str) -> List[str]:
    return [p.texto for p in analise.pontos if p.tipo == tipo]


def indicadores(analise: Analise) -> Dict[str, float]:
    return {i.nome: i.valor for i in analise.indicadores}


def detalhe(analise: Analise) -> Dict[str, Any]:
    return {
        **resumo(analise),
        "setor": analise.setor,
        "tipo": analise.tipo,
        "moeda": analise.moeda,
        "acoes_total_milhoes": analise.acoes_total_milhoes,
        "market_cap": analise.market_cap,
        "valuation": {
            "metodo": analise.valuation_metodo,
            "premissas": analise.valuation_premissas,
            "valor_intrinseco": analise.valor_intrinseco,
            "margem_seguranca": analise.margem_seguranca,
        },
        "indicadores": indicadores(analise),
        "historico": [
            {c: getattr(h, c) for c in ("ano", "receita", "lucro_liquido", "margem_bruta", "margem_ebit",
                                       "margem_liquida", "roe", "roic", "fco", "capex", "fcf",
                                       "divida_liquida_ebitda")}
            for h in analise.historico
        ],
        "checklist": [_item_checklist(c) for c in analise.checklist],
        "pontos_positivos": _pontos(analise, "POSITIVO"),
        "pontos_atencao": _pontos(analise, "ATENCAO"),
        "riscos": _pontos(analise, "RISCO"),
        "gatilhos_saida": _pontos(analise, "GATILHO_SAIDA"),
        "dados_a_conferir": _pontos(analise, "CONFERIR"),
        "mudancas": analise.mudancas,
        "fontes": [f.url for f in analise.fontes],
    }


def _item_checklist(c: AnaliseChecklist) -> Dict[str, str]:
    return {"item": c.item, "pergunta": CHECKLIST_PERGUNTAS.get(c.item, c.item.replace("_", " ")), "resposta": c.resposta}


# ============ DADOS DE MERCADO ============


def simbolo_yahoo(ticker: str, moeda: Optional[str]) -> str:
    """Ações brasileiras precisam do sufixo .SA no Yahoo Finance."""
    ticker = ticker.upper()
    if "." in ticker:
        return ticker
    if (moeda or "").upper() == "BRL" or (ticker[-1:].isdigit() and len(ticker) <= 6):
        return f"{ticker}.SA"
    return ticker


def _finito(valor: Any) -> Optional[float]:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) else None


def buscar_dados_mercado(ticker: str, moeda: Optional[str]) -> Dict[str, Any]:
    """Cotação e indicadores de hoje via yfinance + engines de valuation e score do projeto."""
    import yfinance as yf

    from score_engine import quality_score
    from valuation_engine import ValuationEngine

    simbolo = simbolo_yahoo(ticker, moeda)
    info = yf.Ticker(simbolo).info or {}
    preco = _finito(info.get("currentPrice")) or _finito(info.get("regularMarketPrice"))
    if not preco:
        raise ValueError(f"Cotação de {simbolo} não encontrada no Yahoo Finance")

    roe = _finito(info.get("returnOnEquity"))
    dados: Dict[str, Any] = {
        "simbolo": simbolo,
        "preco_atual": preco,
        "fechamento_anterior": _finito(info.get("previousClose")),
        "minima_52s": _finito(info.get("fiftyTwoWeekLow")),
        "maxima_52s": _finito(info.get("fiftyTwoWeekHigh")),
        "p_l": _finito(info.get("trailingPE")),
        "p_vp": _finito(info.get("priceToBook")),
        "lpa": _finito(info.get("trailingEps")),
        "vpa": _finito(info.get("bookValue")),
        "roe": roe * 100 if roe is not None else None,
        "market_cap": _finito(info.get("marketCap")),
        "moeda": info.get("currency"),
        "modelo_quantitativo": None,
        "erros": [],
    }

    try:
        resultado = ValuationEngine(simbolo).run()
        valor_justo = _finito(resultado.get("Valor Justo (Fair Value)"))
        dados["modelo_quantitativo"] = {
            "dcf": _finito(resultado.get("Valor justo calculado pelo Fluxo de Caixa Descontado")),
            "multiplos": _finito(resultado.get("Valor estimado com base em comparações de mercado (P/L, EV/EBITDA etc.)")),
            "valor_justo": valor_justo,
            "preco_compra": _finito(resultado.get("Preço de Compra (Margem de Segurança)")),
        }
    except Exception as e:  # engine depende de dados que nem sempre existem (ex: FCF de bancos)
        dados["erros"].append(f"Valuation quantitativo indisponível: {e}")

    try:
        score, _, top_positivo, top_alerta = quality_score(info, simbolo)
        dados["score_qualidade"] = {"score": score, "destaque": top_alerta or top_positivo}
    except Exception as e:
        dados["score_qualidade"] = None
        dados["erros"].append(f"Score de qualidade indisponível: {e}")

    return dados


# ============ RELATÓRIO ============


def _pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """Variação percentual de b para a."""
    if a is None or not b:
        return None
    return round((a / b - 1) * 100, 2)


def _arred(valor: Optional[float], casas: int = 2) -> Optional[float]:
    return round(valor, casas) if valor is not None else None


def _fmt(valor: Optional[float], casas: int = 1) -> str:
    if valor is None:
        return "n/d"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _recomendacao(qualidade: Optional[str], margem: Optional[float], margem_desejada: float) -> Dict[str, str]:
    nivel = ORDEM_QUALIDADE.get((qualidade or "").lower())
    if nivel == 0:
        return {"acao": "EVITAR", "descricao": "Qualidade baixa na análise: preço não compensa o risco do negócio."}
    if margem is None:
        return {"acao": "SEM_PRECO_JUSTO", "descricao": "A análise não traz valor intrínseco para comparar com o preço."}
    if margem >= margem_desejada:
        return {"acao": "COMPRAR", "descricao": f"Margem de segurança de {_fmt(margem)}%, acima dos {_fmt(margem_desejada, 0)}% exigidos."}
    if margem >= 0:
        return {"acao": "ACUMULAR_COM_CAUTELA", "descricao": f"Abaixo do valor justo, mas a margem de {_fmt(margem)}% é menor que os {_fmt(margem_desejada, 0)}% exigidos."}
    if margem >= -10:
        return {"acao": "AGUARDAR", "descricao": f"Preço {_fmt(-margem)}% acima do valor justo: manter e esperar um preço melhor para aportar."}
    return {"acao": "CARO", "descricao": f"Preço {_fmt(-margem)}% acima do valor justo: avaliar os gatilhos de saída."}


def _comparar_com_anterior(atual: Analise, anterior: Optional[Analise]) -> Optional[Dict[str, Any]]:
    if anterior is None:
        return None
    ind_atual, ind_ant = indicadores(atual), indicadores(anterior)
    variacoes = []
    for nome in INDICADORES_EVOLUCAO:
        if nome in ind_atual and nome in ind_ant:
            variacoes.append({
                "indicador": nome,
                "anterior": ind_ant[nome],
                "atual": ind_atual[nome],
                "diferenca": round(ind_atual[nome] - ind_ant[nome], 2),
            })
    return {
        "data_anterior": anterior.data_analise.isoformat(),
        "valor_intrinseco": {"anterior": anterior.valor_intrinseco, "atual": atual.valor_intrinseco,
                             "variacao_pct": _pct(atual.valor_intrinseco, anterior.valor_intrinseco)},
        "nota_checklist": {"anterior": anterior.nota_checklist, "atual": atual.nota_checklist},
        "veredito_qualidade": {"anterior": anterior.veredito_qualidade, "atual": atual.veredito_qualidade},
        "veredito_preco": {"anterior": anterior.veredito_preco, "atual": atual.veredito_preco},
        "indicadores": variacoes,
    }


def gerar_relatorio(
    session: Session,
    ticker: str,
    margem_desejada: float = 20.0,
    fonte_mercado: Optional[Callable[[str, Optional[str]], Dict[str, Any]]] = None,
    hoje: Optional[date] = None,
) -> Optional[Dict[str, Any]]:
    analises = listar_analises(session, ticker)
    if not analises:
        return None
    atual, anterior = analises[0], (analises[1] if len(analises) > 1 else None)
    hoje = hoje or date.today()
    ind = indicadores(atual)
    avisos: List[str] = []

    try:
        mercado = (fonte_mercado or buscar_dados_mercado)(atual.ticker, atual.moeda)
        avisos.extend(mercado.pop("erros", []))
    except Exception as e:
        mercado = None
        avisos.append(f"Não foi possível buscar a cotação de hoje ({e}); usando o preço da análise.")

    preco_analise = atual.preco
    preco_atual = (mercado or {}).get("preco_atual") or preco_analise
    vi = atual.valor_intrinseco
    fator = (preco_atual / preco_analise) if preco_analise and preco_atual else None

    # Margem de segurança clássica (Graham): quanto o preço está abaixo do valor intrínseco.
    margem = round((1 - preco_atual / vi) * 100, 2) if vi and preco_atual else None
    potencial = _pct(vi, preco_atual)

    # Múltiplos da análise ajustados pelo preço de hoje (o lucro/patrimônio é o mesmo do período).
    def ajustado(nome: str, inverso: bool = False) -> Optional[float]:
        valor = ind.get(nome)
        if valor is None or not fator:
            return None
        return round(valor / fator if inverso else valor * fator, 2)

    p_l = ajustado("p_l")
    p_vp = ajustado("p_vp")
    dy = ajustado("dividend_yield", inverso=True)
    earnings_yield = ajustado("earnings_yield", inverso=True)
    if earnings_yield is None and p_l:
        earnings_yield = round(100 / p_l, 2)
    juros = ind.get("taxa_juros_referencia")
    custo_capital = ind.get("wacc_estimado")
    retorno_capital = ind.get("roic") if ind.get("roic") is not None else ind.get("roe")

    lpa = preco_analise / ind["p_l"] if preco_analise and ind.get("p_l") else None
    vpa = preco_analise / ind["p_vp"] if preco_analise and ind.get("p_vp") else None
    dpa = preco_analise * ind["dividend_yield"] / 100 if preco_analise and ind.get("dividend_yield") else None
    graham = math.sqrt(22.5 * lpa * vpa) if lpa and vpa and lpa > 0 and vpa > 0 else None
    bazin = dpa / 0.06 if dpa else None

    dias = (hoje - atual.data_analise).days
    variacao_preco = _pct(preco_atual, preco_analise) if mercado else None

    checklist = [_item_checklist(c) for c in atual.checklist]
    contagem = {r: sum(1 for c in checklist if c["resposta"] == r) for r in ("sim", "parcial", "nao")}

    positivos = [{"texto": t, "origem": "analise"} for t in _pontos(atual, "POSITIVO")]
    atencao = [{"texto": t, "origem": "analise"} for t in _pontos(atual, "ATENCAO")]

    if margem is not None:
        if margem >= margem_desejada:
            positivos.insert(0, {"texto": f"Preço atual com margem de segurança de {_fmt(margem)}% sobre o valor justo de {_fmt(vi, 2)}.", "origem": "processamento"})
        elif margem < 0:
            atencao.insert(0, {"texto": f"Preço atual ({_fmt(preco_atual, 2)}) está {_fmt(-margem)}% acima do valor justo ({_fmt(vi, 2)}).", "origem": "processamento"})
        else:
            atencao.insert(0, {"texto": f"Margem de segurança de {_fmt(margem)}%, abaixo dos {_fmt(margem_desejada, 0)}% desejados.", "origem": "processamento"})
    if variacao_preco is not None and abs(variacao_preco) >= VARIACAO_PRECO_RELEVANTE:
        alvo = positivos if variacao_preco < 0 else atencao
        direcao = "caiu" if variacao_preco < 0 else "subiu"
        alvo.append({"texto": f"O preço {direcao} {_fmt(abs(variacao_preco))}% desde a análise de {atual.data_analise.strftime('%d/%m/%Y')}.", "origem": "processamento"})
    if dias > DIAS_ANALISE_DESATUALIZADA:
        atencao.append({"texto": f"Análise feita há {dias} dias: vale atualizar com os resultados mais recentes.", "origem": "processamento"})
    if retorno_capital is not None and custo_capital is not None:
        spread = retorno_capital - custo_capital
        if spread > 0:
            positivos.append({"texto": f"Retorno sobre capital ({_fmt(retorno_capital)}%) {_fmt(spread)} p.p. acima do custo de capital ({_fmt(custo_capital)}%).", "origem": "processamento"})
        else:
            atencao.append({"texto": f"Retorno sobre capital ({_fmt(retorno_capital)}%) abaixo do custo de capital ({_fmt(custo_capital)}%): a empresa não cria valor.", "origem": "processamento"})
    if earnings_yield is not None and juros is not None and earnings_yield < juros:
        atencao.append({"texto": f"Earnings yield de {_fmt(earnings_yield)}% no preço atual, abaixo da taxa de juros de referência ({_fmt(juros, 2)}%).", "origem": "processamento"})
    negativos = [c["pergunta"] for c in checklist if c["resposta"] == "nao"]
    if negativos:
        atencao.append({"texto": "Checklist com resposta 'não' em: " + "; ".join(negativos), "origem": "processamento"})
    comparacao = _comparar_com_anterior(atual, anterior)
    if comparacao:
        for campo, ordem, rotulo in (("veredito_qualidade", ORDEM_QUALIDADE, "qualidade"), ("veredito_preco", ORDEM_PRECO, "preço")):
            de, para = comparacao[campo]["anterior"], comparacao[campo]["atual"]
            nivel_de, nivel_para = ordem.get((de or "").lower()), ordem.get((para or "").lower())
            if nivel_de is not None and nivel_para is not None and nivel_de != nivel_para:
                alvo = positivos if nivel_para > nivel_de else atencao
                alvo.append({"texto": f"Veredito de {rotulo} mudou de '{de}' para '{para}' desde a análise anterior.", "origem": "processamento"})

    return {
        "ticker": atual.ticker,
        "empresa": atual.empresa,
        "setor": atual.setor,
        "tipo": atual.tipo,
        "moeda": atual.moeda,
        "data_processamento": hoje.isoformat(),
        "analise_base": {**resumo(atual), "dias_desde_analise": dias},
        "total_analises": len(analises),
        "preco": {
            "atual": _arred(preco_atual),
            "fonte": "mercado" if mercado else "analise",
            "na_analise": preco_analise,
            "variacao_desde_analise_pct": variacao_preco,
            "minima_52s": _arred((mercado or {}).get("minima_52s")),
            "maxima_52s": _arred((mercado or {}).get("maxima_52s")),
        },
        "preco_justo": {
            "valor_intrinseco": vi,
            "metodo": atual.valuation_metodo,
            "premissas": atual.valuation_premissas,
            "margem_seguranca_pct": margem,
            "potencial_valorizacao_pct": potencial,
            "margem_desejada_pct": margem_desejada,
            "preco_teto_compra": _arred(vi * (1 - margem_desejada / 100)) if vi else None,
            "graham": _arred(graham),
            "bazin": _arred(bazin),
            "modelo_quantitativo": (mercado or {}).get("modelo_quantitativo"),
        },
        "recomendacao": _recomendacao(atual.veredito_qualidade, margem, margem_desejada),
        "qualidade": {
            "veredito_qualidade": atual.veredito_qualidade,
            "veredito_preco": atual.veredito_preco,
            "nota_checklist": atual.nota_checklist,
            "total_checklist": len(checklist),
            "contagem_checklist": contagem,
            "checklist": checklist,
            "score_quantitativo": (mercado or {}).get("score_qualidade"),
        },
        "value_investing": {
            "p_l": p_l,
            "p_vp": p_vp,
            "dividend_yield": dy,
            "earnings_yield": earnings_yield,
            "taxa_juros_referencia": juros,
            "premio_earnings_yield_vs_juros": _arred(earnings_yield - juros) if earnings_yield is not None and juros is not None else None,
            "retorno_sobre_capital": retorno_capital,
            "custo_capital": custo_capital,
            "spread_retorno_custo": _arred(retorno_capital - custo_capital) if retorno_capital is not None and custo_capital is not None else None,
            "payout": ind.get("payout"),
            "cagr_lucro_5a": ind.get("cagr_lucro_5a"),
            "cagr_receita_5a": ind.get("cagr_receita_5a"),
            "inflacao_media_5a": ind.get("inflacao_media_5a"),
            "divida_liquida_ebitda": ind.get("divida_liquida_ebitda"),
            "divida_liquida": ind.get("divida_liquida"),
            "lpa": _arred(lpa),
            "vpa": _arred(vpa),
            "dpa": _arred(dpa),
        },
        "mercado_hoje": {k: v for k, v in (mercado or {}).items() if k not in ("modelo_quantitativo", "score_qualidade")} or None,
        "tese": atual.tese,
        "pontos_positivos": positivos,
        "pontos_atencao": atencao,
        "riscos": _pontos(atual, "RISCO"),
        "gatilhos_saida": _pontos(atual, "GATILHO_SAIDA"),
        "dados_a_conferir": _pontos(atual, "CONFERIR"),
        "mudancas_texto": atual.mudancas,
        "comparacao_anterior": comparacao,
        "evolucao": [
            {
                "data_analise": a.data_analise.isoformat(),
                "preco": a.preco,
                "valor_intrinseco": a.valor_intrinseco,
                "margem_seguranca": a.margem_seguranca,
                "nota_checklist": a.nota_checklist,
                "veredito_qualidade": a.veredito_qualidade,
                "veredito_preco": a.veredito_preco,
                "roe": indicadores(a).get("roe"),
                "p_l": indicadores(a).get("p_l"),
                "dividend_yield": indicadores(a).get("dividend_yield"),
            }
            for a in reversed(analises)
        ],
        "historico": detalhe(atual)["historico"],
        "avisos": avisos,
    }
