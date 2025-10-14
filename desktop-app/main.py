# Em /main.py

import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv

# --- 1. Importações das Camadas ---

# Infrastructure: A camada que fala com o mundo exterior (banco de dados, APIs, arquivos)
from core.infrastructure.database import conectar_mysql, ProductRepository, RecipeRepository
from core.infrastructure.gemini_api import GeminiAPI
from core.infrastructure.file_repository import FileRepository

# Application: A camada que contém a lógica de negócio (os "cérebros" de cada tela)
from core.application.chat_service import ChatService
from core.application.inventory_service import InventoryService
from core.application.recipe_service import RecipeService
from core.application.shopping_list_service import ShoppingListService

# Interfaces: A camada que o usuário vê (a janela principal)
from interfaces.gui_main_menu import App as MainMenuApp

def main():
    """
    Função principal que inicializa e executa a aplicação desktop MyGeli.
    """
    # Carrega as variáveis de ambiente do arquivo .env (DB_USER, GOOGLE_API_KEY, etc.)
    load_dotenv()

    # --- 2. Montagem das Dependências (Injeção de Dependência) ---

    # Conecta ao banco de dados UMA VEZ no início de tudo
    db_connection = conectar_mysql()

    if not db_connection:
        # Se a conexão com o banco de dados falhar, exibe um erro crítico e encerra.
        root = ctk.CTk()
        root.withdraw()  # Esconde a janela principal vazia
        messagebox.showerror("Erro Crítico de Conexão", 
                             "Não foi possível conectar ao banco de dados.\n\n"
                             "Verifique se o servidor MySQL está rodando e se as "
                             "credenciais no arquivo .env estão corretas.")
        root.destroy()
        return

    try:
        # -- Camada de Infraestrutura --
        # Instancia todos os repositórios e APIs, que são a base de tudo.
        product_repo = ProductRepository(db_connection)
        recipe_repo = RecipeRepository(db_connection)
        file_repo = FileRepository()
        gemini_api = GeminiAPI()

        # -- Camada de Aplicação --
        # Instancia os serviços, "injetando" as dependências (repositórios, APIs) que cada um precisa.
        chat_service = ChatService(
            db_repo=product_repo,
            recipe_repo=recipe_repo,
            gemini_api=gemini_api,
            file_repo=file_repo
        )
        
        inventory_service = InventoryService(
            product_repo=product_repo,
            gemini_api=gemini_api
        )

        recipe_service = RecipeService(
            recipe_repo=recipe_repo,
            file_repo=file_repo,
            product_repo=product_repo,
            gemini_api=gemini_api
        )

        shopping_list_service = ShoppingListService(
            file_repo=file_repo,
            product_repo=product_repo
        )

        # --- 3. Iniciação da Interface ---
        # Cria a janela do menu principal, passando todos os serviços que ela e as outras janelas precisarão.
        app = MainMenuApp(
            db_connection=db_connection, 
            chat_service=chat_service,
            inventory_service=inventory_service,
            recipe_service=recipe_service,
            shopping_list_service=shopping_list_service
        )
        app.mainloop()

    finally:
        # Garante que a conexão com o banco de dados seja fechada ao final da execução, não importa o que aconteça.
        if db_connection and db_connection.is_connected():
            db_connection.close()
            print("Log: Conexão com o Banco de Dados fechada com sucesso.")


if __name__ == "__main__":
    main()