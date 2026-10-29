from datetime import date

import pytest

from analise_parser import AnaliseInvalidaError, parse_analise


def test_le_frontmatter_e_secoes(conteudo_itsa4):
    a = parse_analise(conteudo_itsa4)

    assert a.ticker == "ITSA4"
    assert a.data_analise == date(2026, 10, 29)
    assert a.preco == 12.93
    assert a.valor_intrinseco == 12.62
    assert a.veredito_qualidade == "alta"
    assert a.veredito_preco == "justo"
    assert len(a.fontes) == 12
    assert ("indicadores", "roe", 18.7) in a.indicadores
    assert all(nome != "receita_ttm" for _, nome, _ in a.indicadores)  # nulos ignorados
    assert [h["ano"] for h in a.historico] == [2020, 2021, 2022, 2023, 2024, 2025]
    assert ("margem_seguranca", "nao") in a.checklist

    assert len(a.pontos["POSITIVO"]) == 7
    assert len(a.pontos["ATENCAO"]) == 7
    assert a.pontos["ATENCAO"][0].startswith("Sem margem de segurança no preço atual:")
    assert len(a.pontos["RISCO"]) == 4
    assert a.pontos["GATILHO_SAIDA"][0] == "ROE do Itaú abaixo de 18% de forma persistente"
    assert len(a.pontos["GATILHO_SAIDA"]) == 3
    assert len(a.pontos["CONFERIR"]) == 4
    assert a.mudancas.startswith("Esta é a primeira análise")


@pytest.mark.parametrize(
    "conteudo, erro",
    [
        ("", "vazio"),
        ("# sem frontmatter", "frontmatter"),
        ("---\nempresa: X\n---\n", "ticker"),
        ("---\nticker: ABC3\ndata_analise: ontem\n---\n", "data_analise"),
    ],
)
def test_rejeita_arquivo_invalido(conteudo, erro):
    with pytest.raises(AnaliseInvalidaError, match=erro):
        parse_analise(conteudo)
