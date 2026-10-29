import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import analise_service
import api
from database import get_session


@pytest.fixture
def client(engine, monkeypatch):
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)

    def sessao():
        s = fabrica()
        try:
            yield s
        finally:
            s.close()

    api.app.dependency_overrides[get_session] = sessao
    monkeypatch.setattr(api, "init_db", lambda: None)
    monkeypatch.setattr(
        analise_service, "buscar_dados_mercado", lambda t, m: {"preco_atual": 12.0, "erros": []}
    )
    with TestClient(api.app) as c:
        yield c
    api.app.dependency_overrides.clear()


def test_fluxo_upload_lista_relatorio_remove(client, conteudo_itsa4):
    r = client.post("/ativos/itsa4/analises", json={"conteudo": conteudo_itsa4, "nome_arquivo": "ITSA4.md"})
    assert r.status_code == 201, r.text
    criada = r.json()
    assert criada["ticker"] == "ITSA4" and criada["substituida"] is False

    lista = client.get("/ativos/ITSA4/analises").json()
    assert [a["id"] for a in lista] == [criada["id"]]

    detalhe = client.get(f"/analises/{criada['id']}").json()
    assert len(detalhe["pontos_positivos"]) == 7

    rel = client.get("/ativos/ITSA4/relatorio?margem_desejada=15").json()
    assert rel["preco"]["atual"] == 12.0
    assert rel["preco_justo"]["margem_desejada_pct"] == 15

    assert client.delete(f"/analises/{criada['id']}").status_code == 204
    assert client.get("/ativos/ITSA4/relatorio").status_code == 404


def test_upload_rejeita_ticker_diferente(client, conteudo_itsa4):
    r = client.post("/ativos/ITUB4/analises", json={"conteudo": conteudo_itsa4})
    assert r.status_code == 422
    assert "ITSA4" in r.json()["detail"]


def test_upload_rejeita_arquivo_invalido(client):
    r = client.post("/ativos/ITSA4/analises", json={"conteudo": "# sem frontmatter"})
    assert r.status_code == 422
