import customtkinter as ctk
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from tkinter import messagebox

class ChatMessage(ctk.CTkFrame):
    def __init__(self, master, text, sender, **kwargs):
        super().__init__(master, **kwargs)
        try:
            self.large_font = ctk.CTkFont("Poppins Bold", 28)
            self.medium_font = ctk.CTkFont("Poppins Medium", 18)
            self.small_font = ctk.CTkFont("Poppins Light", 14)
            self.button_font = ctk.CTkFont("Poppins SemiBold", 18)
            self.robot_font = ctk.CTkFont("Segoe UI Emoji", 80)
        except Exception:
            self.large_font = ctk.CTkFont("Arial", 28, "bold")
            self.medium_font = ctk.CTkFont("Arial", 18)
            self.small_font = ctk.CTkFont("Arial", 14)
            self.button_font = ctk.CTkFont("Arial", 18, "bold")
            self.title_font = ctk.CTkFont("Arial", 22, "bold")
            self.header_font = ctk.CTkFont("Arial", 16)

        if sender == "user":
            self.configure(fg_color="#0084FF", corner_radius=12)
            label = ctk.CTkLabel(self, text=text, text_color="white",
                                 font=("Helvetica", 14), wraplength=280, justify="left")
            label.pack(padx=12, pady=8)
            self.pack(anchor="e", pady=(5, 0), padx=(60, 10), fill="x")
        elif sender == "bot_typing":
            self.configure(fg_color="transparent", corner_radius=12)
            label = ctk.CTkLabel(self, text=text, text_color="#666666",
                                 font=("Helvetica", 12, "italic"), wraplength=280, justify="left")
            label.pack(padx=12, pady=(2,2))
            self.pack(anchor="w", pady=(2,0), padx=(10,60), fill="x")
        elif sender == "bot_info" or sender == "bot_error": # Para mensagens informativas/erro do bot
            self.configure(fg_color="#F0F0F0", corner_radius=8) # Cor de fundo diferente para destaque
            text_color = "#333333" if sender == "bot_info" else "#D32F2F" # Vermelho para erro
            label = ctk.CTkLabel(self, text=text, text_color=text_color,
                                 font=("Helvetica", 12, "italic" if sender == "bot_info" else "bold"),
                                 wraplength=280, justify="center")
            label.pack(padx=10, pady=6)
            self.pack(anchor="center", pady=(8, 0), padx=20, fill="x") # Centralizado
        else: # Bot (Geli)
            self.configure(fg_color="#EAEAEA", corner_radius=12)
            label = ctk.CTkLabel(self, text=text, text_color="black",
                                 font=("Helvetica", 14), wraplength=280, justify="left")
            label.pack(padx=12, pady=8)
            self.pack(anchor="w", pady=(5, 0), padx=(10, 60), fill="x")
            
