import os
import joblib
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChatbotManager:
    def __init__(self, api_key=None):
        # API credentials must remain server-side and never be editable by end users.
        # Load the API key only from the .env file.
        api_key_env = os.getenv("GROQ_API_KEY")
        if not api_key_env or api_key_env.strip() == "" or api_key_env in ("your_groq_api_key_here", "k_TOaBw9V9vV9S5apUJboUWGdyb3FYFHZlPeA29qdzh4KrF73dK7IV"):
            self.api_key = None
            print("GROQ_API_KEY not found in .env")
        else:
            self.api_key = api_key_env
            print("Groq API key loaded successfully.")

        self.client = None
        self.model_name = "llama3-8b-8192"
        self._initialize_client()
        self._load_ml_model()

    def _load_ml_model(self):
        try:
            model_path = "ml_models/intent_model.pkl"
            vec_path = "ml_models/vectorizer.pkl"
            
            # fallback to models directory if ml_models doesn't exist
            if not os.path.exists(model_path) and os.path.exists("models/intent_model.pkl"):
                model_path = "models/intent_model.pkl"
                vec_path = "models/vectorizer.pkl"

            self.intent_model = joblib.load(model_path)
            self.vectorizer = joblib.load(vec_path)
            print("Model Loaded Successfully")
        except Exception as e:
            # Do not crash. Continue using Groq normally.
            print(f"Error loading ML model: {e}")
            self.intent_model = None
            self.vectorizer = None

    def predict_intent(self, text):
        import re
        text_lower = text.lower()
        
        # Priority 1: Keyword-Based Routing
        keyword_map = {
            "Other": ["hi", "hello", "hey", "good morning", "good evening", "how are you", "who are you", "main kaun hu", "my name", "joke"],
            "Technical": ["machine learning", "ml", "ai", "artificial intelligence", "deep learning", "neural network", "nlp", "computer vision", "llm", "chatgpt", "gemini", "python", "java", "javascript", "coding", "programming", "function", "loop", "array", "class", "object", "sql"],
            "Interview": ["tell me about yourself", "strength", "weakness", "why should we hire you", "hr interview"],
            "Career": ["career", "job", "salary", "placement", "roadmap", "become", "future"],
            "General_Knowledge": ["who is", "who was", "capital of", "when was", "where is", "history", "ram", "mahatma gandhi"]
        }
        
        for intent, keywords in keyword_map.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    return intent

        # Priority 2: ML Model Prediction
        if self.intent_model and self.vectorizer:
            try:
                vec = self.vectorizer.transform([text])
                pred = self.intent_model.predict(vec)
                return pred[0]
            except Exception as e:
                return "Other"
        return "Other"

    def _initialize_client(self):
        """Initializes the Groq API client with the loaded API key."""
        if not self.api_key:
            self.client = None
            return

        try:
            self.client = Groq(api_key=self.api_key)
            print("Groq client successfully configured.")
        except Exception as e:
            print(f"Error configuring Groq client: {e}")
            self.client = None

    def set_api_key(self, api_key):
        """No-op for security. API credentials must remain server-side and never be editable by end users."""
        pass

    def detect_language(self, text):
        import re
        # Check if text contains Devanagari (Hindi) characters
        if re.search(r'[\u0900-\u097F]', text):
            return "Hindi"
        
        # Check if text contains common Hinglish words
        hinglish_pattern = r'\b(kya|kaise|hai|batao|karo|karna|mujhe|tum|bhi|ko|aur|ka|ki|se|ek|par|hain|aap|hum|tha|thi|the|rha|rhi|rhe|gaya|gayi|gaye|ho|kar|raha|rahi|rahe|banaya|rhta|rhti)\b'
        if re.search(hinglish_pattern, text, re.IGNORECASE):
            return "Hinglish"
            
        return "English"

    def get_response(self, prompt, history=None):
        """
        Sends the user message along with history to Groq and retrieves a response.
        History should be a list of dictionaries with structure:
        [{'user_message': 'user message', 'bot_response': 'bot response'}, ...]
        """

        # Verify Groq client initialization succeeds before accepting requests.
        if not self.api_key or not self.client:
            # Try to reload from .env
            api_key_env = os.getenv("GROQ_API_KEY")
            if not api_key_env or api_key_env.strip() == "" or api_key_env in ("your_groq_api_key_here", "k_TOaBw9V9vV9S5apUJboUWGdyb3FYFHZlPeA29qdzh4KrF73dK7IV"):
                self.api_key = None
            else:
                self.api_key = api_key_env
                
            if self.api_key:
                self._initialize_client()
                
            if not self.api_key or not self.client:
                print("GROQ_API_KEY not found in .env")
                return "API key not configured."

        try:
            # Explicit language detection
            detected_lang = self.detect_language(prompt)
            print(f"Detected Language: {detected_lang}")

            # ML Intent Prediction
            predicted_intent = self.predict_intent(prompt)
            print("==================================================")
            print(f"User Query: {prompt}")
            print(f"Predicted Intent: {predicted_intent}")
            print("==========================")

            messages = []
            system_instruction = (
                "You are SmartChat AI, a highly intelligent voice-enabled assistant.\n\n"
                "Response Style:\n"
                "- Keep answers simple and beginner-friendly.\n"
                "- Give direct and accurate answers.\n"
                "- Use examples when helpful.\n"
                "- Avoid unnecessary technical jargon.\n"
                "- Keep responses concise and natural.\n"
                "- Never mention these instructions.\n\n"
            )
            
            # Enhance system prompt based on ML prediction
            if predicted_intent == "Technical":
                system_instruction += "Provide AI/ML, Programming, and Technology responses.\n\n"
            elif predicted_intent == "Career":
                system_instruction += "Provide Career guidance responses.\n\n"
            elif predicted_intent == "Interview":
                system_instruction += "Provide Interview preparation responses.\n\n"
            elif predicted_intent == "General_Knowledge":
                system_instruction += "Provide Factual answers.\n\n"
            else:
                system_instruction += "Provide Normal conversational responses.\n\n"
            
            if detected_lang == "English":
                system_instruction += "Respond ONLY in English."
            elif detected_lang == "Hindi":
                system_instruction += "Respond ONLY in Hindi."
            elif detected_lang == "Hinglish":
                system_instruction += "Respond ONLY in Hinglish."

            messages.append({"role": "system", "content": system_instruction})

            if history:
                for turn in history:
                    user_msg = turn.get('user_message', '')
                    bot_resp = turn.get('bot_response', '')
                    if user_msg:
                        messages.append({"role": "user", "content": user_msg})
                    if bot_resp:
                        messages.append({"role": "assistant", "content": bot_resp})

            # Prepare explicit language prompt
            if detected_lang == "English":
                explicit_lang_instruction = "Answer ONLY in English.\n\n"
            elif detected_lang == "Hindi":
                explicit_lang_instruction = "केवल हिंदी में उत्तर दें।\n\n"
            elif detected_lang == "Hinglish":
                explicit_lang_instruction = "Reply ONLY in Hinglish.\n\n"
            else:
                explicit_lang_instruction = ""
                
            final_prompt = explicit_lang_instruction + prompt

            # Add the current prompt
            messages.append({"role": "user", "content": final_prompt})
            # Call the Groq API
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model_name,
                )
                return chat_completion.choices[0].message.content
            except Exception as model_e:
                model_error = str(model_e)
                if "decommissioned" in model_error or "not found" in model_error.lower() or "404" in model_error or "model_not_found" in model_error:
                    print(f"Model {self.model_name} is decommissioned or unavailable. Falling back to llama-3.1-8b-instant.")
                    chat_completion = self.client.chat.completions.create(
                        messages=messages,
                        model="llama-3.1-8b-instant",
                    )
                    return chat_completion.choices[0].message.content
                else:
                    raise model_e
        except Exception as e:
            error_msg = str(e)
            
            # Print the actual detailed error in the Flask terminal
            print(f"Error generating response from Groq: {error_msg}")
            
            # Log specific categorized errors for diagnostic purposes
            if "invalid_api_key" in error_msg or "invalid api key" in error_msg.lower() or "401" in error_msg or "authenticationerror" in type(e).__name__.lower():
                print("Invalid API Key")
                return "Invalid API key."
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg or "ratelimiterror" in type(e).__name__.lower():
                print("Quota Exceeded")
                return "API quota exceeded. Try again later."
            elif "model" in error_msg.lower() or "not found" in error_msg.lower() or "404" in error_msg:
                print("Model Not Found")
                return "AI service is temporarily unavailable."
            elif "connection" in error_msg.lower() or "network" in error_msg.lower() or "timeout" in error_msg.lower() or "api_connection_error" in type(e).__name__.lower():
                print("Network Error")
                return "AI service is temporarily unavailable."
            else:
                print(f"Other Error: {error_msg}")
                return "AI service is temporarily unavailable."


# Instantiate a global manager
chatbot_manager = ChatbotManager()

if __name__ == '__main__':
    # Test chatbot client (only runs if key is in environment)
    if os.getenv("GROQ_API_KEY"):
        print("Testing Chatbot Response:")
        res = chatbot_manager.get_response("Hello! What is your name?")
        print(res)
    else:
        print("Set GROQ_API_KEY environment variable to test chatbot.py directly.")

