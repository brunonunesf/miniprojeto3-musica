# 1 arquivo por model — evita conflito de merge quando o time trabalha em paralelo.
from app.models.musica import Musica  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.user import User  # noqa: F401
