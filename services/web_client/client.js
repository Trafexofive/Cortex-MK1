document.addEventListener("DOMContentLoaded", () => {
    const statusDiv = document.getElementById("status");
    const conversationDiv = document.getElementById("conversation");
    const promptInput = document.getElementById("prompt-input");
    const sendButton = document.getElementById("send-button");

    const gatewayHost = window.location.hostname;
    const gatewayPort = 8080; // Assuming the gateway is on port 8080
    const wsUrl = `ws://${gatewayHost}:${gatewayPort}/v1/inference/stream`;

    let socket;

    function connect() {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            statusDiv.textContent = "Connected";
            statusDiv.style.backgroundColor = "#03dac6";
            addMessage("assistant", "Connected to Cortex-Prime. Ready for input.");
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.response_text) {
                    addMessage("assistant", data.response_text);
                }
            } catch (error) {
                console.error("Error parsing message:", error);
                addMessage("assistant", `Received non-JSON message: ${event.data}`);
            }
        };

        socket.onclose = () => {
            statusDiv.textContent = "Disconnected. Retrying...";
            statusDiv.style.backgroundColor = "#cf6679";
            setTimeout(connect, 3000); // Retry connection after 3 seconds
        };

        socket.onerror = (error) => {
            console.error("WebSocket Error:", error);
            statusDiv.textContent = "Error";
            statusDiv.style.backgroundColor = "#cf6679";
        };
    }

    function addMessage(role, text) {
        const messageElem = document.createElement("div");
        messageElem.classList.add("message", role);
        messageElem.textContent = text;
        conversationDiv.appendChild(messageElem);
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
    }

    function sendMessage() {
        const prompt = promptInput.value.trim();
        if (prompt && socket && socket.readyState === WebSocket.OPEN) {
            addMessage("user", prompt);
            socket.send(prompt); // For B-Line, just send the raw text
            promptInput.value = "";
        }
    }

    sendButton.addEventListener("click", sendMessage);
    promptInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    connect();
});
