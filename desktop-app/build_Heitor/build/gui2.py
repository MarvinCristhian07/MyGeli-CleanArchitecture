import tkinter as tk
from tkinter import ttk, font as tkFont, messagebox, simpledialog
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageTk
import os
import traceback
import re
import google.generativeai as genai
import threading
from gui0 import GOOGLE_API_KEY

# --- Constantes e Configurações ---
OUTPUT_PATH = Path(__file__).parent
RECIPE_FILE_PATH = OUTPUT_PATH / "latest_recipe.txt"
SAVED_RECIPES_DIR = OUTPUT_PATH / "saved_recipes"
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame2"
DOWNLOADS_BUILD_PATH = OUTPUT_PATH
FAVORITE_PREFIX = "★_"

"""Chamada do Gemini para gerar instruções nutricionais"""
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"AVISO: Não foi possível configurar a API do Gemini. A função de nutrição estará desabilitada. Erro: {e}")
    model = None

# --- Variáveis Globais da UI ---
recipe_buttons_canvas = None
recipe_buttons_inner_frame = None
window = None

# --- Funções Auxiliares ---
def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos e substitui espaços por underscores."""
    name = name.strip()
    # Remove o prefixo de favorito para sanitização, se existir
    if name.startswith(FAVORITE_PREFIX):
        name = name[len(FAVORITE_PREFIX):]
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    return name if name else "receita_sem_nome"

def extract_recipe_name_from_content(content: str) -> str:
    """Extrai o nome da receita da primeira linha não vazia."""
    lines = content.splitlines()
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:
            if stripped_line.lower().startswith("receita de:"):
                return stripped_line[len("receita de:"):].strip()
            if stripped_line.lower().startswith("nome:"):
                return stripped_line[len("nome:"):].strip()
            return stripped_line[:50] + "..." if len(stripped_line) > 53 else stripped_line
    return "Receita Sem Título"

def relative_to_assets(path: str, base_path: Path = ASSETS_PATH) -> Path:
    return base_path / Path(path)

def load_tk_image(filepath_obj: Path, size: tuple = None):
    """Carrega uma imagem usando Pillow e a converte para ImageTk.PhotoImage."""
    try:
        if not filepath_obj.exists():
            print(f"AVISO: Imagem não encontrada: {filepath_obj}")
            return None
        pil_image = Image.open(filepath_obj)
        if size:
            pil_image = pil_image.resize(size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
        return ImageTk.PhotoImage(pil_image)
    except Exception as e:
        print(f"ERRO ao carregar imagem '{filepath_obj}': {e}")
        return None

# --- Classe para Gerenciar o "Long Click" ---
class LongPressHandler:
    """Simula um evento de 'long press' para um widget, como em sistemas mobile."""
    def __init__(self, widget, menu, on_short_click_callback):
        self.widget = widget
        self.menu = menu
        self.on_short_click = on_short_click_callback
        self.timer_id = None
        self.long_press_fired = False

        self.widget.bind("<ButtonPress-1>", self.on_press)
        self.widget.bind("<ButtonRelease-1>", self.on_release)
        # Manter o clique direito para usabilidade no desktop
        self.widget.bind("<Button-3>", self.show_menu_directly)

    def on_press(self, event):
        """Inicia o temporizador quando o botão é pressionado."""
        self.long_press_fired = False
        # Agenda a chamada do long press para daqui a 500ms
        self.timer_id = self.widget.after(500, lambda: self.do_long_press(event))

    def on_release(self, event):
        """Cancela o temporizador ou executa o clique curto."""
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
        if not self.long_press_fired:
            self.on_short_click()

    def do_long_press(self, event):
        """Ação a ser executada no long press (mostrar menu)."""
        self.long_press_fired = True
        self.menu.post(event.x_root, event.y_root)

    def show_menu_directly(self, event):
        """Mostra o menu imediatamente com o clique direito."""
        self.menu.post(event.x_root, event.y_root)


# --- Funções de Gerenciamento de Receitas ---
def rename_recipe(recipe_filepath: Path, parent_app):
    """Renomeia o arquivo e o conteúdo da receita para manter a sincronia."""
    try:
        is_favorite = recipe_filepath.name.startswith(FAVORITE_PREFIX)
        current_name = recipe_filepath.stem.replace("_", " ")
        if is_favorite:
            current_name = current_name[len(FAVORITE_PREFIX):]

        new_name_str = simpledialog.askstring(
            "Renomear Receita",
            "Digite o novo nome para a receita:",
            initialvalue=current_name,
            parent=parent_app
        )

        if not new_name_str or not new_name_str.strip() or new_name_str.strip() == current_name:
            return

        new_name = new_name_str.strip()
        sanitized_new_name = sanitize_filename(new_name)
        if is_favorite:
            sanitized_new_name = FAVORITE_PREFIX + sanitized_new_name
        new_filepath = recipe_filepath.with_name(f"{sanitized_new_name}.txt")

        if new_filepath.exists() and new_filepath.resolve() != recipe_filepath.resolve():
            messagebox.showerror("Erro", "Já existe uma receita com esse nome.", parent=parent_app)
            return

        with open(recipe_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        found_title = False
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line:
                continue
            
            lower_line = stripped_line.lower()
            if lower_line.startswith("receita de:") or lower_line.startswith("nome:"):
                prefix_len = line.find(':') + 1
                prefix = line[:prefix_len]
                lines[i] = f"{prefix} {new_name}\n"
                found_title = True
                break
        
        if not found_title:
            for i, line in enumerate(lines):
                if line.strip():
                    lines[i] = f"{new_name}\n"
                    break
        
        modified_content = "".join(lines)
        os.rename(recipe_filepath, new_filepath)

        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        populate_recipe_buttons(parent_app)

    except Exception as e:
        messagebox.showerror("Erro ao Renomear", f"Ocorreu um erro inesperado: {e}", parent=parent_app)
        traceback.print_exc()

def delete_recipe(recipe_filepath: Path, parent_app):
    confirm = messagebox.askyesno(
        "Confirmar Exclusão",
        f"Tem certeza que deseja excluir a receita '{recipe_filepath.stem.replace('_', ' ')}'?\n\nEsta ação não pode ser desfeita.",
        parent=parent_app
    )
    if confirm:
        try:
            os.remove(recipe_filepath)
            main_app = parent_app
            while isinstance(main_app, tk.Toplevel):
                main_app = main_app.master
            populate_recipe_buttons(main_app)
        except Exception as e:
            messagebox.showerror("Erro ao Excluir", f"Ocorreu um erro: {e}", parent=parent_app)

def toggle_favorite_status(recipe_filepath: Path, parent_app):
    try:
        is_favorite = recipe_filepath.name.startswith(FAVORITE_PREFIX)
        new_name = recipe_filepath.name[len(FAVORITE_PREFIX):] if is_favorite else FAVORITE_PREFIX + recipe_filepath.name
        new_filepath = recipe_filepath.with_name(new_name)
        os.rename(recipe_filepath, new_filepath)
        populate_recipe_buttons(parent_app)
    except Exception as e:
        messagebox.showerror("Erro ao Favoritar", f"Ocorreu um erro: {e}", parent=parent_app)


# --- Funções da UI ---
def on_back_button_click():
    if window:
        window.destroy()
    try:
        subprocess.Popen([sys.executable, str(OUTPUT_PATH / "gui1.py")])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível voltar para a tela anterior: {e}", parent=window if window and window.winfo_exists() else None)

def on_search_button_click():
    if window:
        open_search_box(window)

def show_nutritional_info(recipe_content: str, parent_app: tk.Tk):
    """Função para buscar e exibir informações nutricionais da receita."""
    if not model:
        messagebox.showerror("API Não Configurada", "A chave de API para o Gemini não foi configurada corretamente. Verifique o console para mais detalhes.", parent=parent_app)
        return
        
    loading_window = tk.Toplevel(parent_app)
    loading_window.title("Aguarde")
    loading_window.geometry("300x120")
    loading_window.configure(bg="#FFFFFF")
    loading_window.protocol("WM_DELETE_WINDOW", lambda: None)
    parent_x, parent_y, w, h = parent_app.winfo_x(), parent_app.winfo_y(), parent_app.winfo_width(), parent_app.winfo_height()
    center_x, center_y = parent_x + (w // 2) - 150, parent_y + (h // 2) - 60
    loading_window.geometry(f"+{center_x}+{center_y}")
    loading_window.transient(parent_app)
    loading_window.grab_set()
    loading_window.attributes("-topmost", True)
    ttk.Label(loading_window, text="Gerando Instrução Nutricional...", font=parent_app.small_font, background="white").pack(pady=(15, 5))
    style = ttk.Style(loading_window)
    style.configure("Blue.Horizontal.TProgressbar", background='#0084FF')
    progress_bar = ttk.Progressbar(
        loading_window, 
        mode='indeterminate', 
        style="Blue.Horizontal.TProgressbar",
        length=250
    )
    progress_bar.pack(pady=10, padx=15)
    progress_bar.start(10)
    loading_window.update()

    def do_request():
        try:
            recipe_name_for_prompt = extract_recipe_name_from_content(recipe_content)
            prompt = (
                "Analise a seguinte receita e forneça uma estimativa nutricional por porção."
                "A resposta deve seguir esta estrutura EXATA, sem nenhuma palavra ou formatação adicional:\n\n"
                "Estimativa nutricional para:\n"
                "\{recipe_name_for_prompt}\:\n\n"
                "Calorias: [valor] kcal\n"
                "Proteínas: [valor] g\n"
                "Carboidratos: [valor] g\n"
                "Gorduras: [valor] g\n\n"
                "------------------------------------\n"
                "Lembre-se que estes são valores aproximados e podem variar. Para um acompanhamento preciso, consulte um nutricionista.\n"
                "RECEITA A SER ANALISADA:\n{recipe_content}"
        )
            response = model.generate_content(prompt)        
        except Exception as e:
            response = None
            error_message = "Ocorreu um erro ao consultar as informações nutricionais:\n{e}"
        
        def on_complete():
            progress_bar.stop()
            loading_window.destroy()
            if response:
                show_nutritional_result(response.text, parent_app)
            else:
                messagebox.showerror("Erro de API", error_message, parent=parent_app)
        parent_app.after(0, on_complete)
    threading.Thread(target=do_request, daemon=True).start()


def show_nutritional_result(result_text: str, parent_app: tk.Tk):
    # --- Configurações Iniciais da Janela ---
    result_window = tk.Toplevel(parent_app)
    result_window.title("Informações Nutricionais (Estimativa)")
    result_window.geometry("400x400")
    result_window.configure(bg="#F5F5F5")
    result_window.minsize(350, 300)
    parent_x, parent_y, w, h = parent_app.winfo_x(), parent_app.winfo_y(), parent_app.winfo_width(), parent_app.winfo_height()
    center_x, center_y = parent_x + (w // 2) - 200, parent_y + (h // 2) - 200
    result_window.geometry(f"+{center_x}+{center_y}")
    
    #Configuração do Layout com Grid
    result_window.grid_rowconfigure(1, weight=1)
    result_window.grid_columnconfigure(0, weight=1)

    #Toolbar Superior
    toolbar_frame = ttk.Frame(result_window, height=60, style="Toolbar.TFrame")
    toolbar_frame.grid(row=0, column=0, sticky="ew")
    toolbar_frame.grid_propagate(False)
    toolbar_frame.grid_columnconfigure(1, weight=1)

    # Botão de Voltar (Seta)
    back_arrow_img = load_tk_image(OUTPUT_PATH / "assets" / "geral" / "seta.png", size=(24, 24))
    back_btn = ttk.Button(
        toolbar_frame, 
        image=back_arrow_img if back_arrow_img else None, 
        text="<" if not back_arrow_img else "", 
        command=result_window.destroy, 
        style="Toolbar.TButton"
    )
    back_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    back_btn.image = back_arrow_img # Mantém referência à imagem

    # Título na Toolbar
    ttk.Label(
        toolbar_frame, 
        text="Informações Nutricionais", 
        style="Toolbar.TLabel"
    ).grid(row=0, column=1, pady=10, padx=10)


    #Área de Conteúdo Estilizada
    content_frame = ttk.Frame(result_window, padding="15", style="TFrame")
    content_frame.grid(row=1, column=0, sticky="nsew")
    info_label = ttk.Label(
        content_frame, 
        text=result_text,
        font=parent_app.small_font,
        wraplength=350,
        justify="left"
    )
    info_label.pack(expand=True, fill="both", anchor="nw")


    # --- CORREÇÃO DE FOCO ---
    result_window.attributes("-topmost", True)
    result_window.transient(parent_app)
    result_window.grab_set()
    parent_app.wait_window(result_window)

def display_selected_recipe(recipe_filepath: Path, parent_app):
    try:
        ICONS_PATH = OUTPUT_PATH / "assets" / "geral"

        def load_content(filepath):
            with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            return content, extract_recipe_name_from_content(content)
        
        original_recipe_content, recipe_name = load_content(recipe_filepath)
        current_filepath = recipe_filepath

        star_on_img = load_tk_image(ICONS_PATH / "favorito_on.png", size=(24, 24))
        star_off_img = load_tk_image(ICONS_PATH / "favorito_off.png", size=(24, 24))
        trash_img = load_tk_image(ICONS_PATH / "lixeira.png", size=(24, 24))
        nutri_img = load_tk_image(ICONS_PATH / "nutri.png", size=(24,24))


        # --- Criação e centralização da janela (lógica original) ---
        recipe_window = tk.Toplevel(parent_app)
        recipe_window.title(f"Receita: {recipe_name}")
        recipe_window.geometry("500x700")
        recipe_window.configure(bg="#FFFFFF")
        parent_x, parent_y, w, h = parent_app.winfo_x(), parent_app.winfo_y(), parent_app.winfo_width(), parent_app.winfo_height()
        center_x, center_y = parent_x + (w // 2) - 250, parent_y + (h // 2) - 315
        recipe_window.geometry(f"+{center_x}+{center_y}")
        recipe_window.attributes("-topmost", True)
        recipe_window.grid_rowconfigure(1, weight=1)
        recipe_window.grid_columnconfigure(0, weight=1)
        
        # --- UI: Cabeçalho com Título e Ícones ---
        header_frame = ttk.Frame(recipe_window, style="White.TFrame", padding=(10, 10, 10, 5))
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        recipe_title_label = ttk.Label(header_frame, text=recipe_name, font=parent_app.medium_font, background="white", anchor="w")
        recipe_title_label.grid(row=0, column=0, sticky="ew")
        #Botão de informações nutricionais
        nutri_button = ttk.Button(header_frame, image=nutri_img, text="[i]" if not nutri_img else "", command=lambda: show_nutritional_info(text_area.get("1.0", "end"), parent_app), style="Header.TButton")
        nutri_button.grid(row=0, column=1, sticky="e", padx=5)

        # --- UI: Área de Texto (lógica original) ---
        text_frame = ttk.Frame(recipe_window, padding="10", style="White.TFrame")
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_area = tk.Text(text_frame, wrap="word", font=parent_app.small_font, bg="#F0F0F0", relief="solid", borderwidth=1, padx=10, pady=10)
        text_area.insert("end", original_recipe_content)
        text_area.configure(state="disabled")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set); scrollbar.pack(side="right", fill="y"); text_area.pack(expand=True, fill="both")

        # --- UI: Rodapé com botões de ação ---
        button_frame = ttk.Frame(recipe_window, padding=(10, 5, 10, 10), style="White.TFrame")
        button_frame.grid(row=2, column=0, sticky="ew")

        # --- Funções internas de Lógica para os botões ---
        def toggle_edit_mode():
            if text_area.cget("state") == "disabled":
                text_area.configure(state="normal", bg="#FFFFFF"); text_area.focus_set()
                save_button.pack(side="left", expand=True, fill='x', padx=2)
                edit_button.configure(text="Cancelar")
                # CORREÇÃO: Esconde o frame usando grid
                header_frame.grid_remove()
                close_button.pack_forget()
            else:
                text_area.configure(state="disabled", bg="#F0F0F0")
                text_area.delete("1.0", "end"); text_area.insert("end", original_recipe_content)
                save_button.pack_forget()
                edit_button.configure(text="Editar")
                # CORREÇÃO: Mostra o frame de volta na sua posição original do grid
                header_frame.grid()
                close_button.pack(side="right", expand=True, fill='x', padx=2)
        
        def save_changes():
            nonlocal original_recipe_content, current_filepath
            new_content = text_area.get("1.0", "end-1c").strip()
            with open(current_filepath, "w", encoding="utf-8") as f: f.write(new_content)
            messagebox.showinfo("Sucesso", "Receita salva!", parent=recipe_window)
            populate_recipe_buttons(parent_app)
            toggle_edit_mode()

            def save_changes():
                nonlocal original_recipe_content, current_filepath
                new_content = text_area.get("1.0", "end-1c").strip()
                original_recipe_content = new_content # <--- ADICIONE ESTA LINHA
                with open(current_filepath, "w", encoding="utf-8") as f: f.write(new_content)
                messagebox.showinfo("Sucesso", "Receita salva!", parent=recipe_window)
                populate_recipe_buttons(parent_app)
                toggle_edit_mode()
                    
        def toggle_favorite_and_update():
            nonlocal current_filepath
            toggle_favorite_status(current_filepath, parent_app) 
            new_name = current_filepath.name[len(FAVORITE_PREFIX):] if current_filepath.name.startswith(FAVORITE_PREFIX) else FAVORITE_PREFIX + current_filepath.name
            current_filepath = current_filepath.with_name(new_name)
            update_favorite_button_state()

        def delete_and_close():
            delete_recipe(current_filepath, recipe_window) 
            if not current_filepath.exists(): recipe_window.destroy()

        def update_favorite_button_state():
            is_fav = current_filepath.name.startswith(FAVORITE_PREFIX)
            favorite_button.configure(image=star_on_img if is_fav else star_off_img)
        
        # --- Estilos e Botões ---
        style = ttk.Style(recipe_window)
        style.configure("White.TFrame", background="white")
        style.configure("Header.TButton", background="white", borderwidth=0, relief="flat")
        style.map("Header.TButton", background=[('active', '#F0F0F0')])
        
        favorite_button = ttk.Button(header_frame, image=star_off_img, command=toggle_favorite_and_update, style="Header.TButton")
        favorite_button.grid(row=0, column=2, sticky="e", padx=5)
        delete_button = ttk.Button(header_frame, image=trash_img, command=delete_and_close, style="Header.TButton")
        delete_button.grid(row=0, column=3, sticky="e")
        
        save_button = ttk.Button(button_frame, text="Salvar Alterações", command=save_changes, style="Accent.TButton")
        edit_button = ttk.Button(button_frame, text="Editar", command=toggle_edit_mode)
        close_button = ttk.Button(button_frame, text="Voltar", command=recipe_window.destroy, style="Red.TButton")
        
        edit_button.pack(side="left", expand=True, fill='x', padx=2)
        close_button.pack(side="right", expand=True, fill='x', padx=2)
        
        update_favorite_button_state()
        recipe_window.transient(parent_app); recipe_window.grab_set(); parent_app.wait_window(recipe_window)

    except Exception as e:
        messagebox.showerror("Erro ao Exibir Receita", f"Não foi possível carregar a receita:\n{e}", parent=parent_app)
        traceback.print_exc()

def _on_mousewheel(event, canvas):
    if sys.platform == "win32":
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    elif sys.platform == "darwin":
        canvas.yview_scroll(int(-1 * event.delta), "units")
    else: # Linux
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

def populate_recipe_buttons(parent_app):
    """Limpa e recria os botões de receita, adicionando funcionalidades de gerenciamento."""
    global recipe_buttons_inner_frame, recipe_buttons_canvas
    
    if not recipe_buttons_inner_frame or not recipe_buttons_canvas:
        print("Erro: Frame interno ou canvas não inicializado.")
        return

    for widget in recipe_buttons_inner_frame.winfo_children():
        widget.destroy()

    SAVED_RECIPES_DIR.mkdir(parents=True, exist_ok=True)
            
    recipe_files = sorted(
        [f for f in SAVED_RECIPES_DIR.iterdir() if f.is_file() and f.suffix == '.txt'], 
        key=lambda f: (not f.name.startswith(FAVORITE_PREFIX), f.name.lower())
    )

    if not recipe_files:
        ttk.Label(recipe_buttons_inner_frame, text="Nenhuma receita salva ainda.", 
                  font=parent_app.small_font, foreground="#666666", padding=20, justify="center").pack(pady=20)
    else:
        for recipe_file_path in recipe_files:
            try:
                is_favorite = recipe_file_path.name.startswith(FAVORITE_PREFIX)
                
                with open(recipe_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                recipe_name_for_button = extract_recipe_name_from_content(content)
                if not recipe_name_for_button or recipe_name_for_button == "Receita Sem Título":
                    clean_name = recipe_file_path.stem[len(FAVORITE_PREFIX):] if is_favorite else recipe_file_path.stem
                    recipe_name_for_button = clean_name.replace("_", " ")

                display_text = f"★ {recipe_name_for_button}" if is_favorite else recipe_name_for_button
                button_style = "Favorite.Recipe.TButton" if is_favorite else "Recipe.TButton"

                btn = ttk.Button(
                    recipe_buttons_inner_frame,
                    text=display_text,
                    style=button_style
                )
                btn.pack(pady=(5,0), padx=10, fill="x")

                menu = tk.Menu(parent_app, tearoff=0)
                menu.add_command(label="Renomear", command=lambda p=recipe_file_path: rename_recipe(p, parent_app))
                
                fav_label = "Desfavoritar" if is_favorite else "Favoritar"
                menu.add_command(label=fav_label, command=lambda p=recipe_file_path: toggle_favorite_status(p, parent_app))
                
                menu.add_separator()
                menu.add_command(label="Excluir", command=lambda p=recipe_file_path: delete_recipe(p, parent_app))

                short_click_action = lambda p=recipe_file_path: display_selected_recipe(p, parent_app)
                
                LongPressHandler(widget=btn, menu=menu, on_short_click_callback=short_click_action)

            except Exception as e:
                print(f"Erro ao processar {recipe_file_path.name}: {e}")
                error_label = ttk.Label(
                    recipe_buttons_inner_frame, text=f"Erro ao carregar: {recipe_file_path.name}",
                    font=parent_app.small_font, foreground="red"
                )
                error_label.pack(pady=2, padx=10, fill="x")
    
    recipe_buttons_inner_frame.update_idletasks()
    recipe_buttons_canvas.configure(scrollregion=recipe_buttons_canvas.bbox("all"))

def auto_process_latest_recipe():
    """Processa a última receita de `latest_recipe.txt`."""
    if not RECIPE_FILE_PATH.exists():
        return False

    processed_new_recipe = False
    try:
        with open(RECIPE_FILE_PATH, "r", encoding="utf-8") as f:
            recipe_content = f.read().strip()

        if not recipe_content:
            RECIPE_FILE_PATH.unlink(missing_ok=True)
            return False
            
        recipe_name = extract_recipe_name_from_content(recipe_content)
        safe_filename_base = sanitize_filename(recipe_name if recipe_name != "Receita Sem Título" else "receita_importada")
        
        counter = 0
        final_filename = f"{safe_filename_base}.txt"
        full_save_path = SAVED_RECIPES_DIR / final_filename
        
        SAVED_RECIPES_DIR.mkdir(parents=True, exist_ok=True)

        while full_save_path.exists():
            try:
                with open(full_save_path, "r", encoding="utf-8") as existing_f:
                    if existing_f.read().strip() == recipe_content:
                        RECIPE_FILE_PATH.unlink(missing_ok=True)
                        return False
            except Exception:
                pass
            
            counter += 1
            final_filename = f"{safe_filename_base}_{counter}.txt"
            full_save_path = SAVED_RECIPES_DIR / final_filename

        with open(full_save_path, "w", encoding="utf-8") as f_save:
            f_save.write(recipe_content)
        
        processed_new_recipe = True
        
    except Exception as e:
        traceback.print_exc()
    finally:
        if RECIPE_FILE_PATH.exists():
            try:
                RECIPE_FILE_PATH.unlink(missing_ok=True)
            except Exception as e_unlink:
                print(f"Erro ao remover {RECIPE_FILE_PATH}: {e_unlink}")
    return processed_new_recipe

def open_search_box(parent_app):
    """Abre uma janela para pesquisar receitas localmente."""
    search_window = tk.Toplevel(parent_app)
    search_window.title("Pesquisar Receita (Local)")
    search_width, search_height = 300, 200
    search_window.geometry(f"{search_width}x{search_height}")
    search_window.configure(bg="#F0F0F0")
    search_window.attributes("-topmost", True)

    parent_x, parent_y = parent_app.winfo_x(), parent_app.winfo_y()
    parent_width, parent_height = parent_app.winfo_width(), parent_app.winfo_height()
    center_x = parent_x + (parent_width // 2) - (search_width // 2)
    center_y = parent_y + (parent_height // 2) - (search_height // 2)
    search_window.geometry(f"+{center_x}+{center_y}")
    
    search_window.grid_columnconfigure(0, weight=1)

    ttk.Label(search_window, text="Pesquisar nas receitas salvas:", font=parent_app.medium_font, background="#F0F0F0").grid(row=0, column=0, pady=(15, 10), padx=10, sticky="w")
    
    search_entry = ttk.Entry(search_window, width=40, font=parent_app.small_font)
    search_entry.grid(row=1, column=0, pady=5, padx=10, sticky="ew")
    search_entry.focus_set()

    def perform_local_search_action():
        query = search_entry.get().lower().strip()
        if not query:
            messagebox.showinfo("Pesquisa", "Digite um termo para pesquisar.", parent=search_window)
            return

        found_recipes = []
        search_window.destroy()

        if SAVED_RECIPES_DIR.exists():
            for recipe_file in SAVED_RECIPES_DIR.glob("*.txt"):
                try:
                    with open(recipe_file, "r", encoding="utf-8") as f:
                        if query in f.read().lower():
                            found_recipes.append(recipe_file)
                except Exception as e_file:
                    print(f"Erro ao ler {recipe_file.name}: {e_file}")
        
        if found_recipes:
            results_window = tk.Toplevel(parent_app)
            results_window.title(f"Resultados para: '{query}'")
            res_popup_width, res_popup_height = 400, 450
            results_window.geometry(f"{res_popup_width}x{res_popup_height}")
            results_window.configure(bg="#F5F5F5")
            results_window.attributes("-topmost", True)

            res_center_x = parent_x + (parent_width // 2) - (res_popup_width // 2)
            res_center_y = parent_y + (parent_height // 2) - (res_popup_height // 2)
            results_window.geometry(f"+{res_center_x}+{res_center_y}")

            ttk.Label(results_window, text=f"Receitas encontradas para '{query}':", font=parent_app.medium_font, background="#F5F5F5").pack(pady=10, padx=10, anchor="w")
            
            res_list_container = ttk.Frame(results_window)
            res_list_container.pack(fill="both", expand=True, padx=10, pady=(0,10))
            res_list_container.grid_rowconfigure(0, weight=1)
            res_list_container.grid_columnconfigure(0, weight=1)

            res_canvas = tk.Canvas(res_list_container, bg="#FFFFFF", highlightthickness=0)
            res_scrollbar = ttk.Scrollbar(res_list_container, orient="vertical", command=res_canvas.yview)
            res_scrollable_frame = ttk.Frame(res_canvas)

            res_scrollable_frame.bind("<Configure>", lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
            res_canvas_frame_id = res_canvas.create_window((0, 0), window=res_scrollable_frame, anchor="nw")
            res_canvas.configure(yscrollcommand=res_scrollbar.set)
            
            res_canvas.grid(row=0, column=0, sticky="nsew")
            res_scrollbar.grid(row=0, column=1, sticky="ns")
            res_canvas.bind("<Configure>", lambda e: res_canvas.itemconfig(res_canvas_frame_id, width=e.width))
            
            res_canvas.bind_all("<MouseWheel>", lambda ev: _on_mousewheel(ev, res_canvas))
            res_canvas.bind_all("<Button-4>", lambda ev: _on_mousewheel(ev, res_canvas))
            res_canvas.bind_all("<Button-5>", lambda ev: _on_mousewheel(ev, res_canvas))

            for rec_path in found_recipes:
                with open(rec_path, "r", encoding="utf-8") as f_rec:
                    rec_name = extract_recipe_name_from_content(f_rec.read())
                    if not rec_name or rec_name == "Receita Sem Título": 
                        rec_name = rec_path.stem.replace("_", " ")
                ttk.Button(res_scrollable_frame, text=rec_name, style="ResultItem.TButton", 
                            command=lambda p=rec_path: display_selected_recipe(p, parent_app)
                            ).pack(fill="x", pady=(2,0), padx=5)
            
            ttk.Button(results_window, text="Fechar Resultados", command=results_window.destroy, style="Accent.TButton").pack(pady=10)
            
            results_window.transient(parent_app)
            results_window.grab_set()
            parent_app.wait_window(results_window)
        else: 
            messagebox.showinfo("Pesquisa", f"Nenhuma receita encontrada contendo '{query}'.", parent=parent_app)

    search_button_widget = ttk.Button(search_window, text="Pesquisar", command=perform_local_search_action, style="Accent.TButton")
    search_button_widget.grid(row=2, column=0, pady=10, padx=10, sticky="ew")
    search_window.bind('<Return>', lambda event: perform_local_search_action())
    
    search_window.transient(parent_app)
    search_window.grab_set()
    parent_app.wait_window(search_window)

# --- Configuração da Janela Principal ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        global window, recipe_buttons_canvas, recipe_buttons_inner_frame
        window = self 

        self.title("MyGeli - Minhas Receitas")
        main_width, main_height = 400, 650
        self.geometry(f"{main_width}x{main_height}")
        self.minsize(main_width, main_height)
        self.configure(bg="#F5F5F5")

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        center_x = int(screen_width/2 - main_width / 2)
        center_y = int(screen_height/2 - main_height / 2)
        self.geometry(f"+{center_x}+{center_y}")

        try:
            self.large_font = tkFont.Font(family="Poppins", size=28, weight="bold")
            self.medium_font = tkFont.Font(family="Poppins", size=18)
            self.small_font = tkFont.Font(family="Poppins", size=14)
            self.button_font = tkFont.Font(family="Poppins", size=16, weight="bold")
            self.favorite_font = tkFont.Font(family="Poppins", size=18, weight="bold")
        except tk.TclError:
            self.large_font = tkFont.Font(family="Arial", size=28, weight="bold")
            self.medium_font = tkFont.Font(family="Arial", size=18)
            self.small_font = tkFont.Font(family="Arial", size=14)
            self.button_font = tkFont.Font(family="Arial", size=16, weight="bold")
            self.favorite_font = tkFont.Font(family="Arial", size=18, weight="bold")
        
        style = ttk.Style(self)
        style.theme_use('clam')

        style.configure("TFrame", background="#F5F5F5")
        style.configure("Toolbar.TFrame", background="#0084FF")
        style.configure("Scrollable.TFrame", background="#FFFFFF")
        style.configure("TLabel", background="#F5F5F5", foreground="#333333", font=self.small_font)
        style.configure("Toolbar.TLabel", background="#0084FF", foreground="white", font=self.medium_font)
        style.configure("TButton", font=self.button_font, padding=5)
        style.configure("Accent.TButton", background="#0084FF", foreground="white", font=self.button_font)
        style.map("Accent.TButton", background=[('active', '#0066CC')])
        style.configure("Toolbar.TButton", font=self.button_font, background="#0084FF", foreground="white", relief="flat")
        style.map("Toolbar.TButton", background=[('active', '#0066CC')])
        
        style.configure("Recipe.TButton", font=self.medium_font, background="#FFFFFF", foreground="#333333", borderwidth=1, relief="solid", padding=(10,15)) 
        style.map("Recipe.TButton", background=[('active', '#F0F0F0')])

        style.configure("Favorite.Recipe.TButton", font=self.favorite_font, background="#FFFFE0", foreground="#4C4C00", borderwidth=1, relief="solid", padding=(10,15))
        style.map("Favorite.Recipe.TButton", background=[('active', '#FDFDAB')])

        style.configure("ResultItem.TButton", font=self.small_font, background="#E0E0E0", foreground="#333333", padding=5)
        style.map("ResultItem.TButton", background=[('active', '#CCCCCC')])
        style.configure("Red.TButton", foreground="white", background="#E74C3C", font=self.button_font, padding=5)
        style.map("Red.TButton", background=[('active', '#C0392B')])

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        toolbar_frame = ttk.Frame(self, height=60, style="Toolbar.TFrame")
        toolbar_frame.grid(row=0, column=0, sticky="new")
        toolbar_frame.grid_propagate(False)
        toolbar_frame.grid_columnconfigure(1, weight=1)

        self.back_button_image_tk = load_tk_image(OUTPUT_PATH / "assets" / "geral" / "seta.png", size=(24, 24))
        self.search_button_image_tk = load_tk_image(OUTPUT_PATH / "assets" / "geral" / "lupa.png", size=(24, 24))

        back_btn = ttk.Button(toolbar_frame, image=self.back_button_image_tk if self.back_button_image_tk else None, text="<" if not self.back_button_image_tk else "", command=on_back_button_click, style="Toolbar.TButton")
        back_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        ttk.Label(toolbar_frame, text="Minhas Receitas", style="Toolbar.TLabel").grid(row=0, column=1, pady=10, padx=10)

        search_btn_widget = ttk.Button(toolbar_frame, image=self.search_button_image_tk if self.search_button_image_tk else None, text="?" if not self.search_button_image_tk else "", command=on_search_button_click, style="Toolbar.TButton")
        search_btn_widget.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        list_container = ttk.Frame(self, style="TFrame", padding="20")
        list_container.grid(row=1, column=0, sticky="nsew")
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        recipe_buttons_canvas = tk.Canvas(list_container, bg="#FFFFFF", highlightthickness=0)
        recipe_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=recipe_buttons_canvas.yview)
        recipe_buttons_inner_frame = ttk.Frame(recipe_buttons_canvas, style="Scrollable.TFrame") 

        inner_frame_id = recipe_buttons_canvas.create_window((0, 0), window=recipe_buttons_inner_frame, anchor="nw")
        recipe_buttons_inner_frame.bind("<Configure>", lambda e: recipe_buttons_canvas.configure(scrollregion=recipe_buttons_canvas.bbox("all")))
        recipe_buttons_canvas.bind("<Configure>", lambda e: recipe_buttons_canvas.itemconfig(inner_frame_id, width=e.width))
        recipe_buttons_canvas.configure(yscrollcommand=recipe_scrollbar.set)

        recipe_buttons_canvas.grid(row=0, column=0, sticky="nsew")
        recipe_scrollbar.grid(row=0, column=1, sticky="ns")
        
        recipe_buttons_canvas.bind("<Enter>", lambda e: self.bind_all("<MouseWheel>", lambda ev: _on_mousewheel(ev, recipe_buttons_canvas)))
        recipe_buttons_canvas.bind("<Leave>", lambda e: self.unbind_all("<MouseWheel>"))
        recipe_buttons_canvas.bind("<Enter>", lambda e: self.bind_all("<Button-4>", lambda ev: _on_mousewheel(ev, recipe_buttons_canvas)))
        recipe_buttons_canvas.bind("<Leave>", lambda e: self.unbind_all("<Button-4>"))
        recipe_buttons_canvas.bind("<Enter>", lambda e: self.bind_all("<Button-5>", lambda ev: _on_mousewheel(ev, recipe_buttons_canvas)))
        recipe_buttons_canvas.bind("<Leave>", lambda e: self.unbind_all("<Button-5>"))

        if auto_process_latest_recipe():
            print("Nova receita processada e adicionada.")
        
        populate_recipe_buttons(self) 

        self.protocol("WM_DELETE_WINDOW", self._on_closing) 

    def _on_closing(self):
        self.destroy()

# --- Execução da Aplicação ---
if __name__ == "__main__":
    SAVED_RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    app = App()
    app.mainloop()
