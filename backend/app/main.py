from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import requests

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Plataforma de Adoção de Animais - ONG Parceira",
    description="API para gestão de pets e formulários de adoção (PI2 - Univesp)",
    version="2.0.0"
)

# --- MODELOS DE DADOS (Pydantic / Schemas temporários para validação) ---

class AnimalBase(BaseModel):
    nome: str
    especie: str            # Ex: Cão, Gato
    porte: str              # Ex: Pequeno, Médio, Grande
    idade_aproximada: str
    castrado: bool = False
    vacinado: bool = False
    descricao: Optional[str] = None
    foto_url: Optional[str] = None  # Corrigido: adicionado o ':' que faltava

class AdotanteForm(BaseModel):
    nome: str
    cpf: str
    telefone: str
    cep: str
    animal_id: int

# --- SIMULAÇÃO DE BANCO DE DADOS EM MEMÓRIA (Até conectar com o PostgreSQL) ---

ONG_DADOS = {
    "nome": "Ong Proteção e Amor Animal",
    "endereco": "Rua dos Resgatados, 123 - São Paulo, SP",  # Recomendado usar 'endereco' sem acento para evitar incompatibilidades de chave
    "telefone": "(11) 99999-8888",
    "email": "contato@ongpatinhas.org",
    "latitude": -23.550520,
    "longitude": -46.633308
}

ANIMAIS_DB = [
    {
        "id": 1,
        "nome": "Thor",
        "especie": "Cão",
        "porte": "Médio",
        "idade_aproximada": "2 anos",
        "castrado": True,
        "vacinado": True,
        "status": "disponivel",
        "foto_url": "https://placekitten.com/300/300"
    },
    {
        "id": 2,
        "nome": "Mia",
        "especie": "Gato",
        "porte": "Pequeno",
        "idade_aproximada": "6 meses",
        "castrado": True,
        "vacinado": True,
        "status": "disponivel",
        "foto_url": "https://placekitten.com/301/301"
    }
]

SOLICITACOES_DB = []

# --- INTEGRAÇÃO COM API EXTERNA (Bot do Telegram) ---

def notificar_telegram(nome_adotante: str, telefone: str, nome_pet: str):
    """Função utilitária para notificar a ONG via Telegram quando houver novo interesse"""
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

@app.get("/", tags=["Geral"])  # Corrigido: ajustado parênteses/sintaxe do parâmetro tags
def home():
    """Endpoint raiz para verificar a saúde da API"""
    return {
        "projeto": "Plataforma de Adoção de Animais - PI2 Univesp",
        "status": "Online",
        "versao": "2.0.0"
    }

@app.get("/ong", tags=["ONG"])
def obter_dados_ong():
    """Retorna os dados institucionais e a localização fixa da ONG para exibição no mapa"""
    return ONG_DADOS

@app.get("/animais", tags=["Animais"])
def listar_animais(especie: Optional[str] = None):
    """Lista todos os animais disponíveis para adoção, com filtro opcional por espécie"""
    if especie:
        filtrados = [a for a in ANIMAIS_DB if a["especie"].lower() == especie.lower()]
        return filtrados
    return ANIMAIS_DB

@app.get("/animais/{animal_id}", tags=["Animais"])
def obter_animal(animal_id: int):
    """Retorna os detalhes de um animal específico"""
    animal = next((a for a in ANIMAIS_DB if a["id"] == animal_id), None)  # Corrigido erro de digitação 'dor' -> 'for'
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return animal

@app.post("/animais", tags=["Administração ONG"])
def cadastrar_animal(animal: AnimalBase):
    """Rota restrita para a ONG cadastrar novos pets resgatados"""
    novo_id = len(ANIMAIS_DB) + 1
    novo_pet = animal.dict()
    novo_pet["id"] = novo_id
    novo_pet["status"] = "disponivel"

    ANIMAIS_DB.append(novo_pet)
    return {"mensagem": "Animal cadastrado com sucesso!", "pet": novo_pet}  # Corrigido aspas em "mensagem"

@app.post("/solicitacoes", tags=["Adoção"])
def enviar_solicitacao_adocao(form: AdotanteForm):
    """Recebe o formulário de interesse de um adotante e dispara o aviso para a ONG"""
    animal = next((a for a in ANIMAIS_DB if a["id"] == form.animal_id), None)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal selecionado não existe")  # Corrigido: HTTException -> HTTPException

    nova_solicitacao = {
        "id": len(SOLICITACOES_DB) + 1,
        "adotante": form.nome,
        "cpf": form.cpf,
        "telefone": form.telefone,
        "cep": form.cep,
        "animal": animal["nome"],
        "status": "pendente"  # Corrigido: adicionado os ':' que faltavam
    }

    SOLICITACOES_DB.append(nova_solicitacao)

    # Notifica o grupo da ONG via API do Telegram
    notificar_telegram(form.nome, form.telefone, animal["nome"])

    return {
        "mensagem": "Solicitação de adoção enviada com sucesso! A ONG entrará em contato.",
        "solicitacao_id": nova_solicitacao["id"]
    }