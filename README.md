# SmartChat AI – Voice Enabled Intelligent Chatbot

SmartChat AI is a premium, voice-enabled intelligent chatbot application that leverages Flask, SQLite, Google Gemini API, and a beautiful glassmorphic frontend built using HTML, CSS, JavaScript, and Bootstrap 5. It supports text and speech interactions, records conversations, and supports customization of accent themes instantly.

## 🚀 Key Features

* **🤖 Gemini AI Integration:** Seamless context-aware conversations powered by the latest Gemini models.
* **🎙️ Voice-to-Text (STT):** Dictate questions directly. Supports both server-side Python `SpeechRecognition` and client-side browser speech recognition.
* **🗣️ Text-to-Speech (TTS):** Responses are spoken aloud. Supports server-side `pyttsx3` (speaks via host hardware or serves rendered WAV files) and client-side browser Speech Synthesis.
* **🎨 Premium Glassmorphic UI:** Smooth hover animations, modern typography (Outfit & Inter fonts), auto-scrolling chat history, and loading indicators.
* **🌗 Theme Customization:** Dark mode, light mode, and instant accent color switches (Blue, Purple, Green, Orange) without page refresh.
* **💾 Database Storage:** SQLite backend storing chat history in a `ChatHistory` table.
* **🧠 Future ML Integrations:** Placeholder templates (CSV dataset, training notebook, pickled models) set up for Logistic Regression intent classification.

---

## 📂 Project Structure

```
smartchat_ai/
├── app.py                      # Flask Application Server (Entry point)
├── chatbot.py                  # Gemini AI Wrapper & Client configuration
├── database.py                 # SQLite database initializer and CRUD scripts
├── voice_input.py              # Server Speech Recognition library wrapper
├── voice_output.py             # Server Text-to-Speech engine wrapper
├── smartchat.db                # SQLite database (created on startup)
│
├── models/                     # ML Artifacts (pickled placeholders)
│   ├── intent_model.pkl
│   └── vectorizer.pkl
│
├── dataset/                    # ML Training Dataset
│   └── intents_dataset.csv
│
├── notebooks/                  # Notebook detailing intent model training
│   └── train_model.ipynb
│
├── templates/                  # Frontend HTML layout
│   └── index.html
│
├── static/                     # Frontend Assets
│   ├── css/
│   │   └── style.css           # Glassmorphic Styling & Animations
│   ├── js/
│   │   └── script.js           # Interactive UI, API Fetch, and Audio API Fallbacks
│   └── temp_audio/             # Generated server-side audio speech files
│
├── requirements.txt            # Package dependencies
└── README.md                   # Setup and usage guide (this file)
```

---

## ⚙️ Setup Instructions

### 1. Prerequisite: Python 3.8+
Ensure Python is installed on your computer. You can check this by running `python --version` in your terminal.

### 2. Clone/Move to Workspace
Navigate to the root project directory:
```powershell
cd "d:\Desktop\SmartChat AI"
```

### 3. Install Dependencies
Run the command below to install all project dependencies from `requirements.txt`:
```powershell
pip install -r requirements.txt
```
> **Note on PyAudio (Optional):** If you wish to use the **Server Microphone** option for Speech Recognition, python requires the `PyAudio` package, which accesses microphone hardware. If you run into installation issues, don't worry: the application defaults to **Browser Recognition** which uses standard HTML5 Web Speech APIs and requires no additional system dependencies.

### 4. Configure Gemini API Key
For the chatbot to answer questions, you must provide a Google Gemini API Key.

**Option A (Recommended): Environment Variable**
Set the key in your terminal/environment:
* **Windows (PowerShell):**
  ```powershell
  $env:GEMINI_API_KEY="your-actual-api-key-here"
  ```
* **Linux/macOS:**
  ```bash
  export GEMINI_API_KEY="your-actual-api-key-here"
  ```

**Option B: Settings Panel**
Alternatively, launch the app and click the **Settings (Gear Icon)** in the sidebar to paste your API Key directly. The key will be stored for your current browser tab session.

---

## 🏃 Running the Application

1. Start the Flask server:
   ```powershell
   python app.py
   ```
2. The server will initialize the SQLite database (`smartchat.db`) and start on local address:
   `http://127.0.0.1:5000/`
3. Open your browser and navigate to `http://127.0.0.1:5000/` to chat!

---

## 🗣️ Voice Configurations

To offer a smooth experience on all devices, the application provides toggles in the **Settings Modal** to choose where speech synthesis and recognition occur:

1. **Browser Engines (Recommended & Default):**
   - Uses Web Audio and Speech recognition built into browsers.
   - Extremely responsive and doesn't block Flask background tasks.
2. **Server Engines:**
   - Speech Recognition captures audio on the server host mic (requires PyAudio).
   - Text-to-Speech uses `pyttsx3` to output audio directly on server hardware, or generates a temporary `.wav` file in `static/temp_audio/` and downloads it to the client.

---

## 🧠 Future Machine Learning Integration

To transition this into a hybrid ML chatbot, we have set up the core structure:
* **`dataset/intents_dataset.csv`**: Contains pre-labeled user phrases mapped to specific intents (e.g. `clear_chat`, `greeting`, `search`).
* **`notebooks/train_model.ipynb`**: Contains a fully detailed notebook outlining the workflow to:
  1. Load the intents dataset.
  2. Compute TF-IDF features from the queries (`TfidfVectorizer`).
  3. Train a `LogisticRegression` classification model.
  4. Save the trained model and vectorizer as pickle binaries (`intent_model.pkl`, `vectorizer.pkl`) inside the `models/` directory.
* **Integration Hooks (`chatbot.py`)**: Comments inside the `ChatbotManager.get_response` method describe how the system will load the pickles and perform classification to intercept or route queries before passing them to the Gemini generative model.
