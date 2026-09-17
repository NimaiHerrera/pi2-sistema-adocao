# ==============================================================================
# PROJETO INTEGRADOR II (UNIVESP) - PLATAFORMA DE ADOÇÃO DE ANIMAIS (ONG)
# Arquivo: backend/app/main.py
# Descrição: API RESTful construída com FastAPI e SQLAlchemy ORM
# ==============================================================================

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import requests

# Importação dos módulos locais de banco de dados e modelos
from .database import engine, Base, get_db
from . import models

# Cria todas as tabelas mapeadas no models.py automaticamente no banco SQLite/PostgreSQL
models.Base.metadata.create_all(bind=engine)

# Inicialização e configuração principal da aplicação FastAPI
app = FastAPI(
    title="Plataforma de Adoção de Animais - ONG Parceira",
    description="API RESTful para gestão de pets resgatados e formulários de adoção (PI2 - Univesp)",
    version="2.0.0"
)

# ==============================================================================
# SCHEMAS PYDANTIC (Validação de Dados de Entrada/Saída)
# ==============================================================================

class AnimalBase(BaseModel):
    nome: str
    especie: str            # Ex: Cão, Gato
    porte: str              # Ex: Pequeno, Médio, Grande
    idade_aproximada: Optional[str] = None
    castrado: bool = False
    vacinado: bool = False
    descricao: Optional[str] = None
    foto_url: Optional[str] = None

class AdotanteForm(BaseModel):
    nome: str
    cpf: str
    telefone: str
    cep: str
    animal_id: int

# ==============================================================================
# INTEGRAÇÃO COM BOT DO TELEGRAM (Notificações em Tempo Real)
# ==============================================================================

def notificar_telegram(nome_adotante: str, telefone: str, nome_pet: str):
    """
    Função utilitária que dispara uma mensagem para o grupo/chat do Telegram da ONG
    sempre que um novo formulário de interesse de adoção for enviado.
    """
    # IMPORTANTE: Substituir futuramente pelas credenciais reais do BotFather
    TOKEN_BOT = "SEU_TELEGRAM_BOT_TOKEN"
    CHAT_ID = "SEU_TELEGRAM_CHAT_ID"

    mensagem = (
        f"🐾 *NOVA SOLICITAÇÃO DE ADOÇÃO!*\n\n"
        f"👤 *Adotante:* {nome_adotante}\n"
        f"📞 *Telefone:* {telefone}\n"
        f"🐶 *Pet de Interesse:* {nome_pet}\n\n"
        f"_Verifique o painel administrativo para mais detalhes._"
    )

    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[Aviso Telegram] Não foi possível enviar a notificação: {e}")

# ==============================================================================
# ENDPOINTS / ROTAS DA API
# ==============================================================================

@app.get("/", tags=["Geral"])
def home():
    """Endpoint raiz para verificação rápida do status de funcionamento da API"""
    return {
        "projeto": "Plataforma de Adoção de Animais - PI2 Univesp",
        "status": "Online",
        "versao": "2.0.0"
    }

@app.get("/ong", tags=["ONG"])
def obter_dados_ong(db: Session = Depends(get_db)):
    """
    Retorna os dados institucionais e localização fixa da ONG cadastrada no banco.
    Caso o banco esteja vazio, insere o registro inicial automaticamente.
    """
    ong = db.query(models.Ong).first()
    if not ong:
        # Cadastra uma ONG padrão inicial caso a tabela esteja vazia
        ong = models.Ong(
            nome="ONG Proteção e Amor Animal",
            descricao="Instituição dedicada ao resgate, reabilitação e adoção de pets.",
            endereco="Rua dos Resgatados, 123 - São Paulo, SP",
            telefone="(11) 99999-8888",
            email="contato@ongpatinhas.org",
            latitude="-23.550520",
            longitude="-46.633308"
        )
        db.add(ong)
        db.commit()
        db.refresh(ong)
    return ong

@app.get("/animais", tags=["Animais"])
def listar_animais(especie: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retorna a lista completa de animais cadastrados no banco de dados.
    Permite busca filtrada por espécie através do parâmetro query (ex: /animais?especie=Cão).
    """
    query = db.query(models.Animal)
    if especie:
        query = query.filter(models.Animal.especie.ilike(f"%{especie}%"))
    return query.all()

@app.get("/animais/{animal_id}", tags=["Animais"])
def obter_animal(animal_id: int, db: Session = Depends(get_db)):
    """
    Busca e retorna os detalhes de um único pet pelo seu ID primário no banco de dados.
    Corrigido: Método `.query()` (estava `.quey`).
    """
    animal = db.query(models.Animal).filter(models.Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return animal

@app.post("/animais", tags=["Administração ONG"])
def cadastrar_animal(animal: AnimalBase, db: Session = Depends(get_db)):
    """
    Endpoint administrativo para cadastrar novos pets resgatados diretamente no banco de dados.
    Corrigido: Tipagem `db: Session` (estava `db: Sessison`).
    """
    novo_pet = models.Animal(**animal.dict())
    db.add(novo_pet)
    db.commit()
    db.refresh(novo_pet)
    return {"mensagem": "Animal cadastrado com sucesso!", "pet": novo_pet}

@app.post("/solicitacoes", tags=["Adoção"])
def enviar_solicitacao_adocao(form: AdotanteForm, db: Session = Depends(get_db)):
    """
    Recebe o formulário de adoção do público, busca/cadastra o adotante no banco,
    vincula a solicitação ao pet selecionado e envia o aviso para o Telegram da ONG.
    """
    # 1. Verifica se o pet selecionado existe no banco de dados
    animal = db.query(models.Animal).filter(models.Animal.id == form.animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal selecionado não existe")

    # 2. Busca se o adotante já possui cadastro prévio pelo CPF ou registra um novo
    adotante = db.query(models.Adotante).filter(models.Adotante.cpf == form.cpf).first()
    if not adotante:
        adotante = models.Adotante(
            nome=form.nome,
            cpf=form.cpf,
            telefone=form.telefone,
            cep=form.cep
        )
        db.add(adotante)
        db.commit()
        db.refresh(adotante)

    # 3. Registra a solicitação de adoção relacionando as chaves estrangeiras
    nova_solicitacao = models.SolicitacaoAdocao(
        animal_id=animal.id,
        adotante_id=adotante.id,
        status="pendente"
    )
    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)

    # 4. Dispara a notificação via Bot do Telegram para a equipe da ONG
    notificar_telegram(form.nome, form.telefone, animal.nome)

    # Corrigido: adicionada a vírgula separadora de chaves no dicionário retornado
    return {
        "mensagem": "Solicitação de adoção enviada com sucesso! A ONG entrará em contato.",
        "solicitacao_id": nova_solicitacao.id
    }