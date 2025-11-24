import customtkinter as ctk
from tkinter import messagebox, filedialog
from audio_engine import VoiceVoxPlayer
import threading
import datetime
from PIL import Image, ImageDraw
import os
import json

# --- Theme Configuration ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue") 

# Strict 5-Color Palette & LINE Colors
COLORS = {
    "white": "#FFFFFF",
    "text": "#37474F",        # Dark Grey
    "accent": "#B2DFDB",      # Soft Teal
    "accent_hover": "#80CBC4",
    "alert": "#FFCDD2",       # Soft Red
    "alert_hover": "#EF9A9A",
    "transparent": "transparent",
    "chat_bg": "#99BADD",     # LINE Sky Blue
    "bubble_user": "#8DE055", # LINE Green
    "bubble_se": "#ECEFF1",   # Light Grey
    "input_bg": "#F5F5F5",    # Light Grey for Input Bar
    "send_icon": "#4D73FF",   # LINE Blue for Send Icon
    "stop_icon": "#FF5252"    # Red for Stop Icon
}

# Professional Fonts
FONTS = {
    "main": ("Yu Gothic UI", 14),
    "bold": ("Yu Gothic UI", 14, "bold"),
    "title": ("Yu Gothic UI", 28, "bold"),
    "subtitle": ("Yu Gothic UI", 10),
    "small": ("Yu Gothic UI", 12),
    "status": ("Yu Gothic UI", 16, "bold"),
    "chat": ("Yu Gothic UI", 13)
}

class VLiveCTKApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VLive Controller")
        self.geometry("1050x700")
        
        self.engine = VoiceVoxPlayer()
        self.devices = []
        self.speakers = []
        self.current_speaker_id = None
        self.history_list = []
        self.delete_mode = False
        
        # Load Config
        self.config = self._load_config()

        # Load Background
        self.bg_image = None
        self._load_background()

        # Generate Icons
        self._create_icons()

        self._init_ui()
        
        # Apply Config Defaults
        self._apply_config()
        
        # Startup Check
        self.after(100, self._startup_check)

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        default_config = {
            "voicevox_url": "http://127.0.0.1:50021",
            "default_speed": 1.0,
            "default_volume": 1.0,
            "default_pitch": 0.0,
            "default_speaker_name": "ずんだもん",
            "default_speaker_style": "ノーマル"
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return {**default_config, **json.load(f)}
            except Exception as e:
                print(f"Config load error: {e}")
        return default_config

    def _load_background(self):
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "asset", "bg.png")
            if os.path.exists(bg_path):
                pil_image = Image.open(bg_path)
                self.bg_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(1200, 800))
        except Exception as e:
            print(f"Failed to load background: {e}")

    def _create_icons(self):
        # 1. Send Icon (Paper Plane)
        size = (40, 40)
        send_img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(send_img)
        # Draw a simple paper plane shape
        # Points: Tip(35, 20), TailLeft(5, 5), TailCenter(10, 20), TailRight(5, 35)
        points = [(35, 20), (5, 5), (10, 20), (5, 35)]
        draw.polygon(points, fill=COLORS["send_icon"])
        self.icon_send = ctk.CTkImage(light_image=send_img, dark_image=send_img, size=(25, 25))

        # 2. Stop Icon (Square)
        stop_img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(stop_img)
        # Draw a rounded square
        draw.rounded_rectangle((5, 5, 35, 35), radius=5, fill=COLORS["stop_icon"])
        self.icon_stop = ctk.CTkImage(light_image=stop_img, dark_image=stop_img, size=(25, 25))

    def _init_ui(self):
        # Background Label
        if self.bg_image:
            self.bg_label = ctk.CTkLabel(self, text="", image=self.bg_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Main Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Sidebar (Settings) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=20, fg_color=COLORS["white"], border_width=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(20, 10), pady=20)
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # Logo / Title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="VLive", font=FONTS["title"], text_color=COLORS["text"])
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 0))
        
        self.subtitle_label = ctk.CTkLabel(self.sidebar_frame, text="ずんだもんで通話するアプリ\n©はじっこゆーれー", font=FONTS["subtitle"], text_color="#78909C")
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Device Selection
        self.device_label = ctk.CTkLabel(self.sidebar_frame, text="出力デバイス", anchor="w", font=FONTS["bold"], text_color=COLORS["text"])
        self.device_label.grid(row=2, column=0, padx=25, pady=(10, 5), sticky="w")
        self.device_option = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            command=self._on_device_change,
            fg_color=COLORS["white"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["white"],
            dropdown_text_color=COLORS["text"],
            font=FONTS["main"],
            width=230,
            height=35
        )
        self.device_option.grid(row=3, column=0, padx=20, pady=(0, 15))

        # Character Selection
        self.speaker_label = ctk.CTkLabel(self.sidebar_frame, text="キャラクター", anchor="w", font=FONTS["bold"], text_color=COLORS["text"])
        self.speaker_label.grid(row=4, column=0, padx=25, pady=(10, 5), sticky="w")
        self.speaker_option = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            command=self._on_speaker_change,
            fg_color=COLORS["white"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["white"],
            dropdown_text_color=COLORS["text"],
            font=FONTS["main"],
            width=230,
            height=35
        )
        self.speaker_option.grid(row=5, column=0, padx=20, pady=(0, 20))

        # Voice Settings
        self.settings_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.settings_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        # Speed
        self.speed_label_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.speed_label_frame.pack(fill="x")
        ctk.CTkLabel(self.speed_label_frame, text="話速", font=FONTS["small"], text_color=COLORS["text"]).pack(side="left")
        self.speed_val_label = ctk.CTkLabel(self.speed_label_frame, text="1.00", font=FONTS["small"], text_color=COLORS["text"])
        self.speed_val_label.pack(side="right")
        
        self.speed_slider = ctk.CTkSlider(self.settings_frame, from_=0.5, to=2.0, number_of_steps=15, command=self._on_voice_param_change, button_color=COLORS["accent"], progress_color=COLORS["accent"])
        self.speed_slider.pack(fill="x", pady=(0, 10))

        # Volume
        self.volume_label_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.volume_label_frame.pack(fill="x")
        ctk.CTkLabel(self.volume_label_frame, text="音量", font=FONTS["small"], text_color=COLORS["text"]).pack(side="left")
        self.volume_val_label = ctk.CTkLabel(self.volume_label_frame, text="1.00", font=FONTS["small"], text_color=COLORS["text"])
        self.volume_val_label.pack(side="right")

        self.volume_slider = ctk.CTkSlider(self.settings_frame, from_=0.0, to=2.0, number_of_steps=20, command=self._on_voice_param_change, button_color=COLORS["accent"], progress_color=COLORS["accent"])
        self.volume_slider.pack(fill="x", pady=(0, 10))

        # Pitch
        self.pitch_label_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.pitch_label_frame.pack(fill="x")
        ctk.CTkLabel(self.pitch_label_frame, text="高さ", font=FONTS["small"], text_color=COLORS["text"]).pack(side="left")
        self.pitch_val_label = ctk.CTkLabel(self.pitch_label_frame, text="0.00", font=FONTS["small"], text_color=COLORS["text"])
        self.pitch_val_label.pack(side="right")

        self.pitch_slider = ctk.CTkSlider(self.settings_frame, from_=-0.15, to=0.15, number_of_steps=30, command=self._on_voice_param_change, button_color=COLORS["accent"], progress_color=COLORS["accent"])
        self.pitch_slider.pack(fill="x", pady=(0, 10))


        # --- Main Content Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 20), pady=20)
        self.main_frame.grid_columnconfigure(0, weight=3) 
        self.main_frame.grid_columnconfigure(1, weight=2) 
        self.main_frame.grid_rowconfigure(0, weight=0) # Status
        self.main_frame.grid_rowconfigure(1, weight=1) # Content

        # 1. Status Banner (Top)
        self.status_frame = ctk.CTkFrame(self.main_frame, height=60, fg_color=COLORS["white"], corner_radius=15)
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.now_playing_label = ctk.CTkLabel(
            self.status_frame, 
            text="準備完了", 
            font=FONTS["status"], 
            text_color=COLORS["text"]
        )
        self.now_playing_label.grid(row=0, column=0, pady=15)

        # 2. Left Column: Chat Interface (History + Input)
        self.left_col = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.left_col.grid(row=1, column=0, sticky="nsew", padx=(0, 15))
        self.left_col.grid_rowconfigure(0, weight=1) # History (Scrollable)
        self.left_col.grid_rowconfigure(1, weight=0) # Input (Fixed)
        self.left_col.grid_columnconfigure(0, weight=1)

        # Chat History (Scrollable)
        self.chat_history_frame = ctk.CTkScrollableFrame(self.left_col, fg_color=COLORS["chat_bg"], corner_radius=20, label_text="トーク履歴", label_font=FONTS["bold"], label_fg_color=COLORS["transparent"], label_text_color=COLORS["white"])
        self.chat_history_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 0)) 
        self.chat_history_frame.grid_columnconfigure(0, weight=1)

        # Input Area (Bottom) - Flat Bar style
        self.input_area = ctk.CTkFrame(self.left_col, fg_color=COLORS["input_bg"], corner_radius=0, height=70)
        self.input_area.grid(row=1, column=0, sticky="ew")
        self.input_area.grid_columnconfigure(0, weight=1)

        self.tts_entry = ctk.CTkEntry(
            self.input_area, 
            placeholder_text="メッセージを入力...", 
            height=40, 
            font=FONTS["main"],
            fg_color="#FFFFFF",
            border_color="#E0E0E0",
            border_width=1,
            text_color=COLORS["text"],
            corner_radius=20,
            placeholder_text_color="#90A4AE"
        )
        self.tts_entry.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="ew")
        self.tts_entry.bind("<Return>", lambda e: self._speak())

        # Toggle Button (Send / Stop)
        self.action_btn = ctk.CTkButton(
            self.input_area, 
            text="", 
            image=self.icon_send,
            command=self._speak, 
            height=40, 
            width=40,
            fg_color="transparent",
            hover_color="#E0E0E0",
            corner_radius=20
        )
        self.action_btn.grid(row=0, column=1, padx=(0, 15), pady=15)

        # 3. Right Column: SE
        self.right_col = ctk.CTkFrame(self.main_frame, fg_color=COLORS["white"], corner_radius=20)
        self.right_col.grid(row=1, column=1, sticky="nsew")
        self.right_col.grid_rowconfigure(1, weight=1)
        self.right_col.grid_columnconfigure(0, weight=1)

        # SE Header with Controls
        self.se_header = ctk.CTkFrame(self.right_col, fg_color="transparent")
        self.se_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.se_header, text="効果音", font=FONTS["bold"], text_color=COLORS["text"]).pack(side="left")
        
        self.add_se_btn = ctk.CTkButton(self.se_header, text="+", width=30, height=30, command=self._add_se, fg_color=COLORS["accent"], text_color=COLORS["text"])
        self.add_se_btn.pack(side="right", padx=5)
        
        self.del_se_btn = ctk.CTkButton(self.se_header, text="-", width=30, height=30, command=self._toggle_delete_mode, fg_color="#ECEFF1", text_color=COLORS["text"], hover_color=COLORS["alert"])
        self.del_se_btn.pack(side="right")

        self.se_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent", label_text="")
        self.se_scroll.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="nsew")
        self.se_scroll.grid_columnconfigure(0, weight=1)

    def _apply_config(self):
        self.speed_slider.set(self.config["default_speed"])
        self.volume_slider.set(self.config["default_volume"])
        self.pitch_slider.set(self.config["default_pitch"])
        self._on_voice_param_change(None) # Update labels and engine

    def _startup_check(self):
        self.now_playing_label.configure(text="アプリを確認中...")
        
        def ask_permission(app_name):
            return messagebox.askyesno(
                "アプリ起動", 
                f"{app_name} が起動していません。\n起動しますか？\n(15秒ほどかかる場合があります)"
            )
        
        threading.Thread(target=self._run_startup_logic, args=(ask_permission,), daemon=True).start()

    def _run_startup_logic(self, callback):
        self.engine.check_and_launch_apps(callback)
        self.after(0, self._load_data)

    def _load_data(self):
        self.now_playing_label.configure(text="読み込み中...")
        
        # Load Devices
        self.devices = self.engine.get_output_devices()
        device_names = [f"{d[1]} ({d[2]})" for d in self.devices]
        
        if device_names:
            self.device_option.configure(values=device_names)
            default_idx = 0
            for i, name in enumerate(device_names):
                if "Voicemeeter" in name:
                    default_idx = i
                    break
            self.device_option.set(device_names[default_idx])
            self._on_device_change(device_names[default_idx])
        else:
            self.device_option.configure(values=["デバイスなし"])

        # Load Speakers
        speakers_data = self.engine.get_speakers()
        self.speakers_map = {} 
        speaker_names = []

        if not speakers_data:
            self.now_playing_label.configure(text="Voicevox エラー")
            messagebox.showerror("接続エラー", "Voicevoxに接続できませんでした。")
        else:
            for sp in speakers_data:
                name = sp['name']
                for style in sp['styles']:
                    full_name = f"{name} ({style['name']})"
                    self.speakers_map[full_name] = style['id']
                    speaker_names.append(full_name)
            
            self.speaker_option.configure(values=speaker_names)
            if speaker_names:
                # Try to find default from config
                def_name = self.config["default_speaker_name"]
                def_style = self.config["default_speaker_style"]
                target = next((n for n in speaker_names if def_name in n and def_style in n), speaker_names[0])
                
                self.speaker_option.set(target)
                self._on_speaker_change(target)
                self.now_playing_label.configure(text="準備完了")

        # Load SE
        self._create_se_buttons()

    def _create_se_buttons(self):
        for widget in self.se_scroll.winfo_children():
            widget.destroy()

        for name in self.engine.se_map.keys():
            btn = ctk.CTkButton(
                self.se_scroll, 
                text=name, 
                command=lambda n=name: self._handle_se_click(n),
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color=COLORS["text"],
                font=FONTS["main"],
                corner_radius=15,
                height=40
            )
            btn.pack(fill="x", pady=5)

    def _on_device_change(self, choice):
        for i, (idx, name, host) in enumerate(self.devices):
            if f"{name} ({host})" == choice:
                self.engine.set_output_device(idx)
                break

    def _on_speaker_change(self, choice):
        if choice in self.speakers_map:
            self.current_speaker_id = self.speakers_map[choice]

    def _on_voice_param_change(self, value):
        speed = self.speed_slider.get()
        volume = self.volume_slider.get()
        pitch = self.pitch_slider.get()
        
        self.engine.speed_scale = speed
        self.engine.volume_scale = volume
        self.engine.pitch_scale = pitch
        
        self.speed_val_label.configure(text=f"{speed:.2f}")
        self.volume_val_label.configure(text=f"{volume:.2f}")
        self.pitch_val_label.configure(text=f"{pitch:.2f}")

    def _add_chat_bubble(self, text, is_se=False):
        # Create a frame for the bubble row
        row_frame = ctk.CTkFrame(self.chat_history_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=5, padx=10)
        
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        if is_se:
            # SE Bubble (Left Aligned, Grey)
            bubble = ctk.CTkFrame(row_frame, fg_color=COLORS["bubble_se"], corner_radius=15)
            bubble.pack(side="left", anchor="w")
            
            ctk.CTkLabel(bubble, text=f"♪ {text}", font=FONTS["chat"], text_color=COLORS["text"]).pack(padx=10, pady=5)
            ctk.CTkLabel(row_frame, text=time_str, font=("Yu Gothic UI", 10), text_color="white").pack(side="left", anchor="w", padx=5, pady=(10,0))
            
        else:
            # User Speech Bubble (Right Aligned, Green)
            # Time first (on the left of the bubble)
            ctk.CTkLabel(row_frame, text=time_str, font=("Yu Gothic UI", 10), text_color="white").pack(side="right", anchor="e", padx=5, pady=(10,0))
            
            bubble = ctk.CTkFrame(row_frame, fg_color=COLORS["bubble_user"], corner_radius=15)
            bubble.pack(side="right", anchor="e")
            
            # Wrap text if too long
            ctk.CTkLabel(bubble, text=text, font=FONTS["chat"], text_color=COLORS["text"], wraplength=300, justify="left").pack(padx=10, pady=5)

        # Scroll to bottom (simple hack: update idle tasks then scroll)
        self.chat_history_frame.update_idletasks()
        self.chat_history_frame._parent_canvas.yview_moveto(1.0)
        
        # Console Log
        print(f"[{time_str}] {text}")


    def _set_status(self, text, is_playing=True):
        self.now_playing_label.configure(text=text)
        if is_playing:
            self.status_frame.configure(border_color=COLORS["alert"], border_width=2)
            self._update_action_button("stop")
        else:
            self.status_frame.configure(border_color=COLORS["white"], border_width=0)
            self._update_action_button("send")

    def _update_action_button(self, state):
        if state == "send":
            self.action_btn.configure(image=self.icon_send, command=self._speak)
        elif state == "stop":
            self.action_btn.configure(image=self.icon_stop, command=self._stop)

    def _speak(self):
        text = self.tts_entry.get()
        if not text:
            return
        
        if self.current_speaker_id is None:
            return

        self._add_chat_bubble(text, is_se=False)
        self.tts_entry.delete(0, "end")
        
        self.engine.speak(
            text, 
            self.current_speaker_id,
            on_start=lambda: self._set_status(f"発言中: {text[:20]}...", True),
            on_complete=lambda: self._set_status("準備完了", False)
        )

    def _stop(self):
        self.engine.stop()
        self._set_status("停止しました", False)

    def _handle_se_click(self, name):
        if self.delete_mode:
            if messagebox.askyesno("削除", f"効果音 '{name}' を削除しますか？"):
                if self.engine.remove_se(name):
                    self._create_se_buttons()
        else:
            self._play_se(name)

    def _play_se(self, name):
        self._add_chat_bubble(name, is_se=True)
        self.engine.play_se(
            name,
            on_start=lambda: self._set_status(f"再生中: {name}", True),
            on_complete=lambda: self._set_status("準備完了", False)
        )

    def _add_se(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            name = os.path.splitext(os.path.basename(file_path))[0]
            if self.engine.add_se(name, file_path):
                self._create_se_buttons()
                messagebox.showinfo("成功", f"効果音 '{name}' を追加しました。")

    def _toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.del_se_btn.configure(fg_color=COLORS["alert"], text_color="white")
            self.now_playing_label.configure(text="削除モード: SEをクリックして削除")
        else:
            self.del_se_btn.configure(fg_color="#ECEFF1", text_color=COLORS["text"])
            self.now_playing_label.configure(text="準備完了")

if __name__ == "__main__":
    app = VLiveCTKApp()
    app.mainloop()
