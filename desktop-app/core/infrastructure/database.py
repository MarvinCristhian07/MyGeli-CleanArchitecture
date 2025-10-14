import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def conectar_mysql():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        if conexao.is_connected():
            print("Log: Conexão ao MySQL bem-sucedida!")
            return conexao
    except Error as e:
        print(f"Log: Erro CRÍTICO ao conectar ao MySQL: {e}")
        return None

class ProductRepository:
    """Classe responsável por todas as operações de PRODUTOS no banco."""
    def __init__(self, connection):
        self.connection = connection

    def get_all_products(self, search_term=""):
        cursor = self.connection.cursor(dictionary=True)
        if search_term:
            query = "SELECT * FROM produtos WHERE nome_produto LIKE %s ORDER BY nome_produto ASC"
            cursor.execute(query, (f"%{search_term}%",))
        else:
            query = "SELECT * FROM produtos ORDER BY nome_produto ASC"
            cursor.execute(query)
        products = cursor.fetchall()
        cursor.close()
        return products
    
    # ... adicione aqui outros métodos como add_product, remove_product, etc.
    # Exemplo:
    def update_product_quantity(self, name, new_qty):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE produtos SET quantidade_produto = %s WHERE nome_produto = %s", (new_qty, name))
        self.connection.commit()
        cursor.close()
        
class RecipeRepository:
    """Classe responsável por todas as operações de RECEITAS no banco."""
    def __init__(self, connection):
        self.connection = connection

    def get_all_recipe_titles(self):
        """Busca os títulos de todas as receitas salvas no banco."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT tituloreceita FROM receitas")
        # O resultado vem como uma lista de tuplas, ex: [('Bolo de Fubá',), ('Frango Assado',)]
        # Por isso, pegamos o primeiro item [0] de cada tupla.
        titles = [item[0] for item in cursor.fetchall()]
        cursor.close()
        return titles

    def save_recipe(self, title, description, user_id):
        """Salva uma nova receita no banco de dados."""
        cursor = self.connection.cursor()
        query = "INSERT INTO receitas (tituloreceita, descreceita, idusuario) VALUES (%s, %s, %s)"
        cursor.execute(query, (title, description, user_id))
        self.connection.commit()
        cursor.close()

# Você pode criar outros repositórios aqui, como RecipeRepository, HistoryRepository...