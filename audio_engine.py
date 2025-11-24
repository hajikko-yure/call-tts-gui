import sounddevice as sd
import numpy as np
import wave
import io
import requests
import json
from scipy.signal import resample
import os
import threading
import subprocess
import time
import shutil

class VoiceVoxPlayer:
    def __init__(self, voicevox_url="http://127.0.0.1:50021"):
        self.voicevox_url = voicevox_url
        self.output_device_index = None
        self.output_sample_rate = 48000
        
        # Voice Parameters
        self.speed_scale = 1.0
        self.volume_scale = 1.0
        self.pitch_scale = 0.0
        
        # Asset path
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.asset_dir = os.path.join(self.base_dir, "asset")
        self.se_json_path = os.path.join(self.base_dir, "se.json")
        
        if not os.path.exists(self.asset_dir):
            os.makedirs(self.asset_dir)

        self._load_se_map()
        
        # Paths
        self.VOICEVOX_PATH = r"C:\Program Files\VOICEVOX\VOICEVOX.exe"
        self.VOICEMEETER_PATH = r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeter_x64.exe"

    def _load_se_map(self):
        self.se_map = {}
        # Try load from json
        if os.path.exists(self.se_json_path):
            try:
                with open(self.se_json_path, 'r', encoding='utf-8') as f:
                    self.se_map = json.load(f)
            except Exception as e:
                print(f"Error loading se.json: {e}")
        
        # If empty (first run or deleted), scan asset dir
        if not self.se_map:
            for filename in os.listdir(self.asset_dir):
                if filename.lower().endswith(".wav"):
                    name = os.path.splitext(filename)[0]
                    self.se_map[name] = os.path.join(self.asset_dir, filename)
            self._save_se_map()

    def _save_se_map(self):
        try:
            with open(self.se_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.se_map, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving se.json: {e}")

    def add_se(self, name, path):
        """Adds a new SE, copying the file to the asset directory."""
        try:
            filename = os.path.basename(path)
            dest_path = os.path.join(self.asset_dir, filename)
            
            # Copy if not already there (and not same file)
            if os.path.abspath(path) != os.path.abspath(dest_path):
                shutil.copy2(path, dest_path)
            
            self.se_map[name] = dest_path
            self._save_se_map()
            return True
        except Exception as e:
            print(f"Error adding SE: {e}")
            return False

    def remove_se(self, name):
        """Removes an SE from the map."""
        if name in self.se_map:
            del self.se_map[name]
            self._save_se_map()
            return True
        return False

    def get_output_devices(self):
        """Returns a list of output devices."""
        devices = sd.query_devices()
        output_devices = []
        for i, dev in enumerate(devices):
            if dev['max_output_channels'] > 0:
                output_devices.append((i, dev['name'], dev['hostapi']))
        return output_devices

    def set_output_device(self, index):
        """Sets the output device by index."""
        self.output_device_index = index
        self.output_sample_rate = 48000 

    def get_speakers(self):
        """Fetches available speakers from Voicevox."""
        try:
            response = requests.get(f"{self.voicevox_url}/speakers", timeout=2)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return []

    def stop(self):
        """Stops current playback."""
        sd.stop()

    def play_se(self, name, on_start=None, on_complete=None):
        """Plays a sound effect in a separate thread."""
        if name in self.se_map:
            self.stop()
            threading.Thread(target=self._play_wave_file, args=(self.se_map[name], on_start, on_complete), daemon=True).start()
        else:
            print(f"SE not found: {name}")

    def speak(self, text, speaker_id, on_start=None, on_complete=None):
        """Synthesizes and plays speech in a separate thread."""
        self.stop()
        threading.Thread(target=self._synthesize_and_play, args=(text, speaker_id, on_start, on_complete), daemon=True).start()

    def _play_wave_file(self, path, on_start=None, on_complete=None):
        try:
            with wave.open(path, 'rb') as wf:
                rate = wf.getframerate()
                channels = wf.getnchannels()
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                
                audio = self._process_audio(audio, channels, rate)
                
                if on_start:
                    on_start()
                
                sd.play(audio, samplerate=self.output_sample_rate, device=self.output_device_index)
                sd.wait()
                
                if on_complete:
                    on_complete()
        except Exception as e:
            print(f"Error playing SE: {e}")
            if on_complete:
                on_complete()

    def _synthesize_and_play(self, text, speaker_id, on_start=None, on_complete=None):
        try:
            # Audio Query
            query_res = requests.post(
                f"{self.voicevox_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
                timeout=10
            )
            if query_res.status_code != 200:
                print(f"Voicevox Query Error: {query_res.text}")
                if on_complete: on_complete()
                return
            
            query = query_res.json()
            
            # Apply Voice Parameters
            query["speedScale"] = self.speed_scale
            query["volumeScale"] = self.volume_scale
            query["pitchScale"] = self.pitch_scale

            # Synthesis
            audio_res = requests.post(
                f"{self.voicevox_url}/synthesis",
                params={"speaker": speaker_id},
                data=json.dumps(query),
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if audio_res.status_code != 200:
                print(f"Voicevox Synthesis Error: {audio_res.text}")
                if on_complete: on_complete()
                return

            with wave.open(io.BytesIO(audio_res.content), 'rb') as wf:
                original_rate = wf.getframerate()
                channels = wf.getnchannels()
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)

                audio = self._process_audio(audio, channels, original_rate)
                
                # Add 1 second of silence
                silence_duration = 1.0
                silence_samples = int(self.output_sample_rate * silence_duration)
                if channels == 2:
                    silence = np.zeros((silence_samples, 2), dtype=np.int16)
                else:
                    silence = np.zeros((silence_samples, 1), dtype=np.int16)
                
                audio = np.concatenate([audio, silence])

                if on_start:
                    on_start()

                sd.play(audio, samplerate=self.output_sample_rate, device=self.output_device_index)
                sd.wait()
                
                if on_complete:
                    on_complete()

        except Exception as e:
            print(f"Error in TTS: {e}")
            if on_complete:
                on_complete()

    def _process_audio(self, audio, channels, input_rate):
        # Reshape
        if channels == 2:
            audio = audio.reshape(-1, 2)
        else:
            audio = audio.reshape(-1, 1)

        # Resample if needed
        if input_rate != self.output_sample_rate:
            num_samples = int(len(audio) * self.output_sample_rate / input_rate)
            audio = resample(audio, num_samples)
            audio = np.clip(audio, -32768, 32767).astype(np.int16)
        
        return audio

    def is_process_running(self, process_name):
        try:
            # Simple check using tasklist
            output = subprocess.check_output('tasklist', shell=True).decode('shift_jis', errors='ignore')
            return process_name.lower() in output.lower()
        except:
            return False

    def check_and_launch_apps(self, ask_permission_callback):
        """
        Checks for Voicevox and Voicemeeter.
        ask_permission_callback(app_name) -> bool
        Returns True if all good, False if failed/cancelled.
        """
        apps = [
            ("VOICEVOX", "VOICEVOX.exe", self.VOICEVOX_PATH),
            ("Voicemeeter", "voicemeeter_x64.exe", self.VOICEMEETER_PATH) # Check x64
        ]
        
        for name, exe, path in apps:
            if not self.is_process_running(exe):
                if name == "Voicemeeter" and self.is_process_running("voicemeeter.exe"):
                    continue

                if ask_permission_callback(name):
                    try:
                        subprocess.Popen(path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        wait_time = 15 if name == "VOICEVOX" else 5
                        time.sleep(wait_time) 
                    except Exception as e:
                        print(f"Failed to launch {name}: {e}")
                        return False
                else:
                    return False
        return True
