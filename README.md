# 🎙️ Voice Recorder with AI Transcription

A beautiful, modern voice recording application with real-time transcription using OpenAI's Whisper AI model. Features a minimalist UI with dark/light mode, recording history, and multiple model support.

<img width="1919" height="920" alt="image" src="https://github.com/user-attachments/assets/31815fd5-a350-4aba-bb26-a452b360361a" />



## ✨ Features

- **High-Quality Audio Recording** - Record, pause, resume, and stop with intuitive controls
- **AI-Powered Transcription** - Automatic speech-to-text using OpenAI Whisper
- **Multiple Model Support** - Choose from different Whisper models (tiny, base, small, medium)

## 🎨 Whisper Models ( used )

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny.en` | ~79 MB | Fastest | Dull |
| `small` | ~544 MB | Fast | Good |


## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SimpleCyber/OpenAI-Whisper-Ollama-LLMs.git
cd OpenAI-Whisper-Ollama-LLMs
```

### 2. Install Dependencies

#### Install Whisper and PyTorch

```bash
pip install git+https://github.com/openai/whisper.git
pip install torch
```

#### Install Flask

```bash
pip install flask
```

### 3. Configure Model Cache Path (Optional)

Edit `app.py` and update the model cache path if needed:

```python
model_cache = r"D:\whisper_models"  # Change to your preferred location
```


## 🎯 Usage

### 1. Start the Application

```bash
python app.py
```

The server will start at `http://127.0.0.1:5000`

### 2. Open in Browser

Navigate to `http://localhost:5000` in your web browser.

### 3. Select a Model

- Click the model dropdown in the top-right corner
- Choose your preferred Whisper model
- First-time model usage will download it automatically

### 4. Record Audio

1. **Start Recording** - Click the microphone button
2. **Pause/Resume** - Use pause/resume buttons during recording
3. **Stop** - Click stop when finished
4. **Wait for Transcription** - The AI will process and display the text

### 5. View History

- Click the hamburger menu (☰) to open the sidebar
- See all your past recordings with timestamps
- Click any recording to view full details
- Download audio files from the detail modal



## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - AI transcription model
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Tailwind CSS](https://tailwindcss.com/) - UI styling
- [Font Awesome](https://fontawesome.com/) - Icons
- [Pattern Craft](https://patterncraft.fun) - Background


---

Made with ❤️ by SimpleCyber
