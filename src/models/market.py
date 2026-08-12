from datetime import datetime
from polars import Decimal
from sqlalchemy import MetaData, String, Integer, Text, DateTime, func, ForeignKey, Index, UniqueConstraint, Numeric, BigInteger 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata_obj = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

class Base(DeclarativeBase):
    metadata = metadata_obj

class DimensaoAtivos(Base):
    """Tabela de dimensão com metadados para consulta eficiente (1 linha por ATIVO)."""
    __tablename__ = "dim_ativos"

    id_dim_ativo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ativo: Mapped[str] = mapped_column(String(9), nullable=False)

    # Relacionamento no ORM (puramente para Python, não afeta o banco)
    extractions: Mapped[list["SeriesAtivos"]] = relationship(
        "SeriesAtivos", back_populates="dimension"
    )

    __table_args__ = (
        UniqueConstraint('ativo', name='uq_dim_ativos_ativo'),
    )

class SeriesAtivos(Base):
    """Series temporais dos ativos com dados de data, abertura, fechamento,
    e volumes. É a maior e mais complexa tabela. Sempre deve ser referenciada
    via dim_ativos."""
    __tablename__ = "series_ativos"
    

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # A Chave Estrangeira aponta para o ID Inteiro da Dimensão
    id_dim_ativo: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("dim_ativos.id_dim_ativo", ondelete="CASCADE"), 
        nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 2),    nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relacionamento no ORM
    dimension: Mapped[DimensaoAtivos] = relationship(
        "DimensaoAtivos", back_populates="extractions"
    )

    __table_args__ = (
        # Índice crucial na FK para acelerar JOINS de volumetria pesada
        Index('ix_series_ativos_id_dim_ativo', 'id_dim_ativo'),
        UniqueConstraint('id_dim_ativo', 'date', name='uq_series_ativos_id_dim_ativo_date')
    )