class App(ctk.CTk):
    def __init__(self, chat_service):
        super().__init__()
        self.chat_service = chat_service
        self.last_recipe_for_update = None
        self.typing_indicator_message = None
        
        window_width = 400
        window_height = 650
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.minsize(400, 650)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        
        self.header = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="#007AFF")
        self.header.grid(row=0, column=0, sticky="nsew")
        self.header.grid_propagate(False)

        self.back_btn = ctk.CTkButton(self.header, text="←", width=35, height=35,
                                      fg_color="transparent", hover_color="#0066CC",
                                      font=("Helvetica", 22, "bold"), text_color="white", command=self.voltar)
        self.back_btn.pack(side="left", padx=(10,5), pady=7.5)

        self.title_label = ctk.CTkLabel(self.header, text="Geli",
                                        font=("Helvetica", 20, "bold"), text_color="white")
        self.title_label.pack(side="left", padx=(5,0), pady=10)

        self.chat_frame = ctk.CTkScrollableFrame(self, fg_color="#F0F0F0")
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.chat_frame._scrollbar.configure(height=0) # Oculta a scrollbar horizontal se não for necessária

        self.typing_indicator_message = None

        self.data_atual = datetime.now().strftime("%d/%m/%Y")
        self.date_label = ctk.CTkLabel(self.chat_frame, text=f"Hoje, {self.data_atual}",
                                       text_color="#666666", font=("Helvetica", 12))
        self.date_label.pack(pady=(10,5))

        self.input_frame = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
        self.input_frame.grid(row=2, column=0, sticky="nsew")

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Digite sua mensagem...",
                                  font=("Helvetica", 14), border_width=0, corner_radius=20,
                                  fg_color="#F0F0F0", placeholder_text_color="#888888")
        self.entry.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", self.enviar_mensagem_event)

        self.send_btn = ctk.CTkButton(self.input_frame, text="➤", width=45, height=45,
                                      font=("Arial", 20), corner_radius=20,
                                      fg_color="#007AFF", hover_color="#0066CC",
                                      command=self.enviar_mensagem)
        self.send_btn.pack(side="right", padx=(0, 10), pady=10)
        
        # Mensagem inicial
        if self.chat_service.gemini_api.is_configured():
            self.add_message("Olá! Sou Geli, seu assistente de culinária [...]. Como posso te ajudar hoje?", "bot")
        else:
            self.add_message("API não configurada. Verifique o console.", "bot_error")
            
    def add_message(self, text, sender):
        """Adiciona uma mensagem à interface do chat."""
        if self.typing_indicator_message and sender != "bot_typing":
            self.typing_indicator_message.destroy()
            self.typing_indicator_message = None

        msg_widget = ChatMessage(self.chat_frame, text, sender)

        if sender == "bot_typing":
            self.typing_indicator_message = msg_widget

        # Correção do Bug Visual: Força a atualização da janela principal (self)
        # para recalcular os layouts antes de rolar. Isso evita que o balão de
        # mensagem do usuário apareça "quebrado" temporariamente.
        self.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0) # Rola para o final
        
    def show_typing_indicator(self):
        """Mostra o indicador 'Geli está a escrever...'."""
        self.add_message("Geli está a escrever...", "bot_typing")
        
    def voltar(self):
        """Fecha a janela atual e tenta abrir gui1.py."""
        self.destroy()
        try:
            gui1_path = str(OUTPUT_PATH / "gui1.py") # Assume que gui1.py está no mesmo diretório
            subprocess.Popen([sys.executable, gui1_path])
        except FileNotFoundError:
            print(f"Erro: O arquivo '{gui1_path}' não foi encontrado.")
            # Poderia adicionar uma mensagem na UI se houvesse uma maneira de reabrir uma janela de erro.
            # Por enquanto, o print no console é o principal feedback.
        except Exception as e:
            print(f"Erro ao tentar abrir gui1.py: {e}")
            
    def enviar_mensagem_event(self, event):
        self.enviar_mensagem()

    def enviar_mensagem(self):
        msg = self.entry.get().strip()
        if not msg:
            return

        self.add_message(msg, "user")
        self.entry.delete(0, "end")

        palavras_confirmacao = ['sim', 's', 'pode', 'eu fiz', 'feito', 'preparei', 'fiz']
        
        # <-- MUDANÇA: Lógica de atualização de estoque simplificada
        if self.last_recipe_for_update and msg.lower() in palavras_confirmacao:
            print("LOG: Confirmação recebida! Chamando serviço para baixa de estoque.")
            self.after(10, self._execute_stock_update)
            return

        self.last_recipe_for_update = None
        self.show_typing_indicator()
        self.after(10, lambda: self.processar_resposta_bot(msg))

    def processar_resposta_bot(self, user_message):
        # <-- MUDANÇA RADICAL: A UI só chama o serviço e exibe a resposta
        
        # 1. Chama o serviço para obter a resposta da IA
        resposta_bot = self.chat_service.process_user_message(user_message)
        
        # 2. Mostra a resposta na tela
        self.add_message(resposta_bot, "bot")
        
        # 3. Pede ao serviço para salvar a receita, se for uma
        save_result = self.chat_service.save_recipe_if_detected(resposta_bot)
        if save_result and save_result["status"] == "success":
            self.add_message("Receita salva com sucesso!", "bot_info")
        elif save_result and save_result["status"] == "error":
            self.add_message(f"Falha ao salvar receita: {save_result['message']}", "bot_error")

        # 4. Prepara para a possível baixa de estoque
        ingredientes = self.chat_service.parse_ingredients_for_stock_update(resposta_bot)
        if ingredientes:
            self.last_recipe_for_update = {
                "titulo": save_result['title'] if save_result else "Receita Rápida",
                "ingredientes": ingredientes
            }
            print("LOG: Receita na memória. Aguardando 'sim' do usuário.")
        else:
            self.last_recipe_for_update = None

    def _execute_stock_update(self):
        # <-- MUDANÇA: A UI só chama o serviço
        if not self.last_recipe_for_update:
            return

        self.show_typing_indicator()
        
        # Chama o serviço em uma thread para não travar a UI
        def update_in_background():
            result = self.chat_service.execute_stock_update(
                self.last_recipe_for_update["titulo"],
                self.last_recipe_for_update["ingredientes"]
            )
            # Atualiza a UI na thread principal
            self.after(0, self.add_message, result["message"], "bot_info" if result["status"] == "success" else "bot_error")

        threading.Thread(target=update_in_background, daemon=True).start()
        self.last_recipe_for_update = None

# --- CAMINHOS DOS ARQUIVOS ---
OUTPUT_PATH = Path(__file__).parent
SETA_IMAGE_PATH = OUTPUT_PATH / "seta.png"
UP_ARROW_IMAGE_PATH = OUTPUT_PATH / "up_arrow.png"
DOWN_ARROW_IMAGE_PATH = OUTPUT_PATH / "down_arrow.png"
DEFAULT_ITEM_IMAGE_PATH = OUTPUT_PATH / "default.png"