# Em core/application/shopping_list_service.py

from datetime import datetime

class ShoppingListService:
    """
    Serviço que contém a lógica de negócio para a lista de compras.
    """
    def __init__(self, file_repo, product_repo=None):
        # file_repo é para salvar a lista em .txt
        # product_repo e gemini_api seriam usados no futuro para gerar sugestões reais
        self.file_repo = file_repo
        self.product_repo = product_repo
        self.shopping_list = []

    def generate_suggested_list(self):
        """
        Gera uma lista de compras sugerida.
        ATUALMENTE: Retorna dados simulados, como no código original.
        FUTURO: Usaria a IA e o histórico de consumo (via product_repo) para gerar uma lista real.
        """
        # Simulação de dados para a interface
        self.shopping_list = [
            {"nome": "Leite", "quantidade": 2, "unidade": "Litros", "checked": False},
            {"nome": "Ovos", "quantidade": 12, "unidade": "Unidades", "checked": False},
            {"nome": "Farinha de Trigo", "quantidade": 1, "unidade": "Kg", "checked": False},
            {"nome": "Açúcar", "quantidade": 500, "unidade": "g", "checked": False},
            {"nome": "Frango", "quantidade": 1, "unidade": "Kg", "checked": False},
        ]
        return self.shopping_list

    def get_current_list(self):
        """Retorna a lista de compras atual em memória."""
        return self.shopping_list

    def add_item(self, name, quantity, unit):
        """Adiciona um novo item à lista de compras em memória."""
        new_item = {
            "nome": name,
            "quantidade": quantity,
            "unidade": unit,
            "checked": False
        }
        self.shopping_list.append(new_item)
        return new_item

    def remove_item(self, item_to_remove):
        """Remove um item da lista de compras em memória."""
        try:
            self.shopping_list.remove(item_to_remove)
            return True
        except ValueError:
            return False

    def remove_checked_items(self):
        """Remove todos os itens marcados (checked=True) da lista."""
        initial_count = len(self.shopping_list)
        self.shopping_list = [item for item in self.shopping_list if not item.get("checked")]
        return initial_count - len(self.shopping_list)

    def save_list_to_file(self):
        """Formata e salva a lista de compras atual em um arquivo de texto."""
        if not self.shopping_list:
            return {"status": "warning", "message": "A lista de compras está vazia. Nada para salvar."}

        # Formata o conteúdo do arquivo
        file_content = "=== LISTA DE COMPRAS SUGERIDA ===\n"
        file_content += f"Gerada em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        
        for index, product in enumerate(self.shopping_list, 1):
            file_content += f"{index}. {product['nome']} - {product['quantidade']} {product['unidade']}\n"
        
        file_content += f"\nTotal de itens: {len(self.shopping_list)}"

        try:
            # Usa o file_repo para salvar o arquivo
            file_path = self.file_repo.save_shopping_list(file_content)
            return {"status": "success", "path": file_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}