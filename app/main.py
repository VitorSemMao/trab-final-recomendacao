from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="Sistema de Recomendacao", version="0.1.0")


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    preferences: list[str] = Field(default_factory=list)


class ItemCreate(BaseModel):
    title: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class PreferenceUpdate(BaseModel):
    preferences: list[str] = Field(default_factory=list)


def not_implemented(detail: str) -> None:
    raise HTTPException(status_code=501, detail=detail)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Projeto inicial do sistema de recomendacao",
        "phase": "fase 1",
        "status": "em desenvolvimento",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/users")
def create_user(payload: UserCreate) -> None:
    not_implemented("Cadastro de usuarios sera implementado na proxima fase.")


@app.post("/items")
def create_item(payload: ItemCreate) -> None:
    not_implemented("Cadastro de itens sera implementado na proxima fase.")


@app.get("/users/{user_id}/recommendations")
def get_recommendations(user_id: int) -> None:
    not_implemented("Motor de recomendacao sera implementado na proxima fase.")


@app.put("/users/{user_id}/preferences")
def update_preferences(user_id: int, payload: PreferenceUpdate) -> None:
    not_implemented("Atualizacao de preferencias sera implementada na proxima fase.")
