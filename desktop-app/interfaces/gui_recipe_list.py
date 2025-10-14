# Em interfaces/gui_recipe_list.py

import customtkinter as ctk
from tkinter import messagebox, simpledialog
from pathlib import Path
from PIL import Image
import threading

# A UI não tem mais conhecimento de banco de dados, arquivos ou API.

class App(ctk.CTk):
    def __init__(self, recipe_service, on_close_callback):
        super().__init__()
        self.recipe_service = recipe_service
        self.on_close_callback = on_close_callback  # Função para reabrir o menu principal

        self.title("MyGeli - Minhas Receitas")
        self.geometry("400x650")
        self.minsize(400, 650)
        self.configure(fg_color="#F5F5F5")
        
        self.update_idletasks()
        width, height = 400, 650
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.title_font = ctk.CTkFont("Poppins Bold", 22)
        self.header_font = ctk.CTkFont("Poppins Medium", 16)
        self.item_font = ctk.CTkFont("Poppins Regular", 14)
        
        self._create_widgets()
        self.populate_recipe_buttons()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close_callback)

    def _create_widgets(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#0084FF")
        header_frame.grid(row=0, column=0, sticky="new")
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(1, weight=1)

        assets_path = Path(__file__).parent.parent / "assets" / "geral"
        
        try:
            seta_img = ctk.CTkImage(Image.open(assets_path / "seta.png").resize((30, 30)), size=(30, 30))
            back_btn = ctk.CTkButton(header_frame, text="", image=seta_img, width=40, height=40, fg_color="transparent", hover_color="#0066CC", command=self.on_close_callback)
            back_btn.grid(row=0, column=0, padx=10, pady=20, sticky="w")
        except Exception:
            back_btn = ctk.CTkButton(header_frame, text="Voltar", command=self.on_close_callback)
            back_btn.grid(row=0, column=0, padx=10, pady=20, sticky="w")

        ctk.CTkLabel(header_frame, text="Minhas Receitas", font=self.title_font, text_color="white").grid(row=0, column=1, pady=20, sticky="nsew")

        self.recipe_list_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF", corner_radius=0)
        self.recipe_list_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.recipe_list_frame.grid_columnconfigure(0, weight=1)

    def populate_recipe_buttons(self):
        # Limpa a lista atual
        for widget in self.recipe_list_frame.winfo_children():
            widget.destroy()

        # Pede as receitas ao serviço
        recipes = self.recipe_service.get_all_recipes()

        if not recipes:
            ctk.CTkLabel(self.recipe_list_frame, text="Nenhuma receita salva ainda.", font=self.header_font, text_color="#666").pack(pady=30)
            return

        for recipe in recipes:
            display_text = recipe['display_name']
            button_color = "#FFFFE0" if recipe['is_favorite'] else "#FFFFFF"
            text_color = "#4C4C00" if recipe['is_favorite'] else "#333333"

            btn = ctk.CTkButton(
                self.recipe_list_frame,
                text=display_text,
                fg_color=button_color,
                text_color=text_color,
                hover_color="#E0E0E0",
                height=50,
                font=self.item_font,
                anchor="w",
                border_width=1,
                border_color="#E0E0E0",
                command=lambda p=recipe['path']: self.display_selected_recipe(p)
            )
            btn.pack(fill="x", pady=(0, 5), padx=5)
            # A lógica de menu de clique direito (long press) pode ser adicionada aqui depois

    def display_selected_recipe(self, recipe_path):
        # Lógica para exibir a janela Toplevel com os detalhes da receita
        # Esta função será grande, contendo a criação da nova janela,
        # botões de editar, consumir, favoritar, etc.
        # Todos os botões chamarão métodos do self.recipe_service.
        # Ex: self.recipe_service.consume_recipe_ingredients(...)
        messagebox.showinfo("Em Desenvolvimento", f"Aqui abriria a receita do caminho:\n{recipe_path}", parent=self)

# Bloco de teste (opcional, para rodar este arquivo isoladamente)
if __name__ == "__main__":
    # --- Simulações para teste ---
    class MockRepo:
        def get_all_recipes_from_files(self):
            print("MOCK: Buscando receitas...")
            return [
                {'display_name': '★ Bolo de Cenoura', 'is_favorite': True, 'path': 'path/to/bolo.txt'},
                {'display_name': 'Frango Assado', 'is_favorite': False, 'path': 'path/to/frango.txt'}
            ]
    
    class MockService:
        def __init__(self):
            self.repo = MockRepo()
        def get_all_recipes(self):
            return self.repo.get_all_recipes_from_files()

    # --- Execução do teste ---
    def on_test_close():
        print("Fechando a janela de teste.")
        app.destroy()

    app = App(recipe_service=MockService(), on_close_callback=on_test_close)
    app.mainloop()