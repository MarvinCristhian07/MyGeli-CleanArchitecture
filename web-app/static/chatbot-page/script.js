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
  
  const API_KEY = "AIzaSyAWdU1NiXHbiL7wnZSANHS-_VRu_odbg9I";
  const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${API_KEY}`;
 
  let userMessage = "";
  const chatHistory = [];
 
  const createMsgElement = (content, ...classNames) => {
    const div = document.createElement("div");
    div.classList.add("message", ...classNames);
    div.innerHTML = content;
    return div;
  }

  const scrollToBottom = () => container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });

  const typingEffect = (text, textElement, botMsgDiv) => {
    textElement.textContent = "";
    const words = text.split(" ");
    let wordIndex = 0;

    const typingInterval = setInterval(() => {
      if(wordIndex < words.length) {
        textElement.textContent += (wordIndex === 0 ? "" : " ") + words[wordIndex++];
        botMsgDiv.classList.remove("loading");
        scrollToBottom();
      } else {
        clearInterval(typingInterval);
      }
    }, 40);
  }
  
  const generateResponse = async (botMsgDiv) => {
    const textElement = botMsgDiv.querySelector(".message-text");
    
    chatHistory.push({
      role: "user",
      parts: [{ text: userMessage }]
    })
    
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contents: chatHistory })
      });
      
      const data = await response.json();
      if(!response.ok) throw new Error(data.error.message);
      
      const responseText = data.candidates[0].content.parts[0].text.replace(/\*\*([^*]+)\*\*/g, "$1").trim();
      typingEffect(responseText, textElement, botMsgDiv);
    } catch (error) {
      console.log(error);
    }
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
    scrollToBottom();
   
    setTimeout(() => {
      const botMsgHTML = `<img src="https://raw.githubusercontent.com/FoodYze/MyGeli/refs/heads/main/App/build_Heitor/build/assets/frame1/geli_icon.png" alt="Imagem da Geli" class="avatar"><p class="message-text">Just a sec...</p>`;
      const botMsgDiv = createMsgElement(botMsgHTML, "bot-message", "loading");
      chatsContainer.appendChild(botMsgDiv);
      scrollToBottom();
      generateResponse(botMsgDiv);
    }, 600);
  }
 
  promptForm.addEventListener("submit", handleFormSubmit);
});
