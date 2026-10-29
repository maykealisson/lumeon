from datetime import date

import analise_service
from analise_parser import parse_analise
from database import Analise, AnalisePonto


def _salvar(session, conteudo):
    return analise_service.salvar_analise(session, parse_analise(conteudo), conteudo, "a.md")


def _mercado(preco):
    def fonte(ticker, moeda):
        assert analise_service.simbolo_yahoo(ticker, moeda) == "ITSA4.SA"
        return {"preco_atual": preco, "minima_52s": 11.0, "maxima_52s": 16.0, "erros": []}
    return fonte


def test_reenvio_da_mesma_data_substitui(session, conteudo_itsa4):
    _, substituida = _salvar(session, conteudo_itsa4)
    assert substituida is False
    analise, substituida = _salvar(session, conteudo_itsa4)
    assert substituida is True
    assert session.query(Analise).count() == 1
    assert session.query(AnalisePonto).filter_by(analise_id=analise.id).count() == 25


def test_relatorio_com_preco_de_mercado(session, conteudo_itsa4):
    _salvar(session, conteudo_itsa4)

    r = analise_service.gerar_relatorio(session, "itsa4", 20, _mercado(10.0), hoje=date(2026, 11, 10))

    assert r["preco"]["atual"] == 10.0
    assert r["preco"]["fonte"] == "mercado"
    assert r["preco"]["variacao_desde_analise_pct"] == -22.66
    assert r["preco_justo"]["valor_intrinseco"] == 12.62
    assert r["preco_justo"]["margem_seguranca_pct"] == 20.76
    assert r["preco_justo"]["preco_teto_compra"] == 10.1
    assert r["recomendacao"]["acao"] == "COMPRAR"
    # múltiplos da análise reajustados pelo preço de hoje
    assert r["value_investing"]["p_l"] == 6.38
    assert r["value_investing"]["dividend_yield"] == 11.46
    assert r["value_investing"]["spread_retorno_custo"] == 4.2
    assert r["preco_justo"]["graham"] is not None
    assert r["pontos_positivos"][0]["origem"] == "processamento"
    assert any("caiu" in p["texto"] for p in r["pontos_positivos"])
    assert r["analise_base"]["dias_desde_analise"] == 12
    assert r["comparacao_anterior"] is None


def test_relatorio_sem_mercado_usa_preco_da_analise(session, conteudo_itsa4):
    _salvar(session, conteudo_itsa4)

    def falha(*_):
        raise RuntimeError("sem internet")

    r = analise_service.gerar_relatorio(session, "ITSA4", 20, falha, hoje=date(2026, 10, 29))

    assert r["preco"]["fonte"] == "analise"
    assert r["preco"]["atual"] == 12.93
    assert r["recomendacao"]["acao"] == "AGUARDAR"
    assert r["avisos"]
    assert r["mercado_hoje"] is None


def test_relatorio_compara_com_analise_anterior(session, conteudo_itsa4):
    _salvar(session, conteudo_itsa4)
    nova = (
        conteudo_itsa4.replace("data_analise: 2026-10-29", "data_analise: 2027-02-15")
        .replace("valor_intrinseco: 12.62", "valor_intrinseco: 13.50")
        .replace("veredito_preco: justo", "veredito_preco: barato")
        .replace("  roe: 18.7", "  roe: 19.5")
    )
    _salvar(session, nova)

    r = analise_service.gerar_relatorio(session, "ITSA4", 20, _mercado(12.0), hoje=date(2027, 2, 20))

    assert r["total_analises"] == 2
    assert r["analise_base"]["data_analise"] == "2027-02-15"
    assert [e["data_analise"] for e in r["evolucao"]] == ["2026-10-29", "2027-02-15"]
    comp = r["comparacao_anterior"]
    assert comp["valor_intrinseco"]["variacao_pct"] == 6.97
    roe = next(i for i in comp["indicadores"] if i["indicador"] == "roe")
    assert roe["diferenca"] == 0.8
    assert any("mudou de 'justo' para 'barato'" in p["texto"] for p in r["pontos_positivos"])


def test_relatorio_inexistente(session):
    assert analise_service.gerar_relatorio(session, "XPTO3", 20, _mercado(1)) is None
