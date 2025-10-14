# Em interfaces/gui_main_menu.py

import customtkinter as ctk
from pathlib import Path
from PIL import Image

# --- NOVAS IMPORTAÇÕES ---
# Importa as classes das outras janelas que este menu pode abrir
from .gui_chat import App as ChatApp
from .gui_recipe_list import App as RecipeListApp
from .gui_inventory import App as InventoryApp
from .gui_shopping_list import App as ShoppingListApp
# (Assumindo que você renomeou as classes App em cada arquivo)

class App(ctk.CTk):
    """
    A tela principal (menu) do aplicativo MyGeli.
    Agora é responsável apenas pela UI e por delegar ações.
    """
    # --- Constantes de Estilo (sem alteração) ---
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 650
    BG_COLOR = "#F5F5F5"
    HEADER_COLOR = "#0084FF"
    BUTTON_COLOR = "#0084FF"
    BUTTON_HOVER_COLOR = "#0066CC"
    BUTTON_TEXT_COLOR = "white"
    CARD_COLOR = "#FFFFFF"
    CARD_BORDER_COLOR = "#E0E0E0"

    # --- MUDANÇA IMPORTANTE NO __INIT__ ---
    def __init__(self, db_connection, chat_service, inventory_service, recipe_service):
        super().__init__()
        
        # Armazena a conexão e os serviços para poder passá-los para outras janelas
        self.db_connection = db_connection
        self.chat_service = chat_service
        self.inventory_service = inventory_service
        self.recipe_service = recipe_service
        
        self._configurar_janela()
        self._criar_fontes()
        self._criar_widgets()

    def _configurar_janela(self):
        """Define as propriedades principais da janela (sem alteração)."""
        self.title("MyGeli")
        ctk.set_appearance_mode("light")
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - self.WINDOW_WIDTH / 2)
        center_y = int(screen_height / 2 - self.WINDOW_HEIGHT / 2)
        
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{center_x}+{center_y}")
        self.minsize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.maxsize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.configure(fg_color=self.BG_COLOR)

    def _criar_fontes(self):
        """Define as fontes da aplicação (sem alteração)."""
        self.large_font = ctk.CTkFont("Poppins Bold", 28)
        self.medium_font = ctk.CTkFont("Poppins Medium", 18)
        self.small_font = ctk.CTkFont("Poppins Light", 14)
        self.button_font = ctk.CTkFont("Poppins SemiBold", 18)

    # --- NOVA LÓGICA DE NAVEGAÇÃO ---
    def _abrir_tela(self, TelaClasse, **kwargs):
        """
        Função genérica para abrir uma nova tela e esconder o menu.
        'TelaClasse' é a classe da janela a ser aberta (ex: ChatApp).
        'kwargs' são os serviços que a nova janela precisa (ex: chat_service=self.chat_service).
        """
        self.withdraw()  # Esconde a janela do menu
        
        nova_tela = TelaClasse(**kwargs) # Cria a nova janela (ex: ChatApp(chat_service=...))
        
        # Configura a nova tela para reabrir o menu quando for fechada
        nova_tela.protocol("WM_DELETE_WINDOW", lambda: self._reabrir_menu(nova_tela))

    def _reabrir_menu(self, tela_a_fechar):
        """Fecha a janela filha e reexibe o menu principal."""
        tela_a_fechar.destroy()
        self.deiconify() # Reexibe o menu

    def _criar_widgets(self):
        """Cria todos os componentes visuais da tela do menu."""
        # --- Configuração do Layout Principal (sem alteração) ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Cabeçalho (sem alteração) ---
        header_frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=self.HEADER_COLOR)
        header_frame.grid(row=0, column=0, sticky="new")
        header_frame.grid_propagate(False)

        assets_path = Path(__file__).parent.parent / "assets" # Caminho corrigido para a pasta assets na raiz
        
        user_icon_image = ctk.CTkImage(Image.open(assets_path / "frame1" / "user_icon.png").resize((32, 32), Image.LANCZOS), size=(40, 40))
        user_button = ctk.CTkButton(header_frame, text="", image=user_icon_image, width=45, height=45, fg_color="transparent", hover_color=self.BUTTON_HOVER_COLOR, command=None)
        user_button.pack(side="left", padx=10, pady=10)

        options_image = ctk.CTkImage(Image.open(assets_path / "frame1" / "options.png").resize((32, 32), Image.LANCZOS), size=(30, 30))
        options_button = ctk.CTkButton(header_frame, text="", image=options_image, width=40, height=40, fg_color="transparent", hover_color=self.BUTTON_HOVER_COLOR, command=None)
        options_button.pack(side="right", padx=5, pady=5)
        
        # --- Frame do Conteúdo Principal (sem alteração) ---
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew")

        content_block_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_block_frame.pack(side="top", fill="x", pady=(50, 0))

        logo_completo_path = assets_path / "frame1" / "MyGeli.png"
        original_logo_image = Image.open(logo_completo_path)
        original_width, original_height = original_logo_image.size
        target_width = 280
        aspect_ratio = original_height / original_width
        target_height = int(target_width * aspect_ratio)
        resized_logo = original_logo_image.resize((target_width, target_height), Image.LANCZOS)
        logo_image = ctk.CTkImage(light_image=resized_logo, size=(target_width, target_height))
        ctk.CTkLabel(content_block_frame, image=logo_image, text="").pack(pady=(0, 30))

        # --- Frame dos Botões ---
        buttons_frame = ctk.CTkFrame(content_block_frame, fg_color=self.CARD_COLOR, corner_radius=12, border_color=self.CARD_BORDER_COLOR, border_width=1)
        buttons_frame.pack(padx=30, fill="x")
        buttons_frame.grid_columnconfigure(0, weight=1)

        # --- MUDANÇA NOS COMANDOS DOS BOTÕES ---
        # Cada botão agora chama a função _abrir_tela, passando a classe da janela
        # e os serviços que ela precisa.
        ctk.CTkButton(buttons_frame, text="FALAR COM GELI", command=lambda: self._abrir_tela(ChatApp, chat_service=self.chat_service), height=55, font=self.button_font, fg_color=self.BUTTON_COLOR, hover_color=self.BUTTON_HOVER_COLOR).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        ctk.CTkButton(buttons_frame, text="VER RECEITAS", command=lambda: self._abrir_tela(RecipeListApp, recipe_service=self.recipe_service), height=55, font=self.button_font, fg_color=self.BUTTON_COLOR, hover_color=self.BUTTON_HOVER_COLOR).grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(buttons_frame, text="GERENCIAR ESTOQUE", command=lambda: self._abrir_tela(InventoryApp, inventory_service=self.inventory_service), height=55, font=self.button_font, fg_color=self.BUTTON_COLOR, hover_color=self.BUTTON_HOVER_COLOR).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(buttons_frame, text="LISTA DE COMPRAS", command=lambda: self._abrir_tela(ShoppingListApp), height=55, font=self.button_font, fg_color=self.BUTTON_COLOR, hover_color=self.BUTTON_HOVER_COLOR).grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")

# O if __name__ == "__main__": é removido. Este arquivo não é mais executável diretamente.