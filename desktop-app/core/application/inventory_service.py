# Em core/application/inventory_service.py

from tkinter import messagebox

class InventoryService:
    """
    Serviço que contém toda a lógica de negócio para o gerenciamento de estoque.
    """
    def __init__(self, product_repo, gemini_api):
        self.product_repo = product_repo
        self.gemini_api = gemini_api
        self.local_stock_cache = {} # Cache em memória para evitar buscas repetidas no BD

    def get_stock(self, search_term=""):
        """Busca os produtos do banco e atualiza o cache local."""
        try:
            products = self.product_repo.get_all_products(search_term)
            self.local_stock_cache.clear()
            for product in products:
                self.local_stock_cache[product['nome_produto']] = product
            return list(self.local_stock_cache.values())
        except Exception as e:
            messagebox.showerror("Erro de Serviço", f"Falha ao carregar o estoque: {e}")
            return []
    
    def get_cached_item(self, item_name):
        """Retorna um item do cache local."""
        return self.local_stock_cache.get(item_name)

    def add_or_update_item(self, name, quantity, unit):
        """Adiciona um novo item ou atualiza a quantidade de um item existente."""
        try:
            name_capitalized = name.strip().capitalize()
            base_qty, base_unit = self._convert_to_base_units(quantity, unit)

            existing_item = self.product_repo.get_product_by_name(name_capitalized)

            if existing_item:
                if existing_item['tipo_volume'] != base_unit:
                    return {"status": "error", "message": f"Unidade incompatível. '{name_capitalized}' é medido em '{existing_item['tipo_volume']}'."}
                
                new_qty = float(existing_item['quantidade_produto']) + base_qty
                self.product_repo.update_product_quantity(name_capitalized, new_qty)
            else:
                nutritional_data = self.gemini_api.get_nutritional_info(name_capitalized)
                self.product_repo.add_new_product(name_capitalized, base_qty, base_unit, nutritional_data)

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao salvar item: {e}"}

    def remove_item_quantity(self, name, quantity, unit):
        """Remove uma quantidade específica de um item do estoque."""
        try:
            base_qty, base_unit = self._convert_to_base_units(quantity, unit)
            
            existing_item = self.product_repo.get_product_by_name(name)
            if not existing_item:
                return {"status": "error", "message": f"Item '{name}' não encontrado no estoque."}

            if existing_item['tipo_volume'] != base_unit:
                return {"status": "error", "message": f"Unidade incompatível. '{name}' é medido em '{existing_item['tipo_volume']}'."}

            if float(existing_item['quantidade_produto']) < base_qty:
                return {"status": "warning", "message": f"Quantidade insuficiente para remover de '{name}'."}

            new_qty = float(existing_item['quantidade_produto']) - base_qty
            if new_qty < 0.001: # Praticamente zero
                self.product_repo.delete_product(name)
            else:
                self.product_repo.update_product_quantity(name, new_qty)

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao remover item: {e}"}
    
    def execute_voice_command(self, text):
        """Interpreta e executa um comando de voz."""
        command = self.gemini_api.interpret_voice_command(text)
        if not command or "erro" in command:
            error_msg = command.get('erro', 'Comando não reconhecido.') if isinstance(command, dict) else 'Comando não reconhecido.'
            return {"status": "error", "message": error_msg}
        
        action = command['acao']
        if action == 'adicionar':
            result = self.add_or_update_item(command['item'], command['quantidade'], command['unidade'])
        elif action == 'remover':
            result = self.remove_item_quantity(command['item'], command['quantidade'], command['unidade'])
        else:
            return {"status": "error", "message": "Ação desconhecida."}

        # Retorna o resultado da operação e o comando interpretado para feedback na UI
        return {"status": result.get("status", "error"), "message": result.get("message"), "command": command}

    def get_low_stock_items(self):
        """Verifica o estoque e retorna uma lista de itens com baixa quantidade."""
        low_stock_items = []
        all_items = self.get_stock() # Garante que o cache está atualizado
        for item_data in all_items:
            try:
                numeric_qty = float(item_data["quantidade_produto"])
                unit = item_data["tipo_volume"]
                is_low = (unit == 'Unidades' and numeric_qty <= 2) or \
                         (unit == 'Gramas' and numeric_qty <= 500) or \
                         (unit == 'Mililitros' and numeric_qty <= 500)
                if is_low:
                    low_stock_items.append(item_data)
            except (ValueError, TypeError):
                continue
        return low_stock_items

    # --- Funções de Lógica de Negócio (privadas) ---
    def _convert_to_base_units(self, quantity, unit):
        """Converte Kg->g e L->ml para padronizar no banco."""
        unit_lower = unit.lower()
        quantity_float = float(str(quantity).replace(',', '.'))

        if 'kg' in unit_lower or 'quilos' in unit_lower:
            return (quantity_float * 1000, 'Gramas')
        elif 'l' in unit_lower or 'litros' in unit_lower:
            return (quantity_float * 1000, 'Mililitros')
        elif 'g' in unit_lower or 'gramas' in unit_lower:
            return (quantity_float, 'Gramas')
        elif 'ml' in unit_lower or 'mililitros' in unit_lower:
            return (quantity_float, 'Mililitros')
        elif 'unidades' in unit_lower:
            return (int(quantity_float), 'Unidades')
        return (quantity_float, unit) # Fallback

    def format_for_display(self, quantity, unit):
        """Converte g->Kg e ml->L para uma exibição amigável."""
        qtd_float = float(quantity)
        if unit == 'Gramas' and qtd_float >= 1000:
            return (f"{qtd_float / 1000:g}".replace('.', ','), "Kg")
        if unit == 'Mililitros' and qtd_float >= 1000:
            return (f"{qtd_float / 1000:g}".replace('.', ','), "L")
        return (f"{qtd_float:g}".replace('.', ','), unit)