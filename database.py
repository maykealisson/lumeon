"""
Persistência das análises fundamentalistas enviadas em Markdown.

Usa o mesmo servidor MySQL do liberty, em um banco próprio (MYSQL_DATABASE,
padrão `fundament`), criado na subida da API junto com as tabelas.
DATABASE_URL, se definida, tem precedência (qualquer URL do SQLAlchemy).
"""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


# Lê o .env da raiz do projeto; variáveis já definidas no ambiente têm precedência
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def _database_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    usuario = quote_plus(os.getenv("MYSQL_USER", "root"))
    senha = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "localhost")
    porta = os.getenv("MYSQL_PORT", "3306")
    banco = os.getenv("MYSQL_DATABASE", "fundament")
    return f"mysql+pymysql://{usuario}:{senha}@{host}:{porta}/{banco}?charset=utf8mb4"


DATABASE_URL = _database_url()


class Base(DeclarativeBase):
    pass


class Analise(Base):
    """Uma análise (um arquivo .md) de um ativo em uma data."""

    __tablename__ = "analise"
    __table_args__ = (UniqueConstraint("ticker", "data_analise", name="uq_analise_ticker_data"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_version: Mapped[Optional[int]] = mapped_column(Integer)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    empresa: Mapped[Optional[str]] = mapped_column(String(200))
    setor: Mapped[Optional[str]] = mapped_column(String(200))
    tipo: Mapped[Optional[str]] = mapped_column(String(50))
    moeda: Mapped[Optional[str]] = mapped_column(String(10))
    data_analise: Mapped[date] = mapped_column(Date)
    periodo_referencia: Mapped[Optional[str]] = mapped_column(String(20))

    preco: Mapped[Optional[float]] = mapped_column(Double)
    acoes_total_milhoes: Mapped[Optional[float]] = mapped_column(Double)
    market_cap: Mapped[Optional[float]] = mapped_column(Double)

    valuation_metodo: Mapped[Optional[str]] = mapped_column(Text)
    valuation_premissas: Mapped[Optional[str]] = mapped_column(Text)
    valor_intrinseco: Mapped[Optional[float]] = mapped_column(Double)
    margem_seguranca: Mapped[Optional[float]] = mapped_column(Double)

    nota_checklist: Mapped[Optional[float]] = mapped_column(Double)
    veredito_qualidade: Mapped[Optional[str]] = mapped_column(String(30))
    veredito_preco: Mapped[Optional[str]] = mapped_column(String(30))
    tese: Mapped[Optional[str]] = mapped_column(Text)
    mudancas: Mapped[Optional[str]] = mapped_column(Text)

    nome_arquivo: Mapped[Optional[str]] = mapped_column(String(255))
    # Text com tamanho > 64 KB vira MEDIUMTEXT no MySQL
    conteudo_md: Mapped[str] = mapped_column(Text(1_000_000))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    indicadores: Mapped[List["AnaliseIndicador"]] = relationship(
        back_populates="analise", cascade="all, delete-orphan", order_by="AnaliseIndicador.id"
    )
    historico: Mapped[List["AnaliseHistorico"]] = relationship(
        back_populates="analise", cascade="all, delete-orphan", order_by="AnaliseHistorico.ano"
    )
    checklist: Mapped[List["AnaliseChecklist"]] = relationship(
        back_populates="analise", cascade="all, delete-orphan", order_by="AnaliseChecklist.id"
    )
    pontos: Mapped[List["AnalisePonto"]] = relationship(
        back_populates="analise", cascade="all, delete-orphan", order_by="AnalisePonto.ordem"
    )
    fontes: Mapped[List["AnaliseFonte"]] = relationship(
        back_populates="analise", cascade="all, delete-orphan", order_by="AnaliseFonte.id"
    )


class AnaliseIndicador(Base):
    """Indicadores do frontmatter (grupo `indicadores` ou `setor_financeiro`). Nulos não são gravados."""

    __tablename__ = "analise_indicador"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id", ondelete="CASCADE"), index=True)
    grupo: Mapped[str] = mapped_column(String(50))
    nome: Mapped[str] = mapped_column(String(100))
    valor: Mapped[float] = mapped_column(Double)

    analise: Mapped[Analise] = relationship(back_populates="indicadores")


class AnaliseHistorico(Base):
    """Série anual do frontmatter `historico`."""

    __tablename__ = "analise_historico"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id", ondelete="CASCADE"), index=True)
    ano: Mapped[int] = mapped_column(Integer)
    receita: Mapped[Optional[float]] = mapped_column(Double)
    lucro_liquido: Mapped[Optional[float]] = mapped_column(Double)
    margem_bruta: Mapped[Optional[float]] = mapped_column(Double)
    margem_ebit: Mapped[Optional[float]] = mapped_column(Double)
    margem_liquida: Mapped[Optional[float]] = mapped_column(Double)
    roe: Mapped[Optional[float]] = mapped_column(Double)
    roic: Mapped[Optional[float]] = mapped_column(Double)
    fco: Mapped[Optional[float]] = mapped_column(Double)
    capex: Mapped[Optional[float]] = mapped_column(Double)
    fcf: Mapped[Optional[float]] = mapped_column(Double)
    divida_liquida_ebitda: Mapped[Optional[float]] = mapped_column(Double)

    analise: Mapped[Analise] = relationship(back_populates="historico")


class AnaliseChecklist(Base):
    __tablename__ = "analise_checklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id", ondelete="CASCADE"), index=True)
    item: Mapped[str] = mapped_column(String(100))
    resposta: Mapped[str] = mapped_column(String(20))

    analise: Mapped[Analise] = relationship(back_populates="checklist")


class AnalisePonto(Base):
    """Itens de texto do corpo: POSITIVO, ATENCAO, RISCO, GATILHO_SAIDA, CONFERIR."""

    __tablename__ = "analise_ponto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    texto: Mapped[str] = mapped_column(Text)

    analise: Mapped[Analise] = relationship(back_populates="pontos")


class AnaliseFonte(Base):
    __tablename__ = "analise_fonte"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(Text)

    analise: Mapped[Analise] = relationship(back_populates="fontes")


def _criar_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


engine = _criar_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def _criar_banco_mysql(url: str) -> None:
    """Equivalente ao createDatabaseIfNotExist do liberty."""
    destino = make_url(url)
    if not destino.get_backend_name().startswith("mysql") or not destino.database:
        return
    servidor = create_engine(destino.set(database=""))  # None em URL.set significa "não alterar"
    try:
        with servidor.begin() as conn:
            conn.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{destino.database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
    finally:
        servidor.dispose()


def init_db(bind=None):
    try:
        if bind is None:
            _criar_banco_mysql(DATABASE_URL)
        Base.metadata.create_all(bind=bind or engine)
    except OperationalError as e:
        destino = make_url(DATABASE_URL)
        raise RuntimeError(
            f"Não foi possível conectar ao banco {destino.render_as_string(hide_password=True)}: "
            f"{e.orig}. Confira se o MySQL do liberty está de pé e as variáveis "
            "MYSQL_* (ou DATABASE_URL) no .env."
        ) from None


def get_session():
    """Dependency do FastAPI."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
