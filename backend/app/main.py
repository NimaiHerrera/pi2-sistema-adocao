"""
API RESTful - Plataforma de Gestão e Adoção Responsável de Animais
ONG Parceira: Instituto / Projeto Pancinha Feliz da Lili (Mauá - SP)
Projeto Integrador II - Univesp (2026)
"""

from typing import List, Optional
import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import models
from .database import Base, engine, get_db

# Criação automática das tabelas no SQLite
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Plataforma de Adoção de Animais - Pancinha Feliz da Lili",
    description="API para gestão da vitrine de pets resgatados e solicitações de adoção.",
    version="2.0.0",
)

# Configuração de CORS para permitir requisições do front-end
app.add_middleware(
    CORSMiddleware,
    # Em produção, substitua pelas URLs exatas da Vercel/Netlify
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# SCHEMAS PYDANTIC (Validação de Entrada e Saída)
# ==============================================================================

class AnimalBase(BaseModel):
    nome: str = Field(..., example="Mel")
    especie: str = Field(..., example="Cão")
    porte: str = Field(..., example="Médio")
    idade_aproximada: Optional[str] = Field(None, example="1 ano")
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


class SolicitacaoStatusUpdate(BaseModel):
    status: str = Field(..., example="aprovado")


class LoginSchema(BaseModel):
    usuario: str = Field(..., example="admin")
    senha: str = Field(..., example="pancinha123")


# ==============================================================================
# SERVIÇOS AUXILIARES E INTEGRAÇÕES
# ==============================================================================

def notificar_telegram(nome_adotante: str, telefone: str, nome_pet: str) -> None:
    """Envia uma notificação assíncrona ao Telegram da ONG quando um novo formulário é enviado."""
    TOKEN_BOT = "SEU_TELEGRAM_BOT_TOKEN"
    CHAT_ID = "SEU_TELEGRAM_CHAT_ID"

    if TOKEN_BOT == "SEU_TELEGRAM_BOT_TOKEN":
        return  # Bot não configurado; pula a notificação sem interromper o fluxo

    mensagem = (
        f"🐾 *NOVA SOLICITAÇÃO DE ADOÇÃO!*\n\n"
        f"👤 *Adotante:* {nome_adotante}\n"
        f"📞 *Telefone:* {telefone}\n"
        f"🐶 *Pet:* {nome_pet}\n\n"
        f"_Acesse o painel administrativo para analisar._"
    )

    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as err:
        print(f"[Aviso] Falha ao notificar via Telegram: {err}")


# ==============================================================================
# ENDPOINTS / ROTAS DA API
# ==============================================================================

@app.get("/", tags=["Geral"])
def check_health():
    """Endpoint para verificação do status da aplicação."""
    return {
        "projeto": "Plataforma de Adoção de Animais - Pancinha Feliz da Lili",
        "status": "Online",
        "versao": "2.0.0"
    }


@app.get("/ong", tags=["ONG"])
def obter_dados_ong(db: Session = Depends(get_db)):
    """Retorna os dados institucionais da ONG. Se não existirem, cria o registro inicial."""
    ong = db.query(models.ONG).first()
    if not ong:
        ong = models.ONG(
            nome="Pancinha Feliz da Lili",
            descricao="Instituição dedicada ao resgate, cuidado e adoção responsável de animais.",
            endereco="Mauá - SP",
            telefone="(11) 97319-0676",
            email="contato@pancinhafelizdalili.org",
            latitude="-23.550520",
            longitude="-46.633308"
        )
        db.add(ong)
        db.commit()
        db.refresh(ong)
    return ong


@app.get("/animais", tags=["Animais (Público)"])
def listar_animais_disponiveis(especie: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista apenas pets com status 'disponivel' para a vitrine pública."""
    query = db.query(models.Animal).filter(
        models.Animal.status == "disponivel")
    if especie:
        query = query.filter(models.Animal.especie.ilike(f"%{especie}%"))
    return query.all()


@app.get("/animais/{animal_id}", tags=["Animais (Público)"])
def obter_detalhes_animal(animal_id: int, db: Session = Depends(get_db)):
    """Retorna as informações completas de um pet específico pelo ID."""
    animal = db.query(models.Animal).filter(
        models.Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return animal


@app.post("/animais", status_code=status.HTTP_201_CREATED, tags=["Painel Administrativo"])
def cadastrar_novo_animal(animal: AnimalBase, db: Session = Depends(get_db)):
    """Cadastra um novo animal resgatado no banco de dados."""
    novo_pet = models.Animal(**animal.dict())
    db.add(novo_pet)
    db.commit()
    db.refresh(novo_pet)
    return {"mensagem": "Animal cadastrado com sucesso!", "pet": novo_pet}


@app.delete("/animais/{animal_id}", tags=["Painel Administrativo"])
def remover_animal(animal_id: int, db: Session = Depends(get_db)):
    """Remove permanentemente um pet do sistema (exclusão em cascata das solicitações vinculadas)."""
    animal = db.query(models.Animal).filter(
        models.Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    db.delete(animal)
    db.commit()
    return {"mensagem": f"Animal '{animal.nome}' e seus registros vinculados foram removidos com sucesso!"}


@app.post("/solicitacoes", status_code=status.HTTP_201_CREATED, tags=["Adoção (Público)"])
def registrar_solicitacao_adocao(form: AdotanteForm, db: Session = Depends(get_db)):
    """Recebe o formulário público do adotante e registra a solicitação no banco."""
    animal = db.query(models.Animal).filter(
        models.Animal.id == form.animal_id).first()
    if not animal:
        raise HTTPException(
            status_code=404, detail="O pet selecionado não existe ou não está mais disponível.")

    # Cadastra ou atualiza os dados do adotante pelo CPF
    adotante = db.query(models.Adotante).filter(
        models.Adotante.cpf == form.cpf).first()
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

    # Cria a nova solicitação vinculada
    nova_solicitacao = models.SolicitacaoAdocao(
        animal_id=animal.id,
        adotante_id=adotante.id,
        status="pendente"
    )
    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)

    # Dispara aviso no Telegram se estiver configurado
    notificar_telegram(form.nome, form.telefone, animal.nome)

    return {
        "mensagem": "Solicitação enviada com sucesso! A equipe da ONG entrará em contato em breve.",
        "solicitacao_id": nova_solicitacao.id
    }


@app.get("/solicitacoes", tags=["Painel Administrativo"])
def listar_solicitacoes_adocao(db: Session = Depends(get_db)):
    """Retorna a lista de solicitações de adoção para análise da ONG."""
    solicitacoes = db.query(models.SolicitacaoAdocao).all()
    resultado = []

    for sol in solicitacoes:
        resultado.append({
            "id": sol.id,
            "data_solicitacao": sol.data_solicitacao,
            "status": sol.status,
            "adotante": {
                "id": sol.adotante.id,
                "nome": sol.adotante.nome,
                "cpf": sol.adotante.cpf,
                "telefone": sol.adotante.telefone,
                "cep": sol.adotante.cep
            },
            "animal": {
                "id": sol.animal.id,
                "nome": sol.animal.nome,
                "especie": sol.animal.especie
            }
        })
    return resultado


@app.patch("/solicitacoes/{solicitacao_id}", tags=["Painel Administrativo"])
def atualizar_status_solicitacao(
    solicitacao_id: int,
    novo_status: str,
    db: Session = Depends(get_db)
):
    """
    Atualiza o status de uma solicitação ('aprovado' ou 'recusado').
    Ao aprovar, altera automaticamente o status do pet para 'adotado'.
    """
    solicitacao = db.query(models.SolicitacaoAdocao).filter(
        models.SolicitacaoAdocao.id == solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=404, detail="Solicitação não encontrada.")

    solicitacao.status = novo_status.lower()

    # Fluxo automático: Se aprovado, retira o pet da vitrine pública
    if novo_status.lower() == "aprovado":
        animal = db.query(models.Animal).filter(
            models.Animal.id == solicitacao.animal_id).first()
        if animal:
            animal.status = "adotado"

    db.commit()
    db.refresh(solicitacao)
    return {"mensagem": f"Status atualizado para '{novo_status}' com sucesso!"}


@app.delete("/solicitacoes/{solicitacao_id}", tags=["Painel Administrativo"])
def remover_solicitacao(solicitacao_id: int, db: Session = Depends(get_db)):
    """Remove permanentemente uma solicitação de adoção do banco de dados."""
    solicitacao = db.query(models.SolicitacaoAdocao).filter(
        models.SolicitacaoAdocao.id == solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(
            status_code=404, detail="Solicitação não encontrada.")

    db.delete(solicitacao)
    db.commit()
    return {"mensagem": "Solicitação removida com sucesso!"}

# ==============================================================================
# ENDPOINT DE AUTENTICAÇÃO / LOGIN
# ==============================================================================


@app.post("/login", tags=["Autenticação"])
def autenticar_administrador(credenciais: LoginSchema):
    """
    Valida o usuário e a senha do administrador da ONG.
    """
    # Credenciais padrão para a gestão do painel
    USUARIO_CORRETO = "admin"
    SENHA_CORRETA = "pancinha123"

    if credenciais.usuario == USUARIO_CORRETO and credenciais.senha == SENHA_CORRETA:
        return {
            "autenticado": True,
            "mensagem": "Login realizado com sucesso!",
            "usuario": credenciais.usuario
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário ou senha incorretos."
    )
