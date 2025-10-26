from flask import Flask, request, render_template, jsonify, send_file
import os
import whisper
import json
from datetime import datetime
import uuid
import requests
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

app = Flask(__name__)
UPLOAD_FOLDER = "recordings"
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, "audio")
TTS_FOLDER = os.path.join(UPLOAD_FOLDER, "tts")
HISTORY_FILE = os.path.join(UPLOAD_FOLDER, "history.json")
CHAT_HISTORY_FILE = os.path.join(UPLOAD_FOLDER, "chat_history.json")

os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(TTS_FOLDER, exist_ok=True)

# Model cache
model_cache = r"D:\whisper_models"
os.makedirs(model_cache, exist_ok=True)

# Cache for loaded models
loaded_models = {}

# Ollama configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
AVAILABLE_OLLAMA_MODELS = ["gemma3:4b", "gemma3:270m"]

# Initialize Chatterbox TTS (load once)
print("🔊 Loading Chatterbox TTS model...")
tts_model = ChatterboxTTS.from_pretrained(device="cpu")  # Change to "cuda" if GPU available
print("✅ TTS model loaded successfully")

# Available TTS voices (Chatterbox supports multiple speakers)
AVAILABLE_VOICES = {
    "default": {"name": "Default Voice", "speaker_id": 0},
    "voice1": {"name": "Voice 1", "speaker_id": 1},
    "voice2": {"name": "Voice 2", "speaker_id": 2},
    "voice3": {"name": "Voice 3", "speaker_id": 3},
}

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

def query_ollama(prompt, context="", model="gemma3:4b"):
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
            "model": model,
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

def generate_tts(text, voice="default"):
    """Generate TTS audio from text"""
    try:
        # Generate audio
        wav = tts_model.generate(text)
        
        # Create unique filename
        tts_filename = f"tts_{uuid.uuid4()}.wav"
        tts_path = os.path.join(TTS_FOLDER, tts_filename)
        
        # Save audio file
        ta.save(tts_path, wav, tts_model.sr)
        
        return tts_path, tts_filename
    except Exception as e:
        print(f"Error generating TTS: {str(e)}")
        return None, None

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

# AI Chat endpoints
@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    """Handle AI chat requests (text or voice)"""
    data = request.json
    user_message = data.get('message', '')
    context = data.get('context', '')
    ollama_model = data.get('model', 'gemma3:4b')
    voice = data.get('voice', 'default')
    enable_tts = data.get('enable_tts', True)
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Query Ollama
    ai_response = query_ollama(user_message, context, ollama_model)
    
    # Generate TTS if enabled
    tts_path = None
    tts_filename = None
    if enable_tts:
        tts_path, tts_filename = generate_tts(ai_response, voice)
    
    # Save to chat history
    chat_history = load_chat_history()
    chat_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "ai_response": ai_response,
        "context": context,
        "model": ollama_model,
        "voice": voice,
        "tts_file": tts_filename if tts_filename else None
    }
    chat_history["chats"].insert(0, chat_entry)
    save_chat_history(chat_history)
    
    return jsonify({
        "response": ai_response,
        "id": chat_entry["id"],
        "tts_file": tts_filename,
        "tts_url": f"/tts/{tts_filename}" if tts_filename else None
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
    ollama_model = data.get('model', 'gemma3:4b')
    voice = data.get('voice', 'default')
    enable_tts = data.get('enable_tts', True)
    
    history = load_history()
    for recording in history["recordings"]:
        if recording["id"] == recording_id:
            transcription = recording["transcription"]
            ai_response = query_ollama(instruction, transcription, ollama_model)
            
            # Generate TTS if enabled
            tts_path = None
            tts_filename = None
            if enable_tts:
                tts_path, tts_filename = generate_tts(ai_response, voice)
            
            return jsonify({
                "response": ai_response,
                "tts_file": tts_filename,
                "tts_url": f"/tts/{tts_filename}" if tts_filename else None
            })
    
    return jsonify({"error": "Recording not found"}), 404

@app.route('/tts/<filename>', methods=['GET'])
def serve_tts(filename):
    """Serve TTS audio files"""
    tts_path = os.path.join(TTS_FOLDER, filename)
    if os.path.exists(tts_path):
        return send_file(tts_path, mimetype='audio/wav')
    return jsonify({"error": "TTS file not found"}), 404

@app.route('/ai/models', methods=['GET'])
def get_available_models():
    """Get available Ollama models"""
    return jsonify({
        "ollama_models": AVAILABLE_OLLAMA_MODELS,
        "voices": AVAILABLE_VOICES
    })

@app.route('/ai/speak', methods=['POST'])
def speak_text():
    """Generate TTS for arbitrary text"""
    data = request.json
    text = data.get('text', '')
    voice = data.get('voice', 'default')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    tts_path, tts_filename = generate_tts(text, voice)
    
    if tts_filename:
        return jsonify({
            "tts_file": tts_filename,
            "tts_url": f"/tts/{tts_filename}"
        })
    else:
        return jsonify({"error": "Failed to generate TTS"}), 500

if __name__ == "__main__":
    app.run(debug=True)