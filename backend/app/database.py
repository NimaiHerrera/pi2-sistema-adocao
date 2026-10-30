"""
Configuração da Conexão e Sessão com o Banco de Dados (SQLAlchemy)
Projeto Integrador II - Univesp
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# URL de conexão com o banco local SQLite
# Nota: Para migração futura em ambiente de produção (PostgreSQL), basta substituir a string abaixo.
SQLALCHEMY_DATABASE_URL = "sqlite:///./ong_adocao.db"

# Motor de conexão do SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necessário para operações assíncronas no SQLite
)

# Fábrica para geração de sessões do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base para criação das tabelas/modelos ORM
Base = declarative_base()


def get_db():
    """
    Função utilitária (Dependency Injection) para gerenciar a abertura e o fechamento
    da sessão com o banco de dados em cada requisição do FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()