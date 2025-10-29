document.addEventListener('DOMContentLoaded', () => {
  const loaderWrapper = document.getElementById('loader-wrapper');
  const progressBar = document.getElementById('progress-bar');
  const progressPercentage = document.getElementById('progress-percentage');
 
  let currentProgress = 0;
  const totalSteps = 100;
  const stepInterval = 20;

  function updateProgress() {
    if (currentProgress < 100) {
      currentProgress += Math.random() * 5 + 1;
      if (currentProgress > 100) {
        currentProgress = 100;
      }

      progressBar.style.width = currentProgress + '%';
      progressPercentage.textContent = Math.floor(currentProgress) + '%';
     
      setTimeout(updateProgress, stepInterval);
    } else {
      loaderWrapper.classList.add('hidden');
     
      document.body.classList.add('loaded');
    }
  }

  updateProgress();
 
  // ----------------------------------------------------- //
  const container = document.querySelector(".container");
  const chatsContainer = document.querySelector(".chats-container");
  const promptForm = document.querySelector(".prompt-form");
  const promptInput = document.querySelector(".prompt-input");
  const fileInput = document.querySelector("#file-input");
  const fileUploadWrapper = document.querySelector(".file-upload-wrapper");
  const themeToggle = document.querySelector("#theme-toggle-btn");
 
  const API_KEY = "AIzaSyAWdU1NiXHbiL7wnZSANHS-_VRu_odbg9I";
  const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${API_KEY}`;
 
  let typingInterval, controller;
  const chatHistory = [];
  const userData = { message: "", file: {} };
 
  const createMsgElement = (content, ...classNames) => {
    const div = document.createElement("div");
    div.classList.add("message", ...classNames);
    div.innerHTML = content;
    return div;
  };

  const scrollToBottom = () => container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });

  const typingEffect = (text, textElement, botMsgDiv) => {
    textElement.textContent = ""; // Começa com o texto vazio
    const words = text.split(" ");
    let wordIndex = 0;

    typingInterval = setInterval(() => {
      if(wordIndex < words.length) {
        // Durante a digitação, ainda usamos textContent
        textElement.textContent += (wordIndex === 0 ? "" : " ") + words[wordIndex++];
        scrollToBottom();
      } else {
        // --- MUDANÇA ACONTECE AQUI ---
        clearInterval(typingInterval);
        botMsgDiv.classList.remove("loading");
        document.body.classList.remove("bot-responding");

        // 1. Pega o texto puro final que foi digitado
        const rawText = textElement.textContent;
        
        // 2. Converte o Markdown (ex: #### Título) para HTML (ex: <h4>Título</h4>)
        // Usando a biblioteca 'marked' que importamos
        const dirtyHtml = marked.parse(rawText);
        
        // 3. LIMPA o HTML para previnir ataques de segurança (XSS)
        // Usando a biblioteca 'DOMPurify' que importamos
        const cleanHtml = DOMPurify.sanitize(dirtyHtml);
        
        // 4. Insere o HTML final, formatado e seguro, no balão de chat
        textElement.innerHTML = cleanHtml;
        // --- FIM DA MUDANÇA ---
      }
    }, 40);
  }
 
  // Substitua sua função generateResponse por esta:
  const generateResponse = async (botMsgDiv) => {
    const textElement = botMsgDiv.querySelector(".message-text");
    
    // --- CORREÇÃO 1: Inicializa o controller AQUI ---
    controller = new AbortController(); 
    
    // --- CORREÇÃO 2: Lógica de 'parts' simplificada (corrige o erro 'rest') ---
    const userParts = [{ text: userData.message }];
    if (userData.file && userData.file.data) {
        userParts.push({
            inline_data: {
                mime_type: userData.file.mime_type,
                data: userData.file.data // O prefixo base64 já foi removido no listener do fileInput
            }
        });
    }

    // Adiciona a mensagem completa (texto + imagem) ao histórico
    chatHistory.push({
      role: "user",
      parts: userParts
    });
    // --- FIM DAS CORREÇÕES ---
    
    try {
      // ATENÇÃO: MOVA ISSO PARA O SEU BACKEND FLASK!
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contents: chatHistory }),
        signal: controller.signal // Agora 'controller' está definido
      });
      // FIM DO AVISO

      const data = await response.json();
      
      if (!response.ok) {
        const errorMsg = data?.error?.message || `HTTP error! Status: ${response.status}`;
        throw new Error(errorMsg);
      }
      
      const candidate = data.candidates?.[0];
      const part = candidate?.content?.parts?.[0];
      const responseText = part?.text ? part.text.replace(/\*\*([^*]+)\*\*/g, "$1").trim() : "Desculpe, não consegui processar isso.";

      typingEffect(responseText, textElement, botMsgDiv);
      
      chatHistory.push({ role: "model", parts: [{ text: responseText }] });
    
    } catch (error) {
       textElement.style.color = "#d62939";
       textElement.textContent = error.name === "AbortError" ? "Geração de resposta parada." : error.message;
       botMsgDiv.classList.remove("loading");
       document.body.classList.remove("bot-responding");
    } finally {
       userData.file = {}; // Limpa o arquivo após o envio
    }
  }
 
  const handleFormSubmit = (e) => {
    e.preventDefault();
    const userMessage = promptInput.value.trim();
    if (!userMessage || document.body.classList.contains("bot-responding")) return;
   
    promptInput.value = "";
    userData.message = userMessage;
    document.body.classList.add("bot-responding", "chats-active");
    fileUploadWrapper.classList.remove("active", "img-attached", "file-attached");
   
    const userMsgHTML = `<p class="message-text"></p>
    ${userData.file.data ? (userData.file.isImage ? `<img src="data:${userData.file.mime_type};base64,${userData.file.data}" class="img-attachment" />` : `<p class="file-attachment"><span class="material-symbols-rounded">description</span>${userData.file.fileName}</p>`) : ""}`;
   
    const userMsgDiv = createMsgElement(userMsgHTML, "user-message");
    userMsgDiv.querySelector(".message-text").textContent = userMessage;
    chatsContainer.appendChild(userMsgDiv);
    scrollToBottom();
   
    setTimeout(() => {
      const botMsgHTML = `<img src="${GeliIconURL}" alt="Imagem da Geli" class="avatar"><p class="message-text">Pensando...</p>`;
      const botMsgDiv = createMsgElement(botMsgHTML, "bot-message", "loading");
      chatsContainer.appendChild(botMsgDiv);
      scrollToBottom();
      generateResponse(botMsgDiv);
    }, 600);
  }
 
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if(!file) return;
   
    const isImage= file.type.startsWith("image/");
    const reader = new FileReader();
    reader.readAsDataURL(file);
   
    reader.onload = (e) => {
      fileInput.value = "";
      const base64String = e.target.result.split(",")[1];
      fileUploadWrapper.querySelector(".file-preview").src = e.target.result;
      fileUploadWrapper.classList.add("active", isImage ? "img-attached" : "file-attached");
     
      userData.file = { fileName: file.name, data: base64String, mime_type: file.type, isImage };
    }
  });
 
  document.querySelector("#cancel-file-btn").addEventListener("click", () => {
    userData.file = {};
    fileUploadWrapper.classList.remove("active", "img-attached", "file-attached");
  });
 
  document.querySelector("#stop-response-btn").addEventListener("click", () => {
    userData.file = {};
    controller?.abort();
    clearInterval(typingInterval);
    chatsContainer.querySelector(".bot-message.loading").classList.remove("loading");
    document.body.classList.remove("bot-responding");
  });
 
  document.querySelector("#delete-chats-btn").addEventListener("click", () => {
    chatHistory.length = 0;
    chatsContainer.innerHTML = "";
    document.body.classList.remove("bot-responding", "chats-active");
  });
 
  document.querySelectorAll(".suggestion-item").forEach(item => {
    item.addEventListener("click", () => {
      promptInput.value = item.querySelector(".text").textContent;
      promptForm.dispatchEvent(new Event("submit"));
    });
  });
 
  document.addEventListener("click", ({ target }) => {
    const wrapper = document.querySelector(".prompt-wrapper");
    const shouldHide = target.classList.contains("prompt-input") || (wrapper.classList.contains("hide-controls") && (target.id === "add-file-btn" || target.id === "stop-response-btn"));
    wrapper.classList.toggle("hide-controls", shouldHide);
  })
 
  themeToggle.addEventListener("click", () => {
    const isLightTheme = document.body.classList.toggle("light-theme");
    localStorage.setItem("themeColor", isLightTheme ? "light_mode" : "dark_mode");
    themeToggle.textContent = isLightTheme ? "dark_mode" : "light_mode";
  });
 
  const isLightTheme = localStorage.getItem("themeColor") === "light_mode";
  document.body.classList.toggle("light-theme", isLightTheme);
  themeToggle.textContent = isLightTheme ? "dark_mode" : "light_mode";
 
  promptForm.addEventListener("submit", handleFormSubmit);
  promptForm.querySelector("#add-file-btn").addEventListener("click", () => fileInput.click());
});