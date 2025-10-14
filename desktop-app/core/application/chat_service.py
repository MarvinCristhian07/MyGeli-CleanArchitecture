import re
from datetime import datetime

class ChatService:
    """
    Serviço que contém toda a lógica de negócio para o chat com a Geli.
    """
    def __init__(self, db_repo, recipe_repo, gemini_api, file_repo):
        self.db_repo = db_repo
        self.recipe_repo = recipe_repo
        self.gemini_api = gemini_api
        self.file_repo = file_repo

    def _get_chat_context(self):
        """Busca e formata o estoque e as receitas para enviar à IA."""
        # 1. Busca dados do estoque
        estoque = self.db_repo.get_all_products()
        if not estoque:
            estoque_formatado = "\n\nESTOQUE ATUAL: O estoque está vazio."
        else:
            header = "\n\nESTOQUE ATUAL (itens que você pode deve dar preferência para usar em casos de receitas sugeridas):\n"
            items_str_list = [f"= {item['nome_produto']}: {item['quantidade_produto']} {item['tipo_volume']}" for item in estoque]
            estoque_formatado = header + "\n".join(items_str_list)

        # 2. Busca títulos de receitas
        titulos = self.recipe_repo.get_all_recipe_titles()
        if not titulos:
            receitas_formatado = ""
        else:
            header = "\n\nRECEITAS JÁ CRIADAS (evite sugerir estas novamente):\n"
            items_str_list = [f"- {titulo}" for titulo in titulos]
            receitas_formatado = header + "\n".join(items_str_list)
            
        return f"{estoque_formatado}{receitas_formatado}"

    def process_user_message(self, user_message):
        """
        Processa a mensagem do usuário, adiciona contexto e obtém resposta da IA.
        """
        contexto = self._get_chat_context()
        mensagem_completa = f"{user_message}{contexto}"
        
        if self.gemini_api.is_configured():
            return self.gemini_api.generate_chat_response(mensagem_completa)
        else:
            return "Erro: A API de IA não está configurada."

    def _is_valid_recipe(self, bot_response):
        """Verifica se a resposta do bot é uma receita válida para ser salva."""
        lines = bot_response.splitlines()
        response_lower = bot_response.lower()
        if lines and lines[0].strip() and lines[0].strip().isupper() and 'ingredientes:' in response_lower and 'preparo:' in response_lower:
            return lines[0].strip() # Retorna o título da receita
        return None

    def save_recipe_if_detected(self, bot_response, user_id=1):
        """Salva a receita no banco e em arquivo .txt se for detectada."""
        recipe_title = self._is_valid_recipe(bot_response)
        if not recipe_title:
            return None

        try:
            # Salva no banco de dados
            self.recipe_repo.save_recipe(recipe_title, bot_response, user_id)
            
            # Salva em arquivo .txt
            self.file_repo.save_recipe_to_file(recipe_title, bot_response)
            
            print(f"SUCESSO: Receita '{recipe_title}' salva no banco e em arquivo.")
            return {"status": "success", "title": recipe_title}
        except Exception as e:
            print(f"ERRO no serviço ao salvar receita: {e}")
            return {"status": "error", "message": str(e)}

    def parse_ingredients_for_stock_update(self, recipe_text):
        """Extrai ingredientes marcados como '(do estoque)'."""
        pattern = re.compile(r"^\s*(.*?)\s+\(do estoque\)", re.MULTILINE | re.IGNORECASE)
        matches = pattern.findall(recipe_text)
        
        parsed = []
        for item_str in matches:
            match_comp = re.match(r"^\s*([\d\.,]+)\s*(\w*)\s*(?:de\s)?(.*)", item_str.strip(), re.IGNORECASE)
            if match_comp:
                try:
                    qty = float(match_comp.group(1).replace(',', '.'))
                    unit = match_comp.group(2).strip()
                    name = match_comp.group(3).strip()
                    if not name:
                        name, unit = unit, 'unidade(s)'
                    if name.lower().startswith('de '):
                        name = name[3:]
                    parsed.append({"nome": name, "quantidade": qty, "unidade": unit})
                except (ValueError, IndexError):
                    continue
        return parsed

    def execute_stock_update(self, recipe_title, ingredients):
        """Orquestra a atualização do estoque e do histórico."""
        try:
            for item in ingredients:
                self.db_repo.update_product_quantity_by_name(item['nome'], -item['quantidade']) # Usa valor negativo para subtrair
                self.db_repo.add_history_entry(recipe_title, item['nome'], item['quantidade'], item.get('unidade', ''))
            print("SUCESSO: Estoque e histórico atualizados.")
            return {"status": "success", "message": "Estoque e histórico atualizados com sucesso!"}
        except Exception as e:
            print(f"ERRO no serviço ao dar baixa no estoque: {e}")
            return {"status": "error", "message": str(e)}