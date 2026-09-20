from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import requests

from .database import engine, Base, get_db
from . import models

# Cria as tabelas automaticamente no banco SQLite se não existirem
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Plataforma de Adoção de Animais - ONG Parceira",
    description="API RESTful para gestão de pets resgatados e formulários de adoção (PI2 - Univesp)",
    version="2.0.0"
)

# Configuração do CORS para permitir requisições do Front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS (Schemas Pydantic para validação das requisições) ---

class AnimalBase(BaseModel):
    nome: str
    especie: str       # Ex: Cão, Gato
    porte: str         # Ex: Pequeno, Médio, Grande
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

# --- INTEGRAÇÃO COM API EXTERNA (Bot do Telegram) ---

def notificar_telegram(nome_adotante: str, telefone: str, nome_pet: str):
    """Função utilitária para notificar a ONG via Telegram quando houver nova solicitação"""
    TOKEN_BOT = "SEU_TELEGRAM_BOT_TOKEN"
    CHAT_ID = "SEU_TELEGRAM_CHAT_ID"

    mensagem = (
        f"🐾 *NOVA SOLICITAÇÃO DE ADOÇÃO!*\n\n"
        f"👤 *Adotante:* {nome_adotante}\n"
        f"📞 *Telefone:* {telefone}\n"
        f"🐶 *Pet de Interesse:* {nome_pet}\n\n"
        f"_Verifique o painel para mais detalhes._"
    )

    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[Aviso Telegram] Não foi possível enviar a notificação: {e}")

# --- ENDPOINTS DA API ---

@app.get("/", tags=["Geral"])
def home():
    """Endpoint raiz para verificar a saúde da API"""
    return {
        "projeto": "Plataforma de Adoção de Animais - PI2 Univesp",
        "status": "Online",
        "versao": "2.0.0"
    }

@app.get("/ong", tags=["ONG"])
def obter_dados_ong(db: Session = Depends(get_db)):
    """Retorna os dados institucionais e localização da ONG cadastrada no banco"""
    ong = db.query(models.Ong).first()
    if not ong:
        # Se não houver registro no banco, retorna dados padrão de fallback
        return {
            "nome": "ONG Proteção e Amor Animal",
            "descricao": "Resgatamos e cuidamos de animais abandonados.",
            "endereco": "Rua dos Resgatados, 123 - São Paulo, SP",
            "telefone": "(11) 99999-8888",
            "email": "contato@ongpatinhas.org"
        }
    return ong

@app.get("/animais", tags=["Animais"])
def listar_animais(especie: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista todos os animais do banco de dados, com filtro opcional por espécie"""
    query = db.query(models.Animal)
    if especie:
        query = query.filter(models.Animal.especie.ilike(f"%{especie}%"))
    return query.all()

@app.get("/animais/{animal_id}", tags=["Animais"])
def obter_animal(animal_id: int, db: Session = Depends(get_db)):
    """Retorna os detalhes de um animal específico cadastrado no banco"""
    animal = db.query(models.Animal).filter(models.Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return animal

@app.post("/animais", tags=["Administração ONG"])
def cadastrar_animal(animal: AnimalBase, db: Session = Depends(get_db)):
    """Rota para cadastrar novos pets resgatados diretamente no banco SQLite"""
    novo_pet = models.Animal(**animal.dict())
    db.add(novo_pet)
    db.commit()
    db.refresh(novo_pet)
    return {"mensagem": "Animal cadastrado com sucesso!", "pet": novo_pet}

@app.post("/solicitacoes", tags=["Adoção"])
def enviar_solicitacao_adocao(form: AdotanteForm, db: Session = Depends(get_db)):
    """Recebe o formulário de interesse de um adotante e grava a solicitação no banco"""
    # 1. Verifica se o pet existe
    animal = db.query(models.Animal).filter(models.Animal.id == form.animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal selecionado não existe")

    # 2. Verifica se o adotante já possui cadastro pelo CPF ou cria um novo
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

    # 3. Salva a solicitação de adoção no banco
    nova_solicitacao = models.SolicitacaoAdocao(
        animal_id=animal.id,
        adotante_id=adotante.id,
        status="pendente"
    )
    db.add(nova_solicitacao)
    db.commit()
    db.refresh(nova_solicitacao)

    # 4. Envia o aviso via Telegram
    notificar_telegram(form.nome, form.telefone, animal.nome)

    return {
        "mensagem": "Solicitação de adoção enviada com sucesso! A ONG entrará em contato.",
        "solicitacao_id": nova_solicitacao.id
    }

@app.get('/solicitacoes', tags=["Administração ONG"])
def listar_solicitacoes(db: Session = Depends(get_db)):
    """Retorna todas as solicitações de adoção enviadas com os dados do adotante e do pet"""
    solicitacoes = db.query(models.SolicitacaoAdoao).all()
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

@app.patch("/solicitacoes/{solicitacao_id}", tags=["Administração ONG"])
def atualizar_status_solicitacao(solicitacao_id: int, novo_status: str, db: Session = Depends(get_db)):
    """Atualiza o status de uma solicitação de adoção (ex: 'aprovado' ou 'recusado')"""
    solicitacao = db.query(models.SolicitacaoAdocao).filter(models.SolicitacaoAdocao.id == solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    solicitacao.status = novo_status
    db.commit()
    db.refresh(solicitacao)
    return {"mensagem": f"Status atualizado para '{novo_status}' com sucesso!"}

@app.delete("/animais/{animal_id}", tags=["Administração ONG"])
def remover_animal(animal_id: int, db: Session = Depends(get_db)):
    """Remove um animal do banco de dados permanentemente"""
    animal = db.query(models.Animal).filter(models.Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    
    db.delete(animal)
    db.commit()
    return {"mensagem": f"Animal '{animal.nome}' removido com sucesso!"}