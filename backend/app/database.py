from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL do banco de dados (usaremos SQLite para desenvolvimento local simples)
# Para mudar para PostgreSQL na nuvem futuramente, basta alterar esta string
SQLALCHEMY_DATABASE_URL = "sqlite:///./ong_adocao.db"

# Cria o motor do banco de dados
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Requerido apenas para o SQLite
)

# Cria a fábrica de sessões do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para a criação das classes dos modelos no models.py
Base = declarative_base()

# Função utilitária (Dependency) para abrir e fechar a sessão do banco em cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()