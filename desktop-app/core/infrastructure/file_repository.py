import os
import re
from pathlib import Path
from datetime import datetime

class FileRepository:
    """
    Classe responsável por gerenciar todas as operações de arquivos de receitas.
    """
    def __init__(self, base_path="."):
        # Define o caminho base do projeto e a pasta de receitas salvas.
        # O ideal é que a pasta 'saved_recipes' esteja na raiz do projeto.
        self.saved_recipes_dir = Path(base_path) / "saved_recipes"
        
        # Garante que o diretório exista ao iniciar
        self.saved_recipes_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, name: str) -> str:
        """Limpa e formata uma string para ser usada como nome de arquivo."""
        name = name.strip().lower()
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'[^\w_.-]', '', name)
        return name[:100]

    def save_recipe_to_file(self, title: str, content: str):
        """
        Salva o conteúdo de uma receita em um arquivo .txt, garantindo um nome único.
        """
        if not title:
            title = "receita_sem_titulo"

        base_filename = self._sanitize_filename(title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{base_filename}_{timestamp}.txt"
        
        permanent_recipe_path = self.saved_recipes_dir / final_filename

        try:
            with open(permanent_recipe_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"DEBUG: Receita salva com sucesso em: {permanent_recipe_path.resolve()}")
            return str(permanent_recipe_path)
        except Exception as e:
            print(f"ERRO CRÍTICO ao salvar arquivo de receita: {e}")
            raise e # Lança o erro para a camada de serviço tratar

    # Você adicionará outros métodos aqui no futuro, como:
    # def get_all_recipes_from_files(self):
    # def delete_recipe_file(self, filename):
    # def rename_recipe_file(self, old_name, new_name):