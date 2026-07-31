import base64
import subprocess
import threading
import os
import shutil
import platform
import tempfile
import requests
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
try:
    import winsound
except ImportError:
    winsound = None
USE_WINSOUND = True
try:
    import simpleaudio as sa
except Exception:
    sa = None
try:
    from playsound import playsound
except Exception:
    playsound = None
dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path)
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def _powershell_command(command):
    encoded = command.encode("utf-16-le")
    b64 = base64.b64encode(encoded).decode("ascii")
    return ["PowerShell.exe", "-NoProfile", "-EncodedCommand", b64]
def _play_audio_file(path):
    pass
    system = platform.system()
    if system == "Darwin":
        if shutil.which("afplay"):
            result = subprocess.run(["afplay", path], check=False)
            pass
            return result.returncode == 0
        if playsound:
            try:
                pass
                playsound(path)
                return True
            except Exception as e:
                pass
        pass
        return False
    if system == "Windows":
        if path.lower().endswith(".wav"):
            if USE_WINSOUND and winsound:
                pass
                success = winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                pass
                return bool(success)
            if sa:
                try:
                    pass
                    wobj = sa.WaveObject.from_wave_file(path)
                    play_obj = wobj.play()
                    play_obj.wait_done()
                    return True
                except Exception as e:
                    pass
            quoted_path = _powershell_single_quote(path)
            cmd = f"(New-Object Media.SoundPlayer {quoted_path}).PlaySync()"
            result = subprocess.run(_powershell_command(cmd), capture_output=True, text=True)
            pass
            return result.returncode == 0
        if path.lower().endswith(".mp3"):
            pass
            if playsound:
                try:
                    pass
                    playsound(path)
                    return True
                except Exception as e:
                    pass
            if shutil.which("ffplay"):
                pass
                result = subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path], capture_output=True, text=True)
                pass
                return result.returncode == 0
            if _play_mp3_windows(path):
                return True
            pass
            try:
                os.startfile(path)
                return True
            except Exception as e:
                pass
                fallback = subprocess.run(["cmd", "/c", "start", "", path], capture_output=True, text=True)
                pass
                return fallback.returncode == 0
        pass
        try:
            os.startfile(path)
            return True
        except Exception as e:
            pass
            fallback = subprocess.run(["cmd", "/c", "start", "", path], capture_output=True, text=True)
            pass
            return fallback.returncode == 0
    pass
    return False
def _powershell_single_quote(value):
    return "'" + str(value).replace("'", "''") + "'"
def _play_mp3_windows(path):
    quoted_path = _powershell_single_quote(str(Path(path).resolve()))
    cmd = (
        "$player = New-Object -ComObject WMPlayer.OCX; "
        f"$media = $player.newMedia({quoted_path}); "
        "$player.currentPlaylist.appendItem($media); "
        "$player.controls.play(); "
        "while ($player.playState -ne 1 -and $player.playState -ne 0) { Start-Sleep -Milliseconds 200 }"
    )
    result = subprocess.run(_powershell_command(cmd), check=False)
    return result.returncode == 0
def _convert_mp3_to_wav(mp3_path):
    if not shutil.which("ffmpeg"):
        return None
    wav_path = str(Path(mp3_path).with_suffix(".wav"))
    pass
    result = subprocess.run([
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        mp3_path,
        wav_path
    ], check=False)
    if result.returncode == 0 and os.path.exists(wav_path):
        return wav_path
    return None
def _speak_system(text):
    system = platform.system()
    if system == "Darwin" and shutil.which("say"):
        subprocess.run(["say", "-v", "Daniel", text], check=False)
        return True
    if system == "Windows" and shutil.which("PowerShell.exe"):
        quoted = _powershell_single_quote(text)
        cmd = (
            "Add-Type -AssemblyName System.Speech; "
            f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak({quoted})"
        )
        subprocess.run(_powershell_command(cmd), check=False)
        return True
    return False
def _discover_elevenlabs_voice_id(api_key):
    import requests
    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }
    try:
        resp = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        voices = data.get("voices", [])
        if voices:
            voice_id = voices[0].get("voice_id") or voices[0].get("id")
            if voice_id:
                pass
                return voice_id
    except Exception as e:
        pass
    return None
PROMPT = (
    "You are BetterDesk, a highly intelligent electronics workbench assistant. "
    "You can see the user's workbench and UI. The UI might have bounding boxes, "
    "hand landmarks, and a side panel with component specs. "
    "When asked, describe what you see or answer the user's question. "
    "Be concise, friendly, and conversational. Two or three sentences max."
)
chat_history = []
MAX_HISTORY = 6 
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
    chat_history.append({"role": "user", "content": user_text})
    if len(chat_history) > MAX_HISTORY:
        chat_history = chat_history[-MAX_HISTORY:]
    messages = [{"role": "system", "content": PROMPT}]
    for msg in chat_history[:-1]:
        messages.append(msg)
    current_content = [{"type": "text", "text": user_text}]
    if frame_bgr is not None:
        _, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 75])
        b64 = base64.b64encode(buf).decode('ascii')
        current_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})
    messages.append({"role": "user", "content": current_content})
    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=150
    )
    ans = resp.choices[0].message.content.strip()
    chat_history.append({"role": "assistant", "content": ans})
    if len(chat_history) > MAX_HISTORY:
        chat_history = chat_history[-MAX_HISTORY:]
    return ans
def speak(text):
    api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_LABS_API_KEY") or os.getenv("ELEVENLABS_KEY")
    if not api_key:
        pass
        if not _speak_system(text):
            pass
        return
    voice_id = os.getenv("ELEVENLABS_VOICE_ID") or _discover_elevenlabs_voice_id(api_key)
    if not voice_id:
        pass
        if not _speak_system(text):
            pass
        return
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/wav",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "audio_format": "wav",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        pass
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            suffix = ".wav" if "wav" in content_type else ".mp3"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            tmp_path = os.path.abspath(tmp_path)
            pass
            play_path = tmp_path
            if suffix == ".mp3":
                wav_path = _convert_mp3_to_wav(tmp_path)
                if wav_path:
                    play_path = os.path.abspath(wav_path)
                    pass
                else:
                    pass
            if not os.path.exists(play_path) or os.path.getsize(play_path) == 0:
                pass
                raise RuntimeError("Audio file missing after ElevenLabs response")
            if platform.system() == "Windows" and USE_WINSOUND and winsound and play_path.lower().endswith(".wav"):
                try:
                    pass
                    winsound.PlaySound(play_path, winsound.SND_FILENAME | winsound.SND_SYNC)
                    return
                except Exception as e:
                    pass
            _play_audio_file(play_path)
            return
        pass
    except Exception as e:
        pass
    if not _speak_system(text):
        pass
def analyse_and_speak(frame_bgr=None, audio_file=None, on_start=None, on_done=None):
    def _run():
        if on_start:
            on_start()
        try:
            text = analyse(frame_bgr, audio_file)
            speak(text)
            if on_done:
                on_done(text)
        except Exception as e:
            msg = f"Error: {e}"
            pass
            speak("Sorry, I couldn't analyse that.")
            if on_done:
                on_done(msg)
    threading.Thread(target=_run, daemon=True).start()
