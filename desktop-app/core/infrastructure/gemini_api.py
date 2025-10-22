# Em core/infrastructure/gemini_api.py

import os
import google.generativeai as genai
import traceback
import json
from dotenv import load_dotenv

# Importa as variáveis de prompt do nosso novo arquivo
from . import prompts

# Carrega as variáveis de ambiente (como a GOOGLE_API_KEY do arquivo .env)
load_dotenv()

class GeminiAPI:
    """
    Classe central para gerenciar todas as interações com a Google Gemini API.
    """
    def __init__(self):
        """
        Configura a API e inicializa o modelo na criação da instância.
        """
        self.model = None
        self.chat_session = None
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print("ERRO CRÍTICO: A variável de ambiente GOOGLE_API_KEY não foi encontrada.")
                return

            genai.configure(api_key=api_key)
            
            # AGORA USAMOS A VARIÁVEL IMPORTADA!
            self.model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=prompts.SYSTEM_INSTRUCTION_CHAT)
            self.chat_session = self.model.start_chat(history=[])
            print("Log: Módulo GeminiAPI inicializado com sucesso.")

        except Exception as e:
            print(f"Erro ao inicializar o GeminiAPI: {e}")
            traceback.print_exc()

    def is_configured(self):
        """Verifica se o modelo foi carregado corretamente."""
        return self.model is not None and self.chat_session is not None

    def generate_chat_response(self, user_message_with_context):
        """
        Gera uma resposta de chat para a Geli (lógica de gui0.py).
        """
        if not self.is_configured():
            return "Desculpe, a API de IA não está configurada corretamente."
        try:
            response = self.chat_session.send_message(user_message_with_context)
            return response.text
        except Exception as e:
            print(f"Erro ao chamar a API Gemini (send_message): {e}")
            traceback.print_exc()
            return "Desculpe, ocorreu um erro ao tentar obter uma resposta da IA."

    def get_nutritional_info(self, item_name):
        """
        Busca informações nutricionais de um alimento (lógica de gui3.py).
        """
        if not self.is_configured():
            return None
        try:
            model_nutri = genai.GenerativeModel('gemini-1.5-flash')
            # FORMATAMOS O PROMPT IMPORTADO COM O NOME DO ITEM
            prompt_text = prompts.PROMPT_NUTRITIONAL_INFO.format(item_name=item_name)
            response = model_nutri.generate_content(prompt_text)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_response)
        except Exception as e:
            print(f"Erro ao chamar a API Gemini para info nutricional: {e}")
            return None

    def interpret_voice_command(self, transcribed_text):
        """
        Interpreta um comando de voz transcrito e retorna um JSON (lógica de gui3.py).
        """
        if not self.is_configured():
            return {"erro": "API do Gemini não configurada."}
        try:
            model_comandos = genai.GenerativeModel('gemini-1.5-flash')
            # FORMATAMOS O PROMPT IMPORTADO COM O TEXTO TRANSCRITO
            prompt_text = prompts.PROMPT_VOICE_COMMAND.format(transcribed_text=transcribed_text)
            response = model_comandos.generate_content(prompt_text)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_response)
        except Exception as e:
            print(f"Erro ao processar comando de voz com Gemini: {e}")
            return {"erro": "Falha ao contatar a IA."}