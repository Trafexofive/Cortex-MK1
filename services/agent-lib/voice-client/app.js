// --- app_keyword_v2.js ---

document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration ---
    const API_URL = 'https://agent.clevo.ddnsgeek.com/prompt'; // YOUR endpoint
    const REQUEST_TIMEOUT_MS = 30000;
    const KEYWORD = "agent"; // YOUR keyword (lowercase)
    // --------------------

    // --- DOM Elements ---
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('userInput'); // Used for visual feedback of transcription
    const sendButton = document.getElementById('sendButton'); // Likely remains disabled
    const statusDiv = document.getElementById('status'); // For processing/error status
    const keywordStatusDiv = document.getElementById('keywordStatus');
    const keywordButton = document.getElementById('keywordButton');

    // --- State Management ---
    const STATE = {
        IDLE: 'IDLE',
        LISTENING: 'LISTENING', // Actively listening for keyword OR command
        PROCESSING: 'PROCESSING', // Waiting for API response
        ERROR: 'ERROR' // An error occurred (e.g., mic access, network)
    };
    let currentState = STATE.IDLE;
    let isListenerGloballyActive = false; // User wants the listener ON
    let recognitionInstance = null;
    let finalCommandTranscript = ''; // Store the command part after keyword

    // --- Web Speech API Setup ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.error("Web Speech API not supported.");
        setState(STATE.ERROR, "Speech recognition not supported by this browser.");
        if (keywordButton) keywordButton.disabled = true;
        return; // Stop initialization
    }

    // --- Main Functions ---

    function initializeRecognition() {
        if (recognitionInstance) {
            // Clean up previous instance if exists
            recognitionInstance.onstart = null;
            recognitionInstance.onresult = null;
            recognitionInstance.onerror = null;
            recognitionInstance.onend = null;
            try {
                 if (currentState === STATE.LISTENING) recognitionInstance.stop();
            } catch(e) { console.warn("Error stopping previous instance:", e);}
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = true; // Keep running until stopped
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            console.log("Recognition started.");
            // State change might have already happened in startListener
             if (currentState === STATE.IDLE && isListenerGloballyActive) {
                setState(STATE.LISTENING);
            }
        };

        recognition.onresult = handleRecognitionResult;

        recognition.onerror = (event) => {
            console.error('Recognition Error:', event.error, event.message);
            handleRecognitionError(event.error);
        };

        recognition.onend = () => {
            console.log("Recognition ended.");
            // Only restart automatically if the user *wants* the listener active
            // and we aren't currently processing a command or in an error state.
            if (isListenerGloballyActive && currentState !== STATE.PROCESSING && currentState !== STATE.ERROR) {
                console.log("Attempting controlled restart...");
                // Add slight delay to prevent potential browser rate-limiting or infinite loops on some errors
                setTimeout(() => {
                    if (isListenerGloballyActive && currentState !== STATE.PROCESSING && currentState !== STATE.ERROR) {
                         startRecognition(); // Attempt to start again
                    }
                }, 300); // 300ms delay
            } else {
                 // If listener is supposed to be off, or we are processing/in error, ensure IDLE state if not PROCESSING/ERROR
                 if (currentState !== STATE.PROCESSING && currentState !== STATE.ERROR) {
                    setState(STATE.IDLE);
                 }
            }
        };
        recognitionInstance = recognition; // Store the new instance
        return recognition;
    }

    function startListener() {
        if (!SpeechRecognition) {
             setState(STATE.ERROR, "Speech Recognition not supported.");
             return;
        }
        if (currentState !== STATE.IDLE && currentState !== STATE.ERROR) {
             console.warn("Listener already active or processing.");
             return;
        }
        isListenerGloballyActive = true;
        console.log("User activated listener.");
        if (startRecognition()) {
             // State will be set to LISTENING by startRecognition or onstart
        } else {
             isListenerGloballyActive = false; // Failed to start
             // Error state likely set by startRecognition failure
        }
    }

    function stopListener() {
        isListenerGloballyActive = false;
        console.log("User deactivated listener.");
        stopRecognition();
        // State will be set to IDLE by stopRecognition or onend
    }

    function startRecognition() {
         if (!recognitionInstance) {
             initializeRecognition();
         }
         if (!recognitionInstance) { // Still null after init attempt?
             setState(STATE.ERROR, "Failed to initialize Speech Recognition.");
             return false;
         }

         // Check if already running to prevent InvalidStateError
         // Note: No standard way to check if 'running', rely on state and try/catch
         if (currentState === STATE.LISTENING) {
             console.log("Recognition appears to be already listening.");
             return true;
         }

         console.log("Calling recognition.start()...");
         try {
             finalCommandTranscript = ''; // Reset command transcript
             recognitionInstance.start();
             // Assuming onstart will correctly set LISTENING state
             setState(STATE.LISTENING); // Optimistically set state here
             return true;
         } catch (e) {
             if (e.name === 'InvalidStateError') {
                 console.warn("Attempted to start recognition but it was already started.");
                 setState(STATE.LISTENING); // Ensure UI is correct
                 return true; // It's effectively running
             } else {
                 console.error("Error calling recognition.start():", e);
                 handleRecognitionError(e.name || 'start-failed');
                 return false;
             }
         }
    }

     function stopRecognition() {
        if (recognitionInstance) {
            console.log("Calling recognition.stop()...");
            try {
                 // Prevent onend restart loop by checking isListenerGloballyActive flag first
                 recognitionInstance.stop();
                 // State update will happen in onend or here if needed immediately
                 if (currentState !== STATE.PROCESSING && currentState !== STATE.ERROR) {
                    setState(STATE.IDLE); // Force IDLE if stopped manually unless processing/error
                 }
            } catch (e) {
                if (e.name === 'InvalidStateError') {
                    console.warn("Attempted to stop recognition but it was not running.");
                    if (currentState !== STATE.PROCESSING && currentState !== STATE.ERROR) {
                       setState(STATE.IDLE); // Ensure UI consistency
                    }
                } else {
                    console.error("Error calling recognition.stop():", e);
                    // Potentially set error state? Or just log?
                    if (currentState !== STATE.PROCESSING && currentState !== STATE.ERROR) {
                       setState(STATE.IDLE);
                    }
                }
            }
            // recognitionInstance = null; // Keep instance for potential restart
        } else {
             console.log("No active recognition instance to stop.");
             if (currentState !== STATE.PROCESSING && currentState !== STATE.ERROR) {
               setState(STATE.IDLE); // Ensure UI consistency
             }
        }
    }

    function handleRecognitionResult(event) {
        let interimTranscript = '';
        let currentFinalTranscript = ''; // Transcript for this specific result event

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcriptPart = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                currentFinalTranscript += transcriptPart;
            } else {
                interimTranscript += transcriptPart;
            }
        }

        // Update UI feedback field
        userInput.value = (finalCommandTranscript + currentFinalTranscript + interimTranscript).trim();

        const processedInterim = interimTranscript.toLowerCase().trim();
        const processedFinal = currentFinalTranscript.toLowerCase().trim();

        // Keyword spotting in interim results (more responsive)
        if (currentState === STATE.LISTENING && processedInterim.includes(KEYWORD)) {
            console.log("Keyword detected in interim results.");
            // Don't change major state yet, wait for final or more input
            // Optionally provide visual cue that keyword was heard
             setKeywordStatus(`Status: Keyword "${KEYWORD}" heard, listening for command...`);
        }

        // Process final results
        if (currentFinalTranscript) {
            console.log("Final segment received:", processedFinal);
            finalCommandTranscript += processedFinal + " "; // Append final parts

            const keywordIndex = finalCommandTranscript.toLowerCase().indexOf(KEYWORD);

            if (keywordIndex !== -1) {
                const command = finalCommandTranscript.substring(keywordIndex + KEYWORD.length).trim();
                if (command) {
                    console.log("Command extracted after keyword:", command);
                    isListenerGloballyActive = false; // Stop listening automatically after command
                    stopRecognition();
                    setState(STATE.PROCESSING);
                    addMessageToChat('user', command);
                    sendMessageToAgent(command);
                    finalCommandTranscript = ''; // Reset for next time
                } else {
                    console.log("Keyword found in final transcript, but no command followed yet.");
                    // Keep listening for more final results if recognition.continuous=true allows
                }
            } else {
                 // Final segment doesn't contain keyword, reset command transcript if needed
                 console.log("Final segment without keyword detected.");
                 // Reset if it seems like a new utterance unrelated to keyword? Heuristic needed.
                 // For now, just keep appending, assuming keyword might come later in continuous stream.
                 // A more robust approach might reset finalCommandTranscript on longer pauses.
                 // For simplicity with continuous=true, we primarily rely on keyword detection to trigger action.
                 // If continuous causes issues, switch back to continuous=false and handle logic in onend.
            }
        }
    }

    function handleRecognitionError(errorCode) {
        let userMessage = `Speech Error: ${errorCode}`;
        switch (errorCode) {
            case 'no-speech': userMessage = "No speech detected. Please try again."; break;
            case 'audio-capture': userMessage = "Microphone error. Check connection/settings."; break;
            case 'not-allowed': userMessage = "Microphone access denied. Please allow in browser settings."; break;
            case 'service-not-allowed': userMessage = "Microphone access blocked (browser/OS setting?)."; break;
            case 'network': userMessage = "Network error during speech recognition."; break;
            case 'aborted': userMessage = "Speech input aborted."; break; // User likely stopped it
            case 'language-not-supported': userMessage = "Language not supported."; break;
            case 'bad-grammar': userMessage = "Grammar error in speech service."; break; // Less common
            case 'start-failed': userMessage = "Could not start microphone. Check permissions."; break;
            default: userMessage = `An unknown speech error occurred (${errorCode}).`; break;
        }
        setState(STATE.ERROR, userMessage); // Set error state and message
    }

    // --- API Interaction ---
    async function sendMessageToAgent(promptText) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
             controller.abort();
             console.log("Request aborted due to timeout.");
             }, REQUEST_TIMEOUT_MS);

        try {
            console.log(`Sending request to: ${API_URL}`);
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ prompt: promptText }),
                signal: controller.signal
            });

            clearTimeout(timeoutId); // Clear timeout if fetch completes

            if (!response.ok) {
                 let errorMsg = `Error: ${response.status} ${response.statusText}`;
                 try { const errorData = await response.json(); errorMsg = `Agent API Error: ${errorData.error || response.statusText}${errorData.details ? ' | ' + errorData.details : ''}`; }
                 catch (e) { console.warn("Error response not JSON"); try { const textError = await response.text(); errorMsg += ` | Body: ${textError.substring(0,100)}`;} catch(e2){} }
                 throw new Error(errorMsg);
            }

            const data = await response.json();
            if (data && typeof data.response === 'string') {
                addMessageToChat('agent', data.response);
                 setState(STATE.LISTENING); // Go back to listening state after successful processing
                 if(isListenerGloballyActive) startRecognition(); // Try restarting if user still wants it on
            } else {
                throw new Error("Unexpected response format from agent.");
            }

        } catch (error) {
            clearTimeout(timeoutId); // Clear timeout on error too
            let errorMsg = `Failed to get response: ${error.message}`;
             if (error.name === 'AbortError') {
                 errorMsg = `Request timed out (${REQUEST_TIMEOUT_MS / 1000}s).`;
             } else if (error instanceof TypeError && error.message.includes('fetch')) {
                 errorMsg = `Network/CORS/HTTPS Error. Check URL, server status, and CORS headers.`;
             }
            console.error('sendMessage Error:', error);
            setState(STATE.ERROR, errorMsg); // Set error state
            addMessageToChat('system', errorMsg, true);
            // Don't automatically restart listener after error state
            isListenerGloballyActive = false; // Assume user needs to restart manually
        }
    }

    // --- UI Update Functions ---
    function setState(newState, statusMessage = '') {
         if (currentState === newState && !statusMessage) return;

         console.log(`Setting State: ${newState}, Message: "${statusMessage}"`);
         currentState = newState;
         let keywordStatusText = '';
         let mainStatusText = '';
         let kwButtonText = '';
         let kwButtonClassRemove = ['listening', 'recording'];
         let kwButtonClassAdd = [];
         let kwButtonDisabled = false;
         let inputDisabled = true;
         let sendDisabled = true;

         switch (newState) {
            case STATE.IDLE:
                keywordStatusText = 'Status: Idle. Press "Start Listening"';
                kwButtonText = "Start Listening";
                kwButtonDisabled = !SpeechRecognition;
                inputDisabled = false; // Allow typing when idle
                sendDisabled = false;
                break;
            case STATE.LISTENING:
                keywordStatusText = `Status: Listening for "${KEYWORD}"...`;
                kwButtonText = `Stop Listening ("${KEYWORD}")`;
                kwButtonClassAdd.push('listening');
                kwButtonDisabled = false;
                inputDisabled = true; // Disable typing while listening
                sendDisabled = true;
                break;
             // Note: No explicit RECORDING_COMMAND state needed for UI update logic,
             // rely on interim transcript updates and the final command check.
             // LISTENING state covers both visually.
            case STATE.PROCESSING:
                keywordStatusText = 'Status: Processing command...';
                mainStatusText = 'Agent is thinking...';
                kwButtonText = "Processing...";
                kwButtonDisabled = true;
                inputDisabled = true;
                sendDisabled = true;
                break;
            case STATE.ERROR:
                keywordStatusText = `Status: Error - ${statusMessage}`;
                mainStatusText = `Error: ${statusMessage}`; // Show error in main status too
                kwButtonText = "Start Listening"; // Allow restarting after error
                kwButtonDisabled = !SpeechRecognition; // Only disable if API not supported
                inputDisabled = false; // Allow typing after error
                sendDisabled = false;
                isListenerGloballyActive = false; // Force listener off on error
                stopRecognition(); // Ensure recognition is stopped
                break;
         }

         if (keywordStatusDiv) keywordStatusDiv.textContent = keywordStatusText;
         if (statusDiv) statusDiv.textContent = mainStatusText;
         if (keywordButton) {
             keywordButton.textContent = kwButtonText;
             keywordButton.disabled = kwButtonDisabled;
             kwButtonClassRemove.forEach(cls => keywordButton.classList.remove(cls));
             kwButtonClassAdd.forEach(cls => keywordButton.classList.add(cls));
         }
         if (userInput) {
             userInput.disabled = inputDisabled;
             userInput.placeholder = inputDisabled ? 'Listening for keyword...' : 'Type message or use listener';
         }
         if (sendButton) sendButton.disabled = sendDisabled;
    }

    function addMessageToChat(sender, messageText, isError = false) {
        if (!chatContainer) return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        const typeClass = isError ? 'system-error-message' : `${sender}-message`;
        messageDiv.classList.add(typeClass);
        messageDiv.textContent = messageText.replace(/</g, "<").replace(/>/g, ">"); // Basic sanitize
        chatContainer.appendChild(messageDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 50);
    }

    // --- Event Listeners ---
    keywordButton.addEventListener('click', () => {
        if (isListenerGloballyActive) {
            stopListener();
        } else {
            startListener();
        }
    });

    sendButton.addEventListener('click', () => {
         const text = userInput.value.trim();
         if (text && currentState !== STATE.PROCESSING && currentState !== STATE.LISTENING) {
             setState(STATE.PROCESSING);
             addMessageToChat('user', text);
             sendMessageToAgent(text);
             userInput.value = '';
         }
    });

     userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !sendButton.disabled && currentState !== STATE.LISTENING) {
            event.preventDefault();
            const text = userInput.value.trim();
             if (text) {
                 setState(STATE.PROCESSING);
                 addMessageToChat('user', text);
                 sendMessageToAgent(text);
                 userInput.value = '';
             }
        }
    });


    // --- Initial Page Load ---
    setState(STATE.IDLE); // Set initial state
    userInput.focus();
    console.log(`Keyword Listener V2 Initialized. Keyword: "${KEYWORD}", API: ${API_URL}`);

});
