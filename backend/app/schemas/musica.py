from pydantic import BaseModel, ConfigDict


class MusicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chave_catalogo: str
    titulo: str
    artista: str
    tipo_versao: str
    descricao_versao: str
    generos: list[str]
    tags: list[str]
    capa_url: str


class MusicaPage(BaseModel):
    items: list[MusicaOut]
    total: int
    offset: int
    limit: int
