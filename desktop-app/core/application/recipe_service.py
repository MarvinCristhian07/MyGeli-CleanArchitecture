# Em core/application/recipe_service.py

import re
from tkinter import messagebox

class RecipeService:
    """
    Serviço que contém toda a lógica de negócio para o gerenciamento de receitas.
    """
    def __init__(self, recipe_repo, file_repo, product_repo, gemini_api):
        self.recipe_repo = recipe_repo
        self.file_repo = file_repo
        self.product_repo = product_repo
        self.gemini_api = gemini_api

    # --- Funções de Leitura ---
    def get_all_recipes(self):
        """Busca todas as receitas dos arquivos .txt."""
        return self.file_repo.get_all_recipes_from_files()

    def get_recipe_content(self, recipe_path):
        """Lê o conteúdo de um arquivo de receita específico."""
        return self.file_repo.read_recipe_file(recipe_path)

    # --- Funções de Escrita/Modificação ---
    def rename_recipe(self, old_path, new_name):
        """Renomeia uma receita tanto no arquivo quanto no banco de dados."""
        # Renomeia o arquivo
        new_path = self.file_repo.rename_recipe(old_path, new_name)
        if not new_path:
            return None # Retorna None se o renomeio do arquivo falhou

        # Atualiza o título no banco de dados
        old_title = self.file_repo.extract_recipe_name_from_path(old_path)
        self.recipe_repo.update_recipe_title(old_title, new_name)
        return new_path

    def delete_recipe(self, recipe_path):
        """Deleta uma receita do arquivo e do banco de dados."""
        title_to_delete = self.file_repo.extract_recipe_name_from_path(recipe_path)
        
        # Deleta do banco de dados primeiro
        self.recipe_repo.delete_recipe_by_title(title_to_delete)
        
        # Deleta o arquivo
        self.file_repo.delete_recipe_file(recipe_path)

    def toggle_favorite(self, recipe_path):
        """Adiciona ou remove o status de favorito de uma receita."""
        return self.file_repo.toggle_favorite(recipe_path)

    def save_edited_recipe(self, recipe_path, new_content):
        """Salva o conteúdo editado de uma receita no arquivo e no banco."""
        old_title = self.file_repo.extract_recipe_name_from_path(recipe_path)
        new_title = self.file_repo.extract_recipe_name_from_content(new_content)
        
        # Salva o conteúdo no arquivo
        self.file_repo.write_recipe_file(recipe_path, new_content)

        # Atualiza o conteúdo e possivelmente o título no banco
        self.recipe_repo.update_recipe_content(old_title, new_title, new_content)

    # --- Funções de Lógica de Negócio ---
    def consume_recipe_ingredients(self, recipe_content):
        """Processa a baixa de ingredientes do estoque."""
        recipe_title = self.file_repo.extract_recipe_name_from_content(recipe_content)
        ingredients = self._parse_all_ingredients(recipe_content)

        if not ingredients:
            return {"status": "warning", "message": "Não foi possível encontrar ingredientes formatados nesta receita."}

        success_list = []
        failure_list = []

        for item in ingredients:
            try:
                # Tenta dar baixa no estoque
                updated_rows = self.product_repo.update_product_quantity_by_name(item['nome'], -item['quantidade'])
                
                if updated_rows > 0:
                    success_list.append(item['nome'])
                    # Adiciona ao histórico
                    self.product_repo.add_history_entry(recipe_title, item['nome'], item['quantidade'], item['unidade'])
                else:
                    failure_list.append(item['nome'])
            except Exception as e:
                print(f"Erro ao dar baixa no item {item['nome']}: {e}")
                failure_list.append(item['nome'])
        
        return {"success": success_list, "failure": failure_list}


    def _parse_all_ingredients(self, recipe_text):
        """Lógica para extrair TODOS os ingredientes de um texto de receita."""
        try:
            ingredients_block = recipe_text.split("INGREDIENTES:")[1].split("PREPARO:")[0]
        except IndexError:
            return []

        parsed_ingredients = []
        for line in ingredients_block.splitlines():
            if not line.strip(): continue
            
            cleaned_line = re.sub(r'\s*\(do estoque\)', '', line, flags=re.IGNORECASE).strip()
            match = re.match(r"^\s*([\d\.,]+)\s*(\w*)\s*(?:de\s)?(.*)", cleaned_line, re.IGNORECASE)
            
            if match:
                try:
                    qty = float(match.group(1).replace(',', '.'))
                    unit = match.group(2).strip()
                    name = match.group(3).strip()
                    if not name: name, unit = unit, "unidade(s)"
                    if name.lower().startswith('de '): name = name[3:]
                    
                    parsed_ingredients.append({"nome": name.strip(), "quantidade": qty, "unidade": unit})
                except (ValueError, IndexError):
                    continue
        return parsed_ingredients

    def get_nutritional_info(self, recipe_content):
        """Pede à API Gemini para gerar informações nutricionais."""
        if not self.gemini_api or not self.gemini_api.is_configured():
            return "API não configurada."
        
        recipe_name = self.file_repo.extract_recipe_name_from_content(recipe_content)
        # Este prompt pode ser movido para o prompts.py também
        prompt = (f"Analise a seguinte receita e forneça uma estimativa nutricional por porção. "
                  f"Formate a resposta de forma clara e amigável para um usuário final.\n\n"
                  f"RECEITA:\n{recipe_content}")
        
        return self.gemini_api.generate_chat_response(prompt) # Reutiliza o método de chat para uma resposta simples