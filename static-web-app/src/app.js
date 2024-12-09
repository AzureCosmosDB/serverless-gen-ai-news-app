const newsEndpoint = "https://news-chat-app.azurewebsites.net/api/query";

document.addEventListener("DOMContentLoaded", function () {
    const chatHistory = [];
    const chatHistoryContainer = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-button');
    const typing = document.createElement('img');
    typing.className = 'typing-bot-response';
    typing.src = "images/typing.gif"
    
    async function fetchChatResponse(userMessage) {
        updateChatHistoryDisplay(userMessage, chatHistoryContainer, userInput, true, typing);

        // Prepare the request payload
        requestData = { "message": userMessage, "chatHistory": chatHistory };
        console.log("Request Data:", JSON.stringify(requestData));
        try {
            // Send the request to the server endpoint
            const response = await fetch(newsEndpoint, {
                method: "POST",
                headers: {
                     "Content-type": "application/json; charset=UTF-8"
                },
                body: JSON.stringify(requestData)
            });
            const responsePayload = await response.json();
            console.log("Response Data:", responsePayload);
            // Check if the response is cached
            const cached = responsePayload.cached;

            // Append user message and response to chat history
            chatHistory.push([userMessage, responsePayload.response]);
            updateChatHistoryDisplay(responsePayload.response, chatHistoryContainer, userInput, false, typing);
        } catch (error) {
            console.error("Error:", error);
        }

        // Clear the input box after sending the message
        document.getElementById("user-input").value = "";

    }
    sendButton.addEventListener('click', async () => {
        const userMessage = userInput.value;
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
        userInput.removeAttribute("disabled");
        chatHistoryContainer.removeChild(typing);
        userInput.focus();
    }
    chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
}

