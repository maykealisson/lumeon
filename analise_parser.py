"""
Leitura do arquivo de análise (.md com frontmatter YAML, schema_version 1).

O frontmatter traz os dados estruturados (indicadores, valuation, histórico,
checklist). Do corpo extraímos as listas de pontos positivos, pontos de atenção,
riscos, gatilhos de saída, dados a conferir e o texto de mudanças.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import yaml

CAMPOS_HISTORICO = [
    "receita",
    "lucro_liquido",
    "margem_bruta",
    "margem_ebit",
    "margem_liquida",
    "roe",
    "roic",
    "fco",
    "capex",
    "fcf",
    "divida_liquida_ebitda",
]

FRONTMATTER_RE = re.compile(r"\A\s*---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)
TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,20}$")


class AnaliseInvalidaError(ValueError):
    pass


@dataclass
class AnaliseParseada:
    ticker: str
    data_analise: date
    schema_version: Optional[int] = None
    empresa: Optional[str] = None
    setor: Optional[str] = None
    tipo: Optional[str] = None
    moeda: Optional[str] = None
    periodo_referencia: Optional[str] = None
    preco: Optional[float] = None
    acoes_total_milhoes: Optional[float] = None
    market_cap: Optional[float] = None
    valuation_metodo: Optional[str] = None
    valuation_premissas: Optional[str] = None
    valor_intrinseco: Optional[float] = None
    margem_seguranca: Optional[float] = None
    nota_checklist: Optional[float] = None
    veredito_qualidade: Optional[str] = None
    veredito_preco: Optional[str] = None
    tese: Optional[str] = None
    mudancas: Optional[str] = None
    fontes: List[str] = field(default_factory=list)
    # (grupo, nome, valor)
    indicadores: List[tuple] = field(default_factory=list)
    historico: List[Dict[str, Any]] = field(default_factory=list)
    # (item, resposta)
    checklist: List[tuple] = field(default_factory=list)
    # tipo -> textos
    pontos: Dict[str, List[str]] = field(default_factory=dict)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().strip()
    texto = re.sub(r"^\d+[.)]\s*", "", texto)
    return re.sub(r"\s+", " ", texto)


def _limpar_markdown(texto: str) -> str:
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"`(.+?)`", r"\1", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _numero(valor: Any) -> Optional[float]:
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def _texto(valor: Any) -> Optional[str]:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _data(valor: Any) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor).strip(), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise AnaliseInvalidaError("Campo 'data_analise' ausente ou fora do formato AAAA-MM-DD")


def _resposta_checklist(valor: Any) -> str:
    # YAML 1.1 lê "sim"/"nao" como string, mas "yes"/"no" viraria bool.
    if valor is True:
        return "sim"
    if valor is False:
        return "nao"
    return _normalizar(str(valor)) if valor is not None else "n/d"


def _secoes(corpo: str) -> Dict[str, str]:
    """Mapeia o título normalizado de cada seção `## ` para o seu conteúdo."""
    secoes: Dict[str, str] = {}
    titulo = None
    linhas: List[str] = []
    for linha in corpo.splitlines():
        if linha.startswith("## "):
            if titulo is not None:
                secoes[titulo] = "\n".join(linhas)
            titulo = _normalizar(linha[3:])
            linhas = []
        elif titulo is not None:
            linhas.append(linha)
    if titulo is not None:
        secoes[titulo] = "\n".join(linhas)
    return secoes


def _bullets(texto: str) -> List[str]:
    """Itens de lista de primeiro nível; sub-itens são anexados ao item pai."""
    itens: List[str] = []
    for linha in texto.splitlines():
        if re.match(r"^[-*]\s+", linha):
            itens.append(re.sub(r"^[-*]\s+", "", linha))
        elif itens and re.match(r"^\s+[-*]\s+", linha):
            itens[-1] += " " + re.sub(r"^\s+[-*]\s+", "", linha)
        elif itens and linha.strip() and linha.startswith(" "):
            itens[-1] += " " + linha.strip()
    return [_limpar_markdown(i) for i in itens if i.strip()]


def _secao(secoes: Dict[str, str], *prefixos: str) -> Optional[str]:
    for titulo, conteudo in secoes.items():
        if any(titulo.startswith(p) for p in prefixos):
            return conteudo
    return None


def _dados_a_conferir(corpo: str) -> List[str]:
    m = re.search(r"\*\*Dados a conferir[^*]*\*\*\s*\n(.*?)(?:\n\s*\n(?![-*]\s)|\n---|\Z)", corpo, re.DOTALL)
    return _bullets(m.group(1)) if m else []


def _texto_secao(conteudo: Optional[str]) -> Optional[str]:
    if not conteudo:
        return None
    texto = "\n".join(l for l in conteudo.strip().splitlines() if l.strip() != "---").strip()
    return texto or None


def parse_analise(conteudo: str) -> AnaliseParseada:
    if not conteudo or not conteudo.strip():
        raise AnaliseInvalidaError("Arquivo vazio")

    m = FRONTMATTER_RE.match(conteudo.lstrip("﻿"))
    if not m:
        raise AnaliseInvalidaError("Arquivo sem frontmatter YAML (bloco entre '---' no início)")

    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise AnaliseInvalidaError(f"Frontmatter YAML inválido: {e}")
    if not isinstance(meta, dict):
        raise AnaliseInvalidaError("Frontmatter YAML deve ser um objeto")
    corpo = m.group(2)

    ticker = _texto(meta.get("ticker"))
    if not ticker:
        raise AnaliseInvalidaError("Campo 'ticker' ausente no frontmatter")
    ticker = ticker.upper()
    if not TICKER_RE.match(ticker):
        raise AnaliseInvalidaError(f"Ticker inválido: {ticker}")

    valuation = meta.get("valuation") or {}

    analise = AnaliseParseada(
        ticker=ticker,
        data_analise=_data(meta.get("data_analise")),
        schema_version=int(meta["schema_version"]) if _numero(meta.get("schema_version")) is not None else None,
        empresa=_texto(meta.get("empresa")),
        setor=_texto(meta.get("setor")),
        tipo=_texto(meta.get("tipo")),
        moeda=_texto(meta.get("moeda")),
        periodo_referencia=_texto(meta.get("periodo_referencia")),
        preco=_numero(meta.get("preco")),
        acoes_total_milhoes=_numero(meta.get("acoes_total_milhoes")),
        market_cap=_numero(meta.get("market_cap")),
        valuation_metodo=_texto(valuation.get("metodo")),
        valuation_premissas=_texto(valuation.get("premissas")),
        valor_intrinseco=_numero(valuation.get("valor_intrinseco")),
        margem_seguranca=_numero(valuation.get("margem_seguranca")),
        nota_checklist=_numero(meta.get("nota_checklist")),
        veredito_qualidade=_texto(meta.get("veredito_qualidade")),
        veredito_preco=_texto(meta.get("veredito_preco")),
        tese=_texto(meta.get("tese")),
        fontes=[str(f).strip() for f in (meta.get("fontes") or []) if f],
    )

    for grupo in ("indicadores", "setor_financeiro"):
        for nome, valor in (meta.get(grupo) or {}).items():
            numero = _numero(valor)
            if numero is not None:
                analise.indicadores.append((grupo, str(nome), numero))

    for linha in meta.get("historico") or []:
        if not isinstance(linha, dict) or _numero(linha.get("ano")) is None:
            continue
        registro = {"ano": int(linha["ano"])}
        registro.update({c: _numero(linha.get(c)) for c in CAMPOS_HISTORICO})
        analise.historico.append(registro)

    for item, resposta in (meta.get("checklist") or {}).items():
        analise.checklist.append((str(item), _resposta_checklist(resposta)))

    secoes = _secoes(corpo)
    pontos: Dict[str, List[str]] = {
        "POSITIVO": _bullets(_secao(secoes, "pontos positivos") or ""),
        "ATENCAO": _bullets(_secao(secoes, "pontos de atencao", "pontos negativos") or ""),
        "RISCO": [],
        "GATILHO_SAIDA": [],
        "CONFERIR": _dados_a_conferir(corpo),
    }
    for item in _bullets(_secao(secoes, "riscos") or ""):
        if _normalizar(item).startswith("gatilhos de saida"):
            texto = re.sub(r"^[^:]*:\s*", "", item)
            for gatilho in (t.strip().rstrip(".") for t in texto.split(";")):
                if gatilho:
                    pontos["GATILHO_SAIDA"].append(gatilho[0].upper() + gatilho[1:])
        else:
            pontos["RISCO"].append(item)
    analise.pontos = pontos
    analise.mudancas = _texto_secao(_secao(secoes, "mudancas"))

    return analise
