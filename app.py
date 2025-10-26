from flask import Flask, request, render_template, jsonify, send_file
import os
import whisper
import json
from datetime import datetime
import uuid
import requests

app = Flask(__name__)
UPLOAD_FOLDER = "recordings"
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, "audio")
HISTORY_FILE = os.path.join(UPLOAD_FOLDER, "history.json")
CHAT_HISTORY_FILE = os.path.join(UPLOAD_FOLDER, "chat_history.json")

os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Model cache
model_cache = r"D:\whisper_models"
os.makedirs(model_cache, exist_ok=True)

# Cache for loaded models
loaded_models = {}

# Ollama configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"  # Using your installed model

def get_model(model_name):
    """Load and cache Whisper models"""
    if model_name not in loaded_models:
        print(f"🔊 Loading Whisper model: {model_name}...")
        loaded_models[model_name] = whisper.load_model(model_name, download_root=model_cache)
    return loaded_models[model_name]

# Load default model
print("🔊 Loading default Whisper model...")
get_model("small")

# Load or initialize history
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"recordings": []}

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"chats": []}

def save_chat_history(chat_history):
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(chat_history, f, indent=2, ensure_ascii=False)

def query_ollama(prompt, context=""):
    """Query Ollama API with streaming disabled for simplicity"""
    try:
        system_prompt = """You are a helpful AI assistant. You can:
1. Reformat and improve text (emails, notes, templates, etc.)
2. Generate new content based on user requests
3. Answer questions and help with various tasks

Be concise, helpful, and professional."""

        full_prompt = f"{system_prompt}\n\n"
        if context:
            full_prompt += f"Context/Previous transcription:\n{context}\n\n"
        full_prompt += f"User request: {prompt}"

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False
        }

        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "No response from AI")
        else:
            return f"Error: Ollama API returned status {response.status_code}"
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    file = request.files['audio']
    model_name = request.form.get('model', 'small')
    
    if file:
        recording_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        
        file.save(filepath)
        
        model = get_model(model_name)
        result = model.transcribe(filepath, fp16=False)
        transcription = result["text"]
        
        duration_seconds = int(result.get("segments", [{}])[-1].get("end", 0)) if result.get("segments") else 0
        duration = f"{duration_seconds // 60}:{duration_seconds % 60:02d}"
        
        history = load_history()
        recording_data = {
            "id": recording_id,
            "filename": filename,
            "audio_path": filepath,
            "transcription": transcription,
            "timestamp": timestamp,
            "duration": duration,
            "language": result.get("language", "unknown"),
            "model": model_name
        }
        history["recordings"].insert(0, recording_data)
        save_history(history)
        
        return jsonify({
            "transcription": transcription,
            "id": recording_id,
            "filename": filename,
            "model": model_name
        })
    return jsonify({"error": "No file received"}), 400

@app.route('/history', methods=['GET'])
def get_history():
    history = load_history()
    return jsonify(history)

@app.route('/recording/<recording_id>', methods=['GET'])
def get_recording(recording_id):
    history = load_history()
    for recording in history["recordings"]:
        if recording["id"] == recording_id:
            return jsonify(recording)
    return jsonify({"error": "Recording not found"}), 404

@app.route('/download/<recording_id>', methods=['GET'])
def download_recording(recording_id):
    history = load_history()
    for recording in history["recordings"]:
        if recording["id"] == recording_id:
            return send_file(recording["audio_path"], as_attachment=True)
    return jsonify({"error": "Recording not found"}), 404

@app.route('/delete/<recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    history = load_history()
    updated_recordings = []
    deleted = False

    for recording in history["recordings"]:
        if recording["id"] == recording_id:
            if os.path.exists(recording["audio_path"]):
                os.remove(recording["audio_path"])
            deleted = True
        else:
            updated_recordings.append(recording)

    if deleted:
        history["recordings"] = updated_recordings
        save_history(history)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Recording not found"}), 404

# New AI Chat endpoints
@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    """Handle AI chat requests (text or voice)"""
    data = request.json
    user_message = data.get('message', '')
    context = data.get('context', '')  # Optional: transcription to reformat
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Query Ollama
    ai_response = query_ollama(user_message, context)
    
    # Save to chat history
    chat_history = load_chat_history()
    chat_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "ai_response": ai_response,
        "context": context
    }
    chat_history["chats"].insert(0, chat_entry)
    save_chat_history(chat_history)
    
    return jsonify({
        "response": ai_response,
        "id": chat_entry["id"]
    })

@app.route('/ai/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    chat_history = load_chat_history()
    return jsonify(chat_history)

@app.route('/ai/reformat/<recording_id>', methods=['POST'])
def reformat_recording(recording_id):
    """Reformat a specific recording's transcription"""
    data = request.json
    instruction = data.get('instruction', 'Reformat this text to be more professional and clear')
    
    history = load_history()
    for recording in history["recordings"]:
        if recording["id"] == recording_id:
            transcription = recording["transcription"]
            ai_response = query_ollama(instruction, transcription)
            return jsonify({"response": ai_response})
    
    return jsonify({"error": "Recording not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)