# Cole este código em domain/user.py

class User:
    def __init__(self, user_id, name, phone, email, password_hash):
        if not name or not email:
            raise ValueError("Nome e E-mail são campos obrigatórios.")
        
        self.user_id = user_id
        self.name = name
        self.phone = phone
        self.email = email
        self.password_hash = password_hash # Armazenamos apenas o hash, não a senha