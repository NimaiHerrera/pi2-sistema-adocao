from fastapi import FastAPI

app = FastAPI(title="API Comparador de Preços")


@app.get("/")
def home():
    return {
        "mensagem": "API do Projeto Integrador II - Univesp",
        "status": "Online"
    }
