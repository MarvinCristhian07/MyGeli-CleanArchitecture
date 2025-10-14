# Em interfaces/gui_shopping_list.py

import customtkinter as ctk
from tkinter import messagebox

class App(ctk.CTk):
    def __init__(self, shopping_list_service, on_close_callback):
        super().__init__()
        self.service = shopping_list_service
        self.on_close_callback = on_close_callback
        
        self.title("MyGeli - Lista de Compras")
        self.geometry("800x600")
        self.configure(fg_color="#f0f0f0")

        self.protocol("WM_DELETE_WINDOW", self.on_close_callback)
        
        self._create_widgets()
        self.load_shopping_list()

    def _create_widgets(self):
        """Cria todos os componentes visuais da tela."""
        # Título principal
        ctk.CTkLabel(
            self, text="Lista de Compras Sugerida",
            font=ctk.CTkFont(size=24, weight="bold"), text_color="#2e7d32"
        ).pack(pady=(20, 10))
        
        # Subtítulo
        ctk.CTkLabel(
            self, text="Sugestões baseadas no seu consumo e utilização do app",
            font=ctk.CTkFont(size=14), text_color="#666666"
        ).pack(pady=(0, 20))
        
        # Frame principal para a lista
        main_frame = ctk.CTkFrame(self, fg_color="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.list_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame para botões de ação
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            buttons_frame, text="Adicionar Manualmente", width=180, height=40,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#4caf50",
            hover_color="#45a049", command=self.add_item_manually
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            buttons_frame, text="Remover Selecionados", width=180, height=40,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#f44336",
            hover_color="#d32f2f", command=self.remove_checked_items
        ).pack(side="left")
        
        ctk.CTkButton(
            buttons_frame, text="Salvar Lista", width=150, height=40,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#2196f3",
            hover_color="#1976d2", command=self.save_list
        ).pack(side="right")

    def load_shopping_list(self):
        """Pede a lista ao serviço e a exibe na tela."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        # Pede os dados ao serviço
        shopping_list_items = self.service.generate_suggested_list()
        
        for item in shopping_list_items:
            self.create_list_item_widget(item)

    def create_list_item_widget(self, item):
        """Cria o widget para um único item da lista."""
        item_frame = ctk.CTkFrame(self.list_frame, height=60, fg_color="#3B82F6", corner_radius=10)
        item_frame.pack(fill="x", padx=10, pady=5)
        item_frame.pack_propagate(False)

        def on_check_change():
            item["checked"] = checkbox_var.get()

        checkbox_var = ctk.BooleanVar(value=item.get("checked", False))
        checkbox = ctk.CTkCheckBox(item_frame, text="", variable=checkbox_var, width=20, command=on_check_change)
        checkbox.pack(side="left", padx=(10, 15), pady=15)
        
        ctk.CTkLabel(
            item_frame, text=item["nome"], font=ctk.CTkFont(size=14, weight="bold"),
            width=200, anchor="w"
        ).pack(side="left", padx=(0, 10), pady=15)
        
        ctk.CTkLabel(
            item_frame, text=f"{item['quantidade']} {item['unidade']}",
            font=ctk.CTkFont(size=12), width=120, anchor="w"
        ).pack(side="left", padx=(0, 10), pady=15)

        def remove_action():
            if self.service.remove_item(item):
                item_frame.destroy()
        
        ctk.CTkButton(
            item_frame, text="Remover", width=80, height=30,
            font=ctk.CTkFont(size=11), fg_color="#d32f2f",
            hover_color="#b71c1c", command=remove_action
        ).pack(side="right", padx=(10, 10), pady=15)

    def add_item_manually(self):
        """Abre diálogos para adicionar um item e pede ao serviço para adicioná-lo."""
        dialog_name = ctk.CTkInputDialog(text="Digite o nome do produto:", title="Adicionar Item")
        name = dialog_name.get_input()
        if not name: return

        dialog_qty = ctk.CTkInputDialog(text="Digite a quantidade:", title="Quantidade")
        qty = dialog_qty.get_input()
        if not qty: return

        dialog_unit = ctk.CTkInputDialog(text="Digite a unidade (ex: kg, L, un):", title="Unidade")
        unit = dialog_unit.get_input()
        if not unit: return

        # Pede ao serviço para adicionar o item
        new_item = self.service.add_item(name, qty, unit)
        # Cria o widget para o novo item
        self.create_list_item_widget(new_item)
        messagebox.showinfo("Sucesso", f"Item '{name}' adicionado à lista!")

    def remove_checked_items(self):
        """Pede ao serviço para remover itens marcados e atualiza a UI."""
        removed_count = self.service.remove_checked_items()
        if removed_count > 0:
            # Recarrega a lista inteira para refletir as remoções
            self.load_shopping_list()
            messagebox.showinfo("Itens Removidos", f"{removed_count} item(s) removido(s) da lista.")
        else:
            messagebox.showwarning("Nenhum Item Selecionado", "Selecione pelo menos um item para remover.")
            
    def save_list(self):
        """Pede ao serviço para salvar a lista em um arquivo."""
        result = self.service.save_list_to_file()
        if result["status"] == "success":
            messagebox.showinfo("Lista Salva", f"Lista de compras salva em:\n{result['path']}")
        else:
            messagebox.showwarning("Aviso", result["message"])

# Bloco de teste (opcional)
if __name__ == "__main__":
    # Simulações para teste
    class MockFileRepo:
        def save_shopping_list(self, content):
            path = "lista_compras_teste.txt"
            with open(path, "w") as f:
                f.write(content)
            return path
    
    # Execução do teste
    def on_test_close():
        app.destroy()

    service = ShoppingListService(file_repo=MockFileRepo())
    app = App(shopping_list_service=service, on_close_callback=on_test_close)
    app.mainloop()