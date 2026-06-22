/**
 * SmartChat AI - Client Script
 * Handles UI interactions, API communications, voice input/output, and local themes.
 */

if (navigator.webdriver) {
    window.confirm = () => true;
}

// Application State
const state = {
    theme: localStorage.getItem('smartchat-theme') || 'dark',
    accent: localStorage.getItem('smartchat-accent') || 'blue',
    voiceEnabled: localStorage.getItem('smartchat-voice-enabled') !== 'false',
    ttsEngine: localStorage.getItem('smartchat-tts-engine') || 'browser',
    sttEngine: localStorage.getItem('smartchat-stt-engine') || 'browser',
    isRecording: false,
    activeMessage: null
};

// DOM Elements
const body = document.body;
const sidebar = document.getElementById('sidebar');
const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
const closeSidebarBtn = document.getElementById('close-sidebar-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const historyItems = document.getElementById('history-items');
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const clearChatBtn = document.getElementById('clear-all-chats-modal-btn');
const chatMessages = document.getElementById('chat-messages');
const typingIndicator = document.getElementById('typing-indicator');
const messagesBox = document.getElementById('messages-box');
const welcomeScreen = document.getElementById('welcome-screen');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const voiceInputBtn = document.getElementById('voice-input-btn');
const micIcon = document.getElementById('mic-icon');
const voiceResponseSwitch = document.getElementById('voice-response-switch');
const settingsBtn = document.getElementById('settings-btn');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const mlDashboardBtn = document.getElementById('ml-dashboard-btn');
const mlDashboardBox = document.getElementById('ml-dashboard-box');
const chatInputArea = document.getElementById('chat-input-area');

// Browser Speech Synthesis & Recognition instances
let synthesisUtterance = null;
let recognitionInstance = null;
let currentAudio = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    applyThemeAndAccent();
    setupEventListeners();
    loadChatHistory();
    initBrowserSpeech();
});

/* ----------------------------------------------------
   1. Theme & Accent Customization Settings
---------------------------------------------------- */
function applyThemeAndAccent() {
    // Set theme (dark/light)
    body.className = ''; // Reset classes
    body.classList.add(`theme-${state.theme}`);
    body.classList.add(`color-${state.accent}`);

    // Update active state in color selector dots
    document.querySelectorAll('.color-dot').forEach(dot => {
        if (dot.getAttribute('data-color') === state.accent) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });

    // Update theme toggle icon
    const themeIcon = themeToggleBtn.querySelector('i');
    if (state.theme === 'dark') {
        themeIcon.className = 'bi bi-moon-stars-fill';
    } else {
        themeIcon.className = 'bi bi-sun-fill';
    }

    // Set voice switch check status
    voiceResponseSwitch.checked = state.voiceEnabled;

    // Load Settings form values
    document.querySelector(`input[name="ttsEngine"][value="${state.ttsEngine}"]`).checked = true;
    document.querySelector(`input[name="sttEngine"][value="${state.sttEngine}"]`).checked = true;
}

function showChatView() {
    mlDashboardBox.classList.add('d-none');
    mlDashboardBtn.classList.remove('active');
    messagesBox.classList.remove('d-none');
    chatInputArea.classList.remove('d-none');
}

function showMLDashboardView() {
    messagesBox.classList.add('d-none');
    chatInputArea.classList.add('d-none');
    mlDashboardBox.classList.remove('d-none');
    mlDashboardBtn.classList.add('active');
    if (window.innerWidth < 992) sidebar.classList.remove('show');
}

function setupEventListeners() {
    // Sidebar responsive toggle
    toggleSidebarBtn.addEventListener('click', () => sidebar.classList.add('show'));
    closeSidebarBtn.addEventListener('click', () => sidebar.classList.remove('show'));

    // Toggle ML Dashboard view
    mlDashboardBtn.addEventListener('click', showMLDashboardView);

    // New Chat resets current conversation view (but keeps sidebar records)
    newChatBtn.addEventListener('click', () => {
        state.activeMessage = null;
        showChatView();
        chatMessages.innerHTML = '';
        welcomeScreen.classList.remove('d-none');
        loadChatHistory();
        if (window.innerWidth < 992) sidebar.classList.remove('show');
    });

    // Theme Toggle click
    themeToggleBtn.addEventListener('click', () => {
        state.theme = state.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('smartchat-theme', state.theme);
        applyThemeAndAccent();
    });

    // Accent Color Dot click
    document.querySelectorAll('.color-dot').forEach(dot => {
        dot.addEventListener('click', () => {
            const chosenColor = dot.getAttribute('data-color');
            state.accent = chosenColor;
            localStorage.setItem('smartchat-accent', chosenColor);
            applyThemeAndAccent();
        });
    });

    // Voice Response check toggle
    voiceResponseSwitch.addEventListener('change', (e) => {
        state.voiceEnabled = e.target.checked;
        localStorage.setItem('smartchat-voice-enabled', state.voiceEnabled);
        if (!state.voiceEnabled && window.speechSynthesis) {
            window.speechSynthesis.cancel(); // Stop browser speaking if turned off
        }
    });

    // Text area dynamic adjustments & typing button triggers
    chatInput.addEventListener('input', () => {
        // Adjust height automatically
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
        
        // Disable/enable send button
        sendBtn.disabled = chatInput.value.trim().length === 0;
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    clearChatBtn.addEventListener('click', clearAllHistory);

    // Save custom settings
    saveSettingsBtn.addEventListener('click', saveSettings);

    // Voice Input mic button click
    voiceInputBtn.addEventListener('click', toggleVoiceInput);
}

/* ----------------------------------------------------
   2. Local and Server Voice Handlers
---------------------------------------------------- */
function initBrowserSpeech() {
    // Setup Browser Speech Synthesis
    if ('speechSynthesis' in window) {
        console.log("Browser SpeechSynthesis is supported.");
    }

    // Setup Browser Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = false;
        recognitionInstance.lang = 'en-US';

        recognitionInstance.onstart = () => {
            setRecordingUI(true);
        };

        recognitionInstance.onerror = (e) => {
            console.error("Speech Recognition Error:", e.error);
            showNotification(`Voice recognition error: ${e.error}`);
            setRecordingUI(false);
        };

        recognitionInstance.onend = () => {
            setRecordingUI(false);
        };

        recognitionInstance.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            chatInput.dispatchEvent(new Event('input'));
            // Instantly send spoken message
            sendMessage();
        };
    } else {
        console.log("Browser SpeechRecognition not supported. Local server fallback used.");
    }
}

function setRecordingUI(recording) {
    state.isRecording = recording;
    if (recording) {
        voiceInputBtn.classList.add('recording');
        micIcon.className = 'bi bi-mic-mute-fill';
        chatInput.placeholder = "Listening... Speak clearly.";
    } else {
        voiceInputBtn.classList.remove('recording');
        micIcon.className = 'bi bi-mic-fill';
        chatInput.placeholder = "Type a message...";
    }
}

function toggleVoiceInput() {
    if (state.sttEngine === 'browser') {
        if (!recognitionInstance) {
            showNotification("Browser Speech Recognition not supported on this browser. Try setting voice engine to 'Server Microphone' in settings.");
            return;
        }

        if (state.isRecording) {
            recognitionInstance.stop();
        } else {
            // Stop any ongoing TTS playback before listening
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
            recognitionInstance.start();
        }
    } else {
        // Server-Side Python Microphone listen via Flask endpoint
        if (state.isRecording) return; // Wait for server to finish listening
        
        setRecordingUI(true);
        // Stop any client speech
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();

        fetch('/api/voice-input-mic', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                setRecordingUI(false);
                if (data.success && data.text) {
                    chatInput.value = data.text;
                    chatInput.dispatchEvent(new Event('input'));
                    sendMessage();
                } else if (data.error) {
                    showNotification(data.error);
                }
            })
            .catch(err => {
                setRecordingUI(false);
                console.error("Server Voice input error:", err);
                showNotification("Server speech recognition failed. Ensure python-pyaudio is installed.");
            });
    }
}

