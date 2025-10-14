# Em interfaces/gui_inventory.py

import customtkinter as ctk
from pathlib import Path
from PIL import Image
from tkinter import messagebox
import threading
import speech_recognition as sr

class App(ctk.CTk):
    def __init__(self, inventory_service, on_close_callback, open_history_callback):
        super().__init__()
        # Injeção de dependência: recebe os serviços e callbacks
        self.inventory_service = inventory_service
        self.on_close_callback = on_close_callback
        self.open_history_callback = open_history_callback
        
        # Estado da UI
        self.voice_feedback_window = None
        self.is_recording = False
        
        # --- O código de configuração da janela e fontes continua o mesmo ---
        # ... copie e cole as seções _configurar_janela e _criar_fontes aqui ...
        ctk.set_appearance_mode("light")
        self.title("Estoque")
        # ... (resto da configuração da janela)
        
        self.vcmd = (self.register(self._validate_numeric_input), '%P')
        self.recognizer = sr.Recognizer()
        
        self.measurement_units = ["Unidades", "Quilos (Kg)", "Gramas (g)", "Litros (L)", "Mililitros (ml)"]
        self.mass_units = ["Gramas (g)", "Quilos (Kg)"]
        self.volume_units = ["Mililitros (ml)", "Litros (L)"]
        self.unit_units = ["Unidades"]

        self._create_widgets()
        self.after(100, self.check_low_stock_on_startup)
        
        # Configura o fechamento da janela para chamar o callback
        self.protocol("WM_DELETE_WINDOW", self.on_close_callback)

    # A maior parte da sua lógica antiga foi movida para o InventoryService.
    # As funções da UI agora são muito mais simples.

    def _refresh_item_list(self, search_term=""):
        """Pede os itens ao serviço e atualiza a lista na tela."""
        # Limpa widgets antigos
        for widget in self.items_container.winfo_children():
            widget.destroy()
        
        # Pede os dados ao serviço
        stock_items = self.inventory_service.get_stock(search_term)
        
        if not stock_items:
            msg = "Nenhum item encontrado." if search_term else "Seu estoque está vazio."
            ctk.CTkLabel(self.items_container, text=msg, text_color="#666666").pack(pady=30)
        else:
            for i, item_data in enumerate(stock_items):
                self._add_item_widget(item_data, i)

    def _add_item_widget(self, item_data, row_index):
        """Cria o widget de um único item na lista."""
        # A lógica de cor de estoque baixo agora pode vir do serviço
        # Mas por ser puramente visual, pode ficar aqui também.
        item_color = "#0084FF"; text_color = "white"
        # (Lógica para mudar a cor se for estoque baixo)
        
        item_frame = ctk.CTkFrame(self.items_container, fg_color=item_color, corner_radius=12, height=60)
        item_frame.grid(row=row_index, column=0, sticky="ew", pady=5, padx=2)
        # ... (Resto da criação do widget do item, usando item_data['nome_produto'], etc.)
        # ... (A formatação de exibição agora usa o método do serviço)
        formatted_qtd, display_unit = self.inventory_service.format_for_display(item_data["quantidade_produto"], item_data["tipo_volume"])
        # ...
        
    def open_add_item_dialog(self):
        """Abre a janela para adicionar um item."""
        # A lógica do dialog continua aqui, pois é parte da UI.
        # No entanto, a ação de salvar chamará o serviço.
        # ...
        def _save_item_action():
            # ... (pega os dados dos campos de entrada) ...
            result = self.inventory_service.add_or_update_item(name, qty, unit)
            if result["status"] == "success":
                dialog.destroy()
                self._refresh_item_list()
            else:
                messagebox.showerror("Erro", result["message"], parent=dialog)
        # ...
        
    def open_remove_item_dialog(self):
        # A lógica do dialog de remoção também fica aqui.
        # A ação de remover chamará o serviço.
        # ...
        def _remove_item_action():
            # ... (pega os dados dos campos de entrada) ...
            result = self.inventory_service.remove_item_quantity(name, qty, unit)
            if result["status"] == "success":
                dialog.destroy()
                self._refresh_item_list()
            else:
                messagebox.showerror("Erro", result["message"], parent=dialog)
        # ...

    # --- Lógica de Comando de Voz (simplificada) ---
    def _start_recording(self, event):
        # A lógica de gravação do áudio (speech_recognition) permanece na UI
        # ... (código de _start_recording, _record_loop)
        pass # Substitua pelo seu código

    def _stop_recording_and_process(self, event):
        # Para a gravação e inicia o processamento em background
        # ... (código de _stop_recording_and_process)
        pass # Substitua pelo seu código

    def _process_audio_in_background(self):
        # Transcreve o áudio e envia o texto para o serviço
        try:
            # ... (código para obter 'texto' do áudio)
            texto = "exemplo de texto" # Substituir pela transcrição real
            
            # A UI não interpreta mais, ela apenas envia o texto para o serviço
            result = self.inventory_service.execute_voice_command(texto)
            
            # Atualiza a UI com base na resposta do serviço
            if result["status"] == "success":
                command = result["command"]
                msg_confirmacao = f"Entendido:\n{command['acao'].capitalize()} {command['quantidade']:g} {command['unidade']} de {command['item']}".replace('.',',')
                self.after(0, self._show_voice_feedback, msg_confirmacao)
                self.after(1500, self._refresh_item_list) # Atualiza a lista
                self.after(1500, self._close_voice_feedback)
            else:
                self.after(0, self._show_voice_feedback, f"Erro: {result['message']}")
                self.after(0, self._close_voice_feedback, 3000)
                
        except sr.UnknownValueError:
            self.after(0, self._show_voice_feedback, "Não entendi o que você disse.")
            self.after(0, self._close_voice_feedback)
        except Exception as e:
            self.after(0, self._show_voice_feedback, f"Erro no processamento: {e}")
            self.after(0, self._close_voice_feedback)
            
    # As demais funções (_validate_numeric_input, _center_dialog, _show_voice_feedback, etc.)
    # que são puramente para controle da UI, permanecem neste arquivo.