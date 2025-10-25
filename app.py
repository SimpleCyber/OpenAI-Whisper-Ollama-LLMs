from flask import Flask, request, render_template, jsonify, send_file
import os
import whisper
import json
from datetime import datetime
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "recordings"
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, "audio")
HISTORY_FILE = os.path.join(UPLOAD_FOLDER, "history.json")

os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Model cache
model_cache = r"D:\whisper_models"
os.makedirs(model_cache, exist_ok=True)

# Cache for loaded models
loaded_models = {}

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    file = request.files['audio']
    model_name = request.form.get('model', 'small')
    
    if file:
        # Generate unique ID and filename
        recording_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        
        # Save audio file
        file.save(filepath)
        
        # Get the appropriate model
        model = get_model(model_name)
        
        # Transcribe
        result = model.transcribe(filepath, fp16=False)
        transcription = result["text"]
        
        # Calculate duration (approximate from transcription result)
        duration_seconds = int(result.get("segments", [{}])[-1].get("end", 0)) if result.get("segments") else 0
        duration = f"{duration_seconds // 60}:{duration_seconds % 60:02d}"
        
        # Load history and add new recording
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
        history["recordings"].insert(0, recording_data)  # Add to beginning
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

if __name__ == "__main__":
    app.run(debug=True)