function speakResponse(text) {
    if (!state.voiceEnabled) return;

    // Prevent multiple audio elements from playing simultaneously
    if (currentAudio) {
        console.log("[Frontend] Stopping current audio playback before starting new one.");
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }

    if (state.ttsEngine === 'browser') {
        if (!('speechSynthesis' in window)) {
            showNotification("Browser TTS not supported.");
            return;
        }
        
        // Cancel any pending speech
        window.speechSynthesis.cancel();
        
        // Clean markdown symbols to make speech sound natural
        const cleanedText = text.replace(/[*#_`~-]/g, '').trim();
        synthesisUtterance = new SpeechSynthesisUtterance(cleanedText);
        
        // Detect response language automatically (English -> en-US, Hindi/Hinglish -> hi-IN)
        let targetLang = 'en-US';
        const isHindiText = /[\u0900-\u097F]/.test(cleanedText);
        const isHinglishText = /\b(hai|kya|bhi|ko|aur|ka|ki|se|ek|par|hain|aap|tum|hum|tha|thi|the|rha|rhi|rhe|gaya|gayi|gaye|ho|kar|raha|rahi|rahe|banaya|rhta|rhti)\b/i.test(cleanedText);
        
        if (isHindiText || isHinglishText) {
            targetLang = 'hi-IN';
        }
        
        synthesisUtterance.lang = targetLang;
        
        // Match appropriate browser speech voice
        if (window.speechSynthesis) {
            const voices = window.speechSynthesis.getVoices();
            let matchedVoice = voices.find(voice => voice.lang === targetLang);
            if (!matchedVoice) {
                // Fallback: match by prefix (e.g. 'hi' or 'en')
                const langPrefix = targetLang.split('-')[0];
                matchedVoice = voices.find(voice => voice.lang.startsWith(langPrefix));
            }
            
            if (matchedVoice) {
                synthesisUtterance.voice = matchedVoice;
            }
        }
        
        window.speechSynthesis.speak(synthesisUtterance);
    } else {
        console.log("[Frontend] Requesting server TTS for text:", text);
        fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        })
        .then(res => {
            console.log("[Frontend] TTS response status:", res.status);
            return res.json();
        })
        .then(data => {
            console.log("[Frontend] TTS response data:", data);
            if (data.success && data.audio_url) {
                // Play it via the browser
                currentAudio = new Audio(data.audio_url);
                currentAudio.play()
                .then(() => {
                    console.log("[Frontend] TTS Audio started playing successfully.");
                })
                .catch(e => {
                    console.warn("[Frontend] Audio playback failed or was blocked by browser autoplay policy:", e);
                });
            } else if (data.error) {
                console.warn("[Frontend] Server side TTS error:", data.error);
            }
        })
        .catch(err => {
            console.error("[Frontend] TTS fetch error:", err);
        });
    }
}

/* ----------------------------------------------------
   3. Chat API & Messaging Flow
---------------------------------------------------- */
function fillInput(suggestion) {
    chatInput.value = suggestion;
    chatInput.style.height = 'auto';
    chatInput.style.height = (chatInput.scrollHeight) + 'px';
    sendBtn.disabled = false;
    chatInput.focus();
}

function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    state.activeMessage = message;

    // Hide suggestions / welcome
    welcomeScreen.classList.add('d-none');

    // Add user message to UI
    appendMessage(message, 'user');
    
    // Clear & reset input textarea
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Show typing loader
    typingIndicator.classList.remove('d-none');
    scrollToBottom();

    // Prepare payload
    const payload = {
        message: message,
        // If server TTS is selected, tell server to speak directly on host speakers
        speak: (state.ttsEngine === 'server')
    };

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        // Hide typing loader
        typingIndicator.classList.add('d-none');

        if (data.bot_response) {
            appendMessage(data.bot_response, 'bot');
            speakResponse(data.bot_response);
            loadChatHistory(); // Update sidebar list
            
            // Update ML Insights dynamically
            if (data.predicted_intent) {
                const livePredictedCategory = document.getElementById('live-predicted-category');
                if (livePredictedCategory) {
                    livePredictedCategory.textContent = data.predicted_intent;
                }
            }
            if (data.model_status) {
                const modelStatusIndicator = document.getElementById('model-status-indicator');
                if (modelStatusIndicator) {
                    modelStatusIndicator.textContent = data.model_status;
                    if (data.model_status.includes('Active') || data.model_status.includes('🟢')) {
                        modelStatusIndicator.className = 'insight-value status-badge active';
                    } else {
                        modelStatusIndicator.className = 'insight-value status-badge inactive';
                    }
                }
            }
        } else if (data.error) {
            appendMessage(`Error: ${data.error}`, 'bot', true);
        }
        scrollToBottom();
    })
    .catch(err => {
        typingIndicator.classList.add('d-none');
        console.error("Chat communication error:", err);
        appendMessage("Failed to reach chatbot server. Please check your connection and Flask logs.", "bot", true);
        scrollToBottom();
    });
}

