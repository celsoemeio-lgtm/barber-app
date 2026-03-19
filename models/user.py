class User:
    """Modelo simples de usuário"""
    def __init__(self, nome, tipo, nivel=None):
        self.nome = nome
        self.tipo = tipo  # 'BARBEIRO' ou 'CLIENTE'
        self.nivel = nivel  # 'ADM' ou 'USER' (só para barbeiros)
        self.logado = True
    
    def to_dict(self):
        return {
            'nome': self.nome,
            'tipo': self.tipo,
            'nivel': self.nivel,
            'logado': True
        }