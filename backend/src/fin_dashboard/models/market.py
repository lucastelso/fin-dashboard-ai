from datetime import datetime
from sqlalchemy import MetaData, String, Integer, DateTime, func, ForeignKey, Index, UniqueConstraint, BigInteger, Double
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
    __tablename__ = "dim_ativos"

    id_dim_ativo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ativo: Mapped[str] = mapped_column(String(9), nullable=False)

    extractions: Mapped[list["SeriesAtivos"]] = relationship(
        "SeriesAtivos", back_populates="dimension"
    )

    __table_args__ = (
        UniqueConstraint('ativo', name='uq_dim_ativos_ativo'),
    )

class SeriesAtivos(Base):
    __tablename__ = "series_ativos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_dim_ativo: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("dim_ativos.id_dim_ativo", ondelete="CASCADE"), 
        nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Substituição: Double() encapsula o Float64 nativamente.
    open: Mapped[float] = mapped_column(Double, nullable=False)
    close: Mapped[float] = mapped_column(Double, nullable=False)
    high: Mapped[float] = mapped_column(Double, nullable=False)
    low: Mapped[float] = mapped_column(Double, nullable=False)
    
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    dimension: Mapped[DimensaoAtivos] = relationship(
        "DimensaoAtivos", back_populates="extractions"
    )

    __table_args__ = (
        Index('ix_series_ativos_id_dim_ativo', 'id_dim_ativo'),
        UniqueConstraint('id_dim_ativo', 'date', name='uq_series_ativos_id_dim_ativo_date')
    )