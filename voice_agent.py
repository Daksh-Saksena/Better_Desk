import base64
import subprocess
import threading
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = (
    "You are BetterDesk, a highly intelligent electronics workbench assistant. "
    "You can see the user's workbench and UI. The UI might have bounding boxes, "
    "hand landmarks, and a side panel with component specs. "
    "When asked, describe what you see or answer the user's question. "
    "Be concise, friendly, and conversational. Two or three sentences max."
)

chat_history = []
MAX_HISTORY = 6  # Remember last 3 turns (3 user + 3 assistant)

def analyse(frame_bgr=None, audio_file=None):
    import cv2
    global chat_history
    
    user_text = ""
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, "rb") as f:
            t = _client.audio.transcriptions.create(model="whisper-1", file=f)
            user_text = t.text
    
    if not user_text and frame_bgr is None:
        return "Nothing to analyse."
        
    if not user_text:
        user_text = "What do you see?"

    # Append just the text to our internal chat history for memory
    chat_history.append({"role": "user", "content": user_text})
    if len(chat_history) > MAX_HISTORY:
        chat_history = chat_history[-MAX_HISTORY:]
    
    messages = [{"role": "system", "content": PROMPT}]
    
    # Add historical context (text only, to save tokens/money)
    for msg in chat_history[:-1]:
        messages.append(msg)
        
    # Build current turn
    current_content = [{"type": "text", "text": user_text}]
    if frame_bgr is not None:
        _, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 75])
        b64 = base64.b64encode(buf).decode('ascii')
        current_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})
        
    messages.append({"role": "user", "content": current_content})
    
    resp = _client.chat.completions.create(
        model="gpt-4o",  # Using gpt-4o for better OCR/UI reading, or gpt-4o-mini
        messages=messages,
        max_tokens=150
    )
    
    ans = resp.choices[0].message.content.strip()
    chat_history.append({"role": "assistant", "content": ans})
    if len(chat_history) > MAX_HISTORY:
        chat_history = chat_history[-MAX_HISTORY:]
        
    return ans

def speak(text):
    import requests
    
    api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_LABS_API_KEY") or os.getenv("ELEVENLABS_KEY")
    if not api_key:
        print("No ElevenLabs key found in .env, falling back to Mac TTS")
        subprocess.run(["say", "-v", "Daniel", text])
        return

    # The voice ID you requested is a library voice, which requires a paid plan.
    # Using Charlie (a default 'premade' free voice) so it actually works on your free tier:
    voice_id = "IKne3meq5aSn9XLyUdCD"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2", # Turbo v2 is faster and cheaper
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open("response.mp3", "wb") as f:
            f.write(response.content)
        subprocess.run(["afplay", "response.mp3"])
    else:
        print(f"ElevenLabs Error: {response.text}")
        subprocess.run(["say", "-v", "Daniel", text])

def analyse_and_speak(frame_bgr=None, audio_file=None, on_start=None, on_done=None):
    def _run():
        if on_start: on_start()
        try:
            text = analyse(frame_bgr, audio_file)
            speak(text)
            if on_done: on_done(text)
        except Exception as e:
            msg = f"Error: {e}"
            print(msg)
            speak("Sorry, I couldn't analyse that.")
            if on_done: on_done(msg)
    threading.Thread(target=_run, daemon=True).start()
