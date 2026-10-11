import os
import sys
import tempfile
import threading
import time
import customtkinter as ctk
import pygame
import yt_dlp

# WinGet orqali o'rnatilgan FFmpeg'ni avtomatik aniqlash va PATH ga qo'shish
winget_ffmpeg_path = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
)
if os.path.exists(winget_ffmpeg_path) and winget_ffmpeg_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = winget_ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

# Dastur mavzusi (Dark)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Pygame mikserini ishga tushirish
pygame.mixer.init()


class JahongirOtajonovMusicPlayer(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Jahongir Otajonov - Online Music Platform")
        self.geometry("480x880")
        self.resizable(False, False)

        # Qo'shiqlar ro'yxati
        self.songs_list = [
            {"title": "Bevafo", "query": "Jahangir Otajonov Bevafo official"},
            {"title": "Qaddini ursin", "query": "Jahangir Otajonov Qaddini ursin"},
            {"title": "Dog'man", "query": "Jahangir Otajonov Dogman"},
            {"title": "Ayrildim", "query": "Jahangir Otajonov Ayrildim"},
            {"title": "Kechir", "query": "Jahangir Otajonov Kechir"},
            {"title": "Guldona", "query": "Jahangir Otajonov Guldona"},
            {"title": "Chaqasi bor", "query": "Jahangir Otajonov Chaqasi bor"},
            {"title": "Qaddi baland", "query": "Jahangir Otajonov Qaddi baland"},
        ]
        self.current_index = 0
        self.is_playing = False
        self.is_downloading = False
        self.song_duration = 0
        self.playlist_buttons = []

        # Kesh papkasi
        self.cache_dir = os.path.join(tempfile.gettempdir(), "jo_music_player")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.current_audio_file = None

        self.setup_ui()
        self.update_progress_loop()

    def setup_ui(self):
        # 1. Yuqori panel (Header)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=25, pady=(20, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="SAMSUNG MUSIC STYLE",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#8E8E93",
        )
        self.title_label.pack(side="left")

        self.artist_tag = ctk.CTkLabel(
            self.header_frame,
            text="ONLINE STREAMING",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1DB954",
        )
        self.artist_tag.pack(side="right")

        # 2. Cover / Albom vizualizatori
        self.cover_frame = ctk.CTkFrame(
            self, corner_radius=25, fg_color="#1C1C1E", width=280, height=280
        )
        self.cover_frame.pack(pady=10)
        self.cover_frame.pack_propagate(False)

        self.cover_label = ctk.CTkLabel(
            self.cover_frame,
            text="🎙️\n\nJahongir\nOtajonov",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#8E8E93",
        )
        self.cover_label.pack(expand=True)

        # 3. Qo'shiq nomi va holati
        self.song_title = ctk.CTkLabel(
            self,
            text="Qo'shiqni tanlang",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF",
        )
        self.song_title.pack(pady=(10, 0))

        self.song_subtitle = ctk.CTkLabel(
            self,
            text="Jahongir Otajonov",
            font=ctk.CTkFont(size=14),
            text_color="#A1A1A6",
        )
        self.song_subtitle.pack(pady=(0, 10))

        # 4. Taymer va Progress Bar (Seekbar)
        self.progress_slider = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            button_color="#1DB954",
            button_hover_color="#1AA34A",
            progress_color="#1DB954",
            command=self.on_seek,
        )
        self.progress_slider.set(0)
        self.progress_slider.pack(fill="x", padx=40, pady=(5, 0))

        self.time_label = ctk.CTkLabel(
            self,
            text="00:00 / 00:00",
            font=ctk.CTkFont(size=12),
            text_color="#8E8E93",
        )
        self.time_label.pack(pady=(2, 10))

        # 5. Pleyer boshqaruv tugmalari
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack(pady=5)

        self.prev_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏮",
            width=55,
            height=55,
            corner_radius=28,
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            font=ctk.CTkFont(size=20),
            command=self.prev_song,
        )
        self.prev_btn.pack(side="left", padx=12)

        self.play_btn = ctk.CTkButton(
            self.controls_frame,
            text="▶",
            width=70,
            height=70,
            corner_radius=35,
            fg_color="#1DB954",
            hover_color="#1AA34A",
            font=ctk.CTkFont(size=26),
            command=self.toggle_play,
        )
        self.play_btn.pack(side="left", padx=12)

        self.next_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏭",
            width=55,
            height=55,
            corner_radius=28,
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            font=ctk.CTkFont(size=20),
            command=self.next_song,
        )
        self.next_btn.pack(side="left", padx=12)

        # 6. Ovoz boshqaruvi (Volume)
        self.volume_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.volume_frame.pack(fill="x", padx=45, pady=5)

        self.vol_icon = ctk.CTkLabel(
            self.volume_frame,
            text="🔈",
            font=ctk.CTkFont(size=14),
        )
        self.vol_icon.pack(side="left", padx=(0, 5))

        self.volume_slider = ctk.CTkSlider(
            self.volume_frame,
            from_=0,
            to=1,
            width=150,
            button_color="#8E8E93",
            button_hover_color="#FFFFFF",
            progress_color="#1DB954",
            command=self.change_volume,
        )
        self.volume_slider.set(0.8)
        pygame.mixer.music.set_volume(0.8)
        self.volume_slider.pack(side="left", fill="x", expand=True)

        # 7. Pleylist
        self.playlist_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#1C1C1E",
            corner_radius=18,
            height=190,
        )
        self.playlist_frame.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        self.render_playlist()

    def render_playlist(self):
        for idx, song in enumerate(self.songs_list):
            btn = ctk.CTkButton(
                self.playlist_frame,
                text=f"  {idx+1}. {song['title']}",
                anchor="w",
                fg_color="transparent",
                hover_color="#2C2C2E",
                text_color="#E5E5EA",
                font=ctk.CTkFont(size=14),
                command=lambda i=idx: self.select_song(i),
            )
            btn.pack(fill="x", pady=2)
            self.playlist_buttons.append(btn)

    def highlight_active_song(self):
        for idx, btn in enumerate(self.playlist_buttons):
            if idx == self.current_index:
                btn.configure(fg_color="#2C2C2E", text_color="#1DB954")
            else:
                btn.configure(fg_color="transparent", text_color="#E5E5EA")

    def select_song(self, index):
        if self.is_downloading:
            return

        self.current_index = index
        self.highlight_active_song()
        song = self.songs_list[index]
        self.song_title.configure(text=song["title"])
        self.play_from_youtube(song["query"])

    def play_from_youtube(self, query):
        self.is_downloading = True
        self.song_subtitle.configure(text="🌐 YouTube'dan yuklanmoqda...")
        self.progress_slider.set(0)
        self.time_label.configure(text="00:00 / --:--")

        def download_and_stream():
            file_hash = f"song_{self.current_index}_{int(time.time())}"
            output_template = os.path.join(self.cache_dir, f"{file_hash}.%(ext)s")
            final_mp3_path = os.path.join(self.cache_dir, f"{file_hash}.mp3")

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
                "no_warnings": True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                    if "entries" in info and len(info["entries"]) > 0:
                        duration = info["entries"][0].get("duration", 0)
                    else:
                        duration = info.get("duration", 0)

                # UI asosiy oqimda yangilanadi
                self.after(0, lambda: self._on_download_success(final_mp3_path, duration))
            except Exception as e:
                print("Xatolik tafsiloti:", e)
                self.after(0, self._on_download_error)

        threading.Thread(target=download_and_stream, daemon=True).start()

    def _on_download_success(self, mp3_path, duration):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            # Eski faylni tozalash
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                try:
                    os.remove(self.current_audio_file)
                except OSError:
                    pass

            self.current_audio_file = mp3_path
            self.song_duration = duration or 180
            self.progress_slider.configure(to=self.song_duration)

            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()

            self.is_playing = True
            self.is_downloading = False
            self.play_btn.configure(text="⏸")
            self.song_subtitle.configure(text="Jahongir Otajonov (Jonli ijro)")
        except Exception as err:
            print("Musiqa yuklashda xatolik:", err)
            self._on_download_error()

    def _on_download_error(self):
        self.is_downloading = False
        self.is_playing = False
        self.play_btn.configure(text="▶")
        self.song_subtitle.configure(text="❌ Yuklashda xatolik yuz berdi!")

    def toggle_play(self):
        if not self.current_audio_file or self.is_downloading:
            return

        if self.is_playing:
            pygame.mixer.music.pause()
            self.play_btn.configure(text="▶")
            self.is_playing = False
        else:
            pygame.mixer.music.unpause()
            self.play_btn.configure(text="⏸")
            self.is_playing = True

    def next_song(self):
        next_idx = (self.current_index + 1) % len(self.songs_list)
        self.select_song(next_idx)

    def prev_song(self):
        prev_idx = (self.current_index - 1) % len(self.songs_list)
        self.select_song(prev_idx)

    def change_volume(self, val):
        pygame.mixer.music.set_volume(float(val))

    def on_seek(self, val):
        if self.is_playing and self.current_audio_file:
            try:
                pygame.mixer.music.set_pos(float(val))
            except Exception:
                pass

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def update_progress_loop(self):
        if self.is_playing and not self.is_downloading:
            curr_pos_ms = pygame.mixer.music.get_pos()
            if curr_pos_ms >= 0:
                curr_secs = curr_pos_ms / 1000
                self.progress_slider.set(curr_secs)
                curr_str = self.format_time(curr_secs)
                total_str = self.format_time(self.song_duration)
                self.time_label.configure(text=f"{curr_str} / {total_str}")

                # Qo'shiq tugaganini tekshirish
                if not pygame.mixer.music.get_busy():
                    self.next_song()

        self.after(500, self.update_progress_loop)


if __name__ == "__main__":
    app = JahongirOtajonovMusicPlayer()
    app.mainloop()
