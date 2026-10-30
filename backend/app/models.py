"""
Modelos ORM / Mapeamento de Tabelas do Banco de Dados
Projeto Integrador II - Univesp
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class ONG(Base):
    """Tabela para armazenamento dos dados institucionais da ONG parceira."""

    __tablename__ = "ong"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    endereco = Column(String(200), nullable=False)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)


class Animal(Base):
    """Tabela para cadastro dos pets resgatados e disponíveis para adoção."""

    __tablename__ = "animais"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    especie = Column(String(20), nullable=False)  # Ex: Cão, Gato
    porte = Column(String(20), nullable=False)    # Ex: Pequeno, Médio, Grande
    idade_aproximada = Column(String(30), nullable=True)
    castrado = Column(Boolean, default=False)
    vacinado = Column(Boolean, default=False)
    status = Column(String(20), default="disponivel")  # Status: disponivel / adotado
    descricao = Column(Text, nullable=True)
    foto_url = Column(String(255), nullable=True)

    # Relacionamento com as solicitações de adoção (exclusão em cascata)
    solicitacoes = relationship("SolicitacaoAdocao", back_populates="animal", cascade="all, delete-orphan")


class Adotante(Base):
    """Tabela de cadastro dos cidadãos interessados em adotar."""

    __tablename__ = "adotantes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    telefone = Column(String(20), nullable=False)
    cep = Column(String(9), nullable=False)
    logradouro = Column(String(150), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)

    # Relacionamento com as solicitações de adoção (exclusão em cascata)
    solicitacoes = relationship("SolicitacaoAdocao", back_populates="adotante", cascade="all, delete-orphan")


class SolicitacaoAdocao(Base):
    """Tabela intermediária de ligação entre o Adotante e o Animal selecionado."""

    __tablename__ = "solicitacoes_adocao"

    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer, ForeignKey("animais.id", ondelete="CASCADE"), nullable=False)
    adotante_id = Column(Integer, ForeignKey("adotantes.id", ondelete="CASCADE"), nullable=False)
    data_solicitacao = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="pendente")  # Status: pendente / aprovado / recusado

    # Mapeamento ORM dos relacionamentos
    animal = relationship("Animal", back_populates="solicitacoes")
    adotante = relationship("Adotante", back_populates="solicitacoes")