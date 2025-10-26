import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

# Load model (GPU recommended, else use "cpu")
model = ChatterboxTTS.from_pretrained(device="cpu")  # or "cpu"

text = "Ezreal and Jinx teamed up with Ahri, Yasuo, and Teemo to take down the enemy's Nexus in an epic late-game pentakill."
wav = model.generate(text)

# Save the output
ta.save("test-english.wav", wav, model.sr)
