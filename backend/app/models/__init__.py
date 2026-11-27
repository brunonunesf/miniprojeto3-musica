# 1 arquivo por model — evita conflito de merge quando o time trabalha em paralelo.
from app.models.comentario import Comentario  # noqa: F401
from app.models.curtida import Curtida  # noqa: F401
from app.models.follow import Follow  # noqa: F401
from app.models.musica import Musica  # noqa: F401
from app.models.post import Post  # noqa: F401
from app.models.review_apagada import ReviewApagada  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.user import User  # noqa: F401

from app.models.catalogo_externo import AuditoriaCatalogo, ReferenciaExterna, RevisaoCorrespondencia, SolicitacaoInclusao  # noqa: F401
