from pydantic import BaseModel


class CurtidaOut(BaseModel):
    """Estado da curtida depois de curtir ou descurtir, para a tela não precisar de outra consulta."""

    curtidas: int
    curtido_por_mim: bool
