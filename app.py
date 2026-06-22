import os
import uuid
import glob
import joblib
from flask import Flask, render_template, request, jsonify, send_from_directory
from database import init_db, save_chat, get_chat_history, clear_chat_history, delete_conversation_by_message, check_conversation_exists, delete_conversation_by_id
from chatbot import chatbot_manager
from voice_input import voice_input_manager
from voice_output import voice_output_manager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load ML Model
intent_model = None
vectorizer = None
model_status = "🔴 Inactive"

try:
    model_path = 'ml_models/intent_model.pkl'
    vec_path = 'ml_models/vectorizer.pkl'
    if not os.path.exists(model_path) and os.path.exists('models/intent_model.pkl'):
        model_path = 'models/intent_model.pkl'
        vec_path = 'models/vectorizer.pkl'

    intent_model = joblib.load(model_path)
    vectorizer = joblib.load(vec_path)
    model_status = "🟢 Active"
except Exception as e:
    print(f"Error loading ML model: {e}")

def predict_intent(user_message):
    if intent_model and vectorizer:
        try:
            vec = vectorizer.transform([user_message])
            pred = intent_model.predict(vec)
            return pred[0]
        except Exception as e:
            print(f"Error predicting intent: {e}")
            return "Other"
    return "Other"

# Configure temporary directories
TEMP_AUDIO_DIR = os.path.join(app.root_path, 'static', 'temp_audio')
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

def cleanup_old_audio():
    """Helper to clean up generated TTS audio files from static folder."""
    try:
        for ext in ["*.wav", "*.mp3"]:
            files = glob.glob(os.path.join(TEMP_AUDIO_DIR, ext))
            for f in files:
                try:
                    os.remove(f)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error during audio cleanup: {e}")

# Initialize the SQLite database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main endpoint for sending a message.
    Accepts JSON containing 'message' and optionally a client-side 'speak' boolean.
    """
    data = request.json or {}
    user_message = data.get('message', '').strip()
    speak = data.get('speak', False)
    
    if not user_message:
        return jsonify({'error': 'Message content cannot be empty.'}), 400
    
    # Retrieve current history to pass context
    db_history = get_chat_history(limit=10)
    
    # Call Gemini wrapper to get answer
    bot_response = chatbot_manager.get_response(user_message, history=db_history)
    
    # Save the conversation to the SQLite database
    save_chat(user_message, bot_response)
    
    # ML Prediction
    predicted_intent = predict_intent(user_message)
    
    # Trigger Python-side Speech Output on server if requested (disabled to prevent duplicate playback)
    # if speak:
    #     voice_output_manager.speak_text(bot_response)

    return jsonify({
        'user_message': user_message,
        'bot_response': bot_response,
        'predicted_intent': predicted_intent,
        'model_status': model_status,
        'status': 'success'
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns the chat history database contents."""
    history = get_chat_history(limit=50)
    return jsonify({'history': history})

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clears all entries in the chat database."""
    success = clear_chat_history()
    cleanup_old_audio()
    if success:
        return jsonify({'status': 'success', 'message': 'Chat history cleared.'})
    return jsonify({'status': 'error', 'message': 'Failed to clear chat history.'}), 500

@app.route('/api/delete-item/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Deletes a specific conversation item by its database ID."""
    try:
        app.logger.info(f"Received request to delete conversation ID: {item_id}")
        
        # Verify the conversation exists before deletion
        if not check_conversation_exists(item_id):
            app.logger.warning(f"Conversation ID {item_id} not found for deletion.")
            return jsonify({
                "success": False,
                "message": "Conversation not found"
            }), 404
            
        success = delete_conversation_by_id(item_id)
        if success:
            app.logger.info(f"Conversation ID {item_id} successfully deleted.")
            return jsonify({
                "success": True,
                "message": "Conversation deleted successfully"
            }), 200
        else:
            app.logger.error(f"Failed to delete conversation ID {item_id} from database.")
            return jsonify({
                "success": False,
                "message": "Failed to delete conversation from database"
            }), 500
            
    except Exception as e:
        app.logger.exception(f"Exception occurred while deleting conversation ID {item_id}: {e}")
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route('/api/voice-input-mic', methods=['POST'])
def voice_input_mic():
    """
    Triggers the server-side microphone to listen using SpeechRecognition.
    Suitable for local desktop testing.
    """
    result = voice_input_manager.listen_from_mic()
    return jsonify(result)

@app.route('/api/voice-file', methods=['POST'])
def voice_file():
    """
    Accepts an uploaded audio file from the client, transcribes it, 
    and returns the transcribed text.
    """
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file uploaded.'}), 400
        
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename.'}), 400

    # Save to a temporary WAV path
    temp_filename = f"upload_{uuid.uuid4().hex}.wav"
    temp_filepath = os.path.join(TEMP_AUDIO_DIR, temp_filename)
    
    try:
        audio_file.save(temp_filepath)
        
        # Transcribe audio file using SpeechRecognition
        transcription_result = voice_input_manager.transcribe_audio_file(temp_filepath)
        
        # Cleanup uploaded file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            
        return jsonify(transcription_result)
    except Exception as e:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return jsonify({'success': False, 'error': f'Failed to process file: {str(e)}'}), 500

@app.route('/api/tts', methods=['POST'])
def generate_tts():
    """
    Converts a response string to an MP3 audio file on the server using Edge-TTS,
    and returns the URL of the generated file for client playback.
    """
    data = request.json or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided for text-to-speech.'}), 400
        
    # Generate unique filename for this speech output
    filename = f"speech_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(TEMP_AUDIO_DIR, filename)
    
    # Render audio using Edge-TTS
    success = voice_output_manager.save_speech_to_file(text, filepath)
    
    if success:
        return jsonify({
            'success': True,
            'audio_url': f'/static/temp_audio/{filename}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to synthesize audio on server.'
        }), 500

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Allows updating API settings dynamically. Custom API keys are ignored for security."""
    return jsonify({'success': True, 'message': 'Settings updated on server. Custom API keys are disabled.'})

if __name__ == '__main__':
    # Cleanup any leftovers on startup
    cleanup_old_audio()
    # Run the server locally
    app.run(debug=True, port=5000)
