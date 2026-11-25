const hostname = window.location.hostname;
const newsEndpoint = window.NEWS_API_ENDPOINT ||
    (hostname === "localhost" || hostname === "127.0.0.1"
        ? `http://${hostname}:7071/api/query`
        : "https://news-chat-app.azurewebsites.net/api/query");

document.addEventListener("DOMContentLoaded", function () {
    const chatHistory = [];
    const chatHistoryContainer = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typing = document.createElement('img');
    typing.className = 'typing-bot-response';
    typing.src = "images/typing.gif"
    
    async function fetchChatResponse(userMessage) {
        sendButton.disabled = true;
        updateChatHistoryDisplay(userMessage, chatHistoryContainer, userInput, true, typing);

        // Prepare the request payload
        const requestData = { "message": userMessage, "chatHistory": chatHistory };
        try {
            // Send the request to the server endpoint
            const response = await fetch(newsEndpoint, {
                method: "POST",
                headers: {
                     "Content-type": "application/json; charset=UTF-8"
                },
                body: JSON.stringify(requestData)
            });
            if (!response.ok) {
                throw new Error(`Chat request failed with HTTP ${response.status}`);
            }
            const responsePayload = await response.json();
            if (typeof responsePayload.response !== "string" || !responsePayload.response.trim()) {
                throw new Error("Chat API returned an invalid response");
            }

            // Append user message and response to chat history
            chatHistory.push([userMessage, responsePayload.response]);
            updateChatHistoryDisplay(responsePayload.response, chatHistoryContainer, userInput, false, typing);
        } catch (error) {
            console.error("Error:", error);
            const errorElement = document.createElement('div');
            errorElement.className = 'message-bot-response';
            errorElement.textContent = "Unable to get the news response. Please try again.";
            chatHistoryContainer.appendChild(errorElement);
        } finally {
            userInput.removeAttribute("disabled");
            sendButton.disabled = false;
            if (typing.parentNode === chatHistoryContainer) {
                chatHistoryContainer.removeChild(typing);
            }
            userInput.focus();
            chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
        }

    }
    sendButton.addEventListener('click', async () => {
        if (sendButton.disabled) return;
        const userMessage = userInput.value.trim();
        if (!userMessage) return;
        userInput.value = '';
        await fetchChatResponse(userMessage);
    });

    // Handle 'Enter' key press for submitting
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            if (event.shiftKey) {
                // Allow new line when Shift + Enter is pressed
                return;
              } else {
                // Prevent default form submission behavior
                event.preventDefault();
                sendButton.click();
                console.log("Enter key pressed");
              }
        }

    });

});


function updateChatHistoryDisplay(message, chatHistoryContainer, userInput, userMessage, typing) {
    const messageElement = document.createElement('div');
    if(userMessage){
        messageElement.className = 'message-user-message';
        messageElement.textContent = message;
    }else{
        messageElement.className = 'message-bot-response';
        //const formattedNewsContent = formatNewsString(message);
        messageElement.innerHTML = message;
    }
    
    chatHistoryContainer.appendChild(messageElement);

    if(userMessage){
        chatHistoryContainer.appendChild(typing);
        userInput.setAttribute("disabled", true);
    }else{
    }
    chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
}

