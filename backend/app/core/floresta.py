"""Instância única da floresta de reviews usada pela API (padrão de core/README.md).

A estrutura em si (`FlorestaReviews`) é de `core/arvores.py` e não conhece banco nem servidor.
Aqui fica só a instância: ela é reconstruída no startup a partir do banco
(`services/arvores.reconstruir`) e atualizada depois de cada gravação confirmada.
"""

from app.core.arvores import FlorestaReviews

floresta = FlorestaReviews()
