document.addEventListener("DOMContentLoaded", () => {
    const statusDiv = document.getElementById("status");
    const voiceStatusDiv = document.getElementById("voice-status");
    const conversationDiv = document.getElementById("conversation");
    const promptInput = document.getElementById("prompt-input");
    const sendButton = document.getElementById("send-button");
    const speakButton = document.getElementById("speak-button");
    const transcriptionOutput = document.getElementById("transcription-output");

    const gatewayHost = window.location.hostname;
    const gatewayPort = window.location.port || (window.location.protocol === 'https:' ? 443 : 80);
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    const wsUrl = `${wsProtocol}//${gatewayHost}:${gatewayPort}/v1/inference/stream`;
    const voiceWsUrl = `${wsProtocol}//${gatewayHost}:${gatewayPort}/v1/voice/stream`;

    let socket;
    let voiceSocket;
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

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

    function connectVoice() {
        voiceStatusDiv.textContent = "Voice Connecting...";
        voiceStatusDiv.style.color = "#e0e0e0";
        voiceSocket = new WebSocket(voiceWsUrl);

        voiceSocket.onopen = () => {
            console.log("Voice WebSocket connected.");
            voiceStatusDiv.textContent = "Voice Connected";
            voiceStatusDiv.style.color = "#03dac6";
        };

        voiceSocket.onmessage = (event) => {
            transcriptionOutput.textContent = event.data;
            promptInput.value = event.data;
        };

        voiceSocket.onclose = (event) => {
            console.log("Voice WebSocket disconnected.", event);
            voiceStatusDiv.textContent = "Voice Disconnected";
            voiceStatusDiv.style.color = "#cf6679";
        };

        voiceSocket.onerror = (error) => {
            console.error("Voice WebSocket Error:", error);
            voiceStatusDiv.textContent = "Voice Error";
            voiceStatusDiv.style.color = "#cf6679";
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
            transcriptionOutput.textContent = "";
        }
    }

    async function startRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Your browser does not support audio recording.");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                console.log(`Audio blob created. Size: ${audioBlob.size} bytes`);
                if (voiceSocket && voiceSocket.readyState === WebSocket.OPEN) {
                    console.log("Sending audio blob to voice service.");
                    voiceSocket.send(audioBlob);
                }
                audioChunks = [];
            };
            mediaRecorder.start();
            speakButton.textContent = "Stop Recording";
            speakButton.classList.add("recording");
            isRecording = true;
        } catch (error) {
            console.error("Error accessing microphone:", error);
            alert("Could not access microphone. Please check permissions.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            speakButton.textContent = "Tap to Speak";
            speakButton.classList.remove("recording");
            isRecording = false;
        }
    }

    function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }

    sendButton.addEventListener("click", sendMessage);
    promptInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    speakButton.addEventListener("click", toggleRecording);

    connect();
    connectVoice();
});
