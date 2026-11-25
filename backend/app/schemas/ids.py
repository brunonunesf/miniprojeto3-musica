# Maior inteiro que o SQLite guarda. Um id acima disso nunca existe e, sem este limite,
# estouraria no banco como erro 500 em vez de 422.
ID_MAXIMO = 2**63 - 1
