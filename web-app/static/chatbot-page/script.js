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
      // Quando o carregamento chega a 100%
      // 1. Esconde o preloader com uma transição suave
      loaderWrapper.classList.add('hidden');
     
      // 2. Mostra o conteúdo da página com uma transição suave
      document.body.classList.add('loaded');
    }
  }

  // Inicia a animação quando o DOM estiver completamente carregado
  updateProgress();
 
  // ----------------------------------------------------- //
  const chatsContainer = document.querySelector(".chats-container");
  const promptForm = document.querySelector(".prompt-form");
  const promptInput = document.querySelector(".prompt-input");
 
  let userMessage = "";
 
  const createMsgElement = (content, ...classNames) => {
    const div = document.createElement("div");
    div.classList.add("message", ...classNames);
    div.innerHTML = content;
    return div;
  }
 
  const handleFormSubmit = (e) => {
    e.preventDefault();
    userMessage = promptInput.value.trim();
    if (!userMessage) return;
   
    promptInput.value = "";
   
    const userMsgHTML = `<p class="message-text"></p>`;
    const userMsgDiv = createMsgElement(userMsgHTML, "user-message");
   
    userMsgDiv.querySelector(".message-text").textContent = userMessage;
    chatsContainer.appendChild(userMsgDiv);
   
    setTimeout(() => {
      const botMsgHTML = `<img src="https://raw.githubusercontent.com/FoodYze/MyGeli/refs/heads/main/App/build_Heitor/build/assets/frame1/geli_icon.png" alt="Imagem da Geli" class="avatar">Just a sec...<p class="message-text"></p>`;
      const botMsgDiv = createMsgElement(botMsgHTML, "bot-message", "loading");
      chatsContainer.appendChild(botMsgDiv);
      generateResponse();
    }, 600);
  }
 
  promptForm.addEventListener("submit", handleFormSubmit);
});