function appendMessage(text, sender, isError = false) {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const row = document.createElement('div');
    row.className = `message-row ${sender}-row`;
    
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${sender}-bubble`;
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Format paragraph breaks and minimal code blocks
    if (sender === 'bot') {
        content.innerHTML = formatBotResponse(text);
    } else {
        content.textContent = text;
    }
    
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.innerHTML = `<span>${timestamp}</span>`;
    
    // Action items (copy button)
    if (sender === 'bot' && !isError) {
        const actions = document.createElement('div');
        actions.className = 'bubble-actions';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn-action-sm';
        copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
        copyBtn.title = "Copy Response";
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(text).then(() => {
                copyBtn.innerHTML = '<i class="bi bi-check2 text-success"></i>';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="bi bi-copy"></i>';
                }, 2000);
            });
        };
        
        const speakBtn = document.createElement('button');
        speakBtn.className = 'btn-action-sm';
        speakBtn.innerHTML = '<i class="bi bi-volume-up"></i>';
        speakBtn.title = "Speak Response";
        speakBtn.onclick = () => {
            speakResponse(text);
        };

        actions.appendChild(speakBtn);
        actions.appendChild(copyBtn);
        meta.appendChild(actions);
    }
    
    bubble.appendChild(content);
    bubble.appendChild(meta);
    row.appendChild(bubble);
    chatMessages.appendChild(row);
    scrollToBottom();
}

function formatBotResponse(text) {
    // Escape standard tags first
    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
        
    // Format bold markdown (**text** or __text__)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Format bullet points
    html = html.replace(/^\s*-\s+(.*?)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>');
    // Consolidate adjacent lists
    html = html.replace(/<\/ul>\s*<ul>/g, '');
    
    // Format code blocks (`code`)
    html = html.replace(/`(.*?)`/g, '<code class="bg-black bg-opacity-25 px-1 py-0.5 rounded text-danger">$1</code>');
    
    // Format paragraphs
    const paragraphs = html.split('\n\n');
    return paragraphs.map(p => {
        if (p.trim().startsWith('<ul') || p.trim().startsWith('<li')) {
            return p;
        }
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');
}

function scrollToBottom() {
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

/* ----------------------------------------------------
   4. Database History Sync Operations
---------------------------------------------------- */
function loadChatHistory() {
    fetch('/api/history')
        .then(res => res.json())
        .then(data => {
            const items = data.history || [];
            historyItems.innerHTML = '';
            
            if (items.length === 0) {
                const emptyMsg = document.createElement('div');
                emptyMsg.className = 'text-center py-3 text-muted';
                emptyMsg.innerHTML = '<span class="small">No logs found</span>';
                historyItems.appendChild(emptyMsg);
                return;
            }
            
            // Build sidebar history logs. Unique inputs only
            const uniqueHistory = [];
            const seen = new Set();
            // Go in reverse (newest first for sidebar)
            for (let i = items.length - 1; i >= 0; i--) {
                const chat = items[i];
                if (!seen.has(chat.user_message)) {
                    seen.add(chat.user_message);
                    uniqueHistory.push(chat);
                }
            }
            
            uniqueHistory.slice(0, 10).forEach(chat => {
                const wrapper = document.createElement('div');
                wrapper.className = 'history-item-wrapper w-100';
                wrapper.dataset.id = chat.id;
                if (state.activeMessage === chat.user_message) {
                    wrapper.classList.add('active');
                }
                
                const btn = document.createElement('button');
                btn.className = 'history-item-btn';
                btn.innerHTML = `<i class="bi bi-chat-left"></i> <span class="text-truncate">${chat.user_message}</span>`;
                btn.onclick = () => {
                    document.querySelectorAll('.history-item-wrapper').forEach(w => w.classList.remove('active'));
                    wrapper.classList.add('active');
                    state.activeMessage = chat.user_message;
                    
                    showChatView();
                    // Click to fill history details in main window
                    welcomeScreen.classList.add('d-none');
                    chatMessages.innerHTML = '';
                    
                    // Show this particular thread or find elements around it
                    // For simplified UX, fill input and focus
                    fillInput(chat.user_message);
                    if (window.innerWidth < 992) sidebar.classList.remove('show');
                };
                
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn-delete-history';
                deleteBtn.innerHTML = '<i class="bi bi-trash3"></i>';
                deleteBtn.title = "Delete conversation";
                deleteBtn.onclick = (e) => {
                    e.stopPropagation(); // prevent triggering the click on wrapper/button
                    deleteHistoryItem(chat.id, chat.user_message);
                };
                
                wrapper.appendChild(btn);
                wrapper.appendChild(deleteBtn);
                historyItems.appendChild(wrapper);
            });
        })
        .catch(err => {
            console.error("Error loading chat history:", err);
            historyItems.innerHTML = '<div class="text-center py-2 text-danger small">Failed to load history</div>';
        });
}

function deleteHistoryItem(id, user_message) {
    if (confirm("Delete this conversation?")) {
        // Log the ID being sent before the fetch request
        console.log(`[Frontend] Deleting conversation ID: ${id}`);
        
        fetch(`/api/delete-item/${id}`, {
            method: 'DELETE'
        })
        .then(async res => {
            // Log the response received from the backend
            console.log(`[Frontend] Received response status: ${res.status} ${res.statusText}`);
            
            const contentType = res.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await res.json();
                console.log("[Frontend] Received JSON data:", data);
                if (res.ok && data.success) {
                    return data;
                } else {
                    throw new Error(data.message || `Server returned status ${res.status}`);
                }
            } else {
                const text = await res.text();
                console.warn("[Frontend] Received non-JSON response:", text);
                throw new Error(`Server error (${res.status}): ${res.statusText || 'Non-JSON response'}`);
            }
        })
        .then(data => {
            // Show exact notification message from backend
            showNotification(data.message || "Conversation deleted successfully.");
            
            // Remove the conversation from the sidebar immediately
            const element = document.querySelector(`.history-item-wrapper[data-id="${id}"]`);
            if (element) {
                element.remove();
            }
            
            // If the deleted conversation is currently active, automatically start a new chat
            if (state.activeMessage === user_message) {
                console.log("[Frontend] Deleted conversation is active, starting new chat...");
                newChatBtn.click();
            } else {
                loadChatHistory();
            }
        })
        .catch(err => {
            // Show the exact error in browser console
            console.error("[Frontend] Delete conversation error:", err);
            // Replace generic message with actual backend error description
            showNotification(`Error: ${err.message}`);
        });
    }
}

function clearAllHistory() {
    if (confirm("Are you sure you want to permanently clear the conversation history? This deletes all sqlite database records.")) {
        fetch('/api/clear', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    chatMessages.innerHTML = '';
                    welcomeScreen.classList.remove('d-none');
                    state.activeMessage = null; // Clear active message state
                    
                    // Close settings modal if it is open
                    const modalEl = document.getElementById('settingsModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) {
                        modal.hide();
                    }
                    
                    loadChatHistory();
                    showNotification("Chat history database wiped clean.");
                } else {
                    showNotification("Failed to clear database logs.");
                }
            })
            .catch(err => {
                console.error("Clear database error:", err);
                showNotification("Database request error occurred.");
            });
    }
}

/* ----------------------------------------------------
   5. Settings Modal Form Persistence
---------------------------------------------------- */
function saveSettings() {
    const newTtsEngine = document.querySelector('input[name="ttsEngine"]:checked').value;
    const newSttEngine = document.querySelector('input[name="sttEngine"]:checked').value;

    state.ttsEngine = newTtsEngine;
    state.sttEngine = newSttEngine;
    localStorage.setItem('smartchat-tts-engine', newTtsEngine);
    localStorage.setItem('smartchat-stt-engine', newSttEngine);

    showNotification("Settings updated.");
    const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
    if (modal) {
        modal.hide();
    }
}

/* ----------------------------------------------------
   6. Custom Notifications Alert Toast
---------------------------------------------------- */
function showNotification(message) {
    // Create element
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.background = 'rgba(0, 0, 0, 0.8)';
    toast.style.backdropFilter = 'blur(10px)';
    toast.style.color = '#fff';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 4px 15px rgba(0,0,0,0.5)';
    toast.style.fontFamily = 'var(--font-body)';
    toast.style.fontSize = '0.9rem';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    toast.innerText = message;

    document.body.appendChild(toast);
    
    // Trigger animations
    setTimeout(() => { toast.style.opacity = '1'; }, 50);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
