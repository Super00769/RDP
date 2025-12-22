import sys
import subprocess
import os
import importlib.util
import datetime 

# ================= AUTO-INSTALLER =================
required_libraries = {
    "telethon": "telethon",
    "PIL": "pillow",
    "cv2": "opencv-python-headless",
    "requests": "requests",
    "cryptg": "cryptg",
    "customtkinter": "customtkinter"
}

def install_libraries():
    print("Checking libraries...")
    for module_name, pip_name in required_libraries.items():
        is_installed = importlib.util.find_spec(module_name) is not None
        if not is_installed:
            if module_name == "cryptg":
                 try: import cryptg; is_installed = True
                 except: is_installed = False

        if not is_installed:
            print(f"Installing {pip_name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"✅ {pip_name} installed!")
            except Exception as e:
                print(f"⚠️ {pip_name} failed. Error: {e}")

install_libraries()
# =================================================

# --- SILENCE OPENCV/FFMPEG ERRORS ---
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8" 
# ------------------------------------

import customtkinter as ctk 
import tkinter as tk
from tkinter import filedialog
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
from PIL import Image, ImageTk
import cv2  
import threading
import asyncio
import time
import math
import json
import requests
import concurrent.futures
import tempfile

# ================= CONFIGURATION =================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue") 

default_fallback_id = "" 
config_file = "config.json"
home = os.path.expanduser("~")
default_upload_folder = os.path.join(home, "Desktop", "Telegram_Uploads")
default_download_folder = os.path.join(home, "Desktop", "Telegram_Downloads")

for folder in [default_upload_folder, default_download_folder]:
    if not os.path.exists(folder):
        try: os.makedirs(folder)
        except: pass

# ================= HELPER CLASSES =================

class ModernPopup(ctk.CTkToplevel):
    def __init__(self, parent, title, message, is_error=False):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x300") 
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        accent_color = "#D32F2F" if is_error else "#00E676" 
        text_color = "white" if is_error else "black"
        
        self.header = ctk.CTkFrame(self, height=10, fg_color=accent_color, corner_radius=0)
        self.header.pack(fill="x")
        
        icon_text = "!" if is_error else "✔"
        self.lbl_icon = ctk.CTkLabel(self, text=icon_text, font=("Arial", 45))
        self.lbl_icon.pack(pady=(20, 5))
        
        self.lbl_title = ctk.CTkLabel(self, text=title, font=("Roboto Medium", 20))
        self.lbl_title.pack(pady=(0, 10))
        
        self.lbl_msg = ctk.CTkLabel(self, text=message, font=("Roboto", 13), text_color=("gray30", "silver"), wraplength=380)
        self.lbl_msg.pack(pady=(0, 20), padx=20)
        
        self.btn_ok = ctk.CTkButton(self, text="OK", command=self.destroy, fg_color=accent_color, text_color=text_color, hover_color="#333", width=120)
        self.btn_ok.pack(side="bottom", pady=20)
        self.grab_set()
        self.focus_force()

class MessageDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Send Message")
        self.geometry("500x480") 
        self.attributes("-topmost", True)
        
        self.lbl_title = ctk.CTkLabel(self, text="Compose Message", font=("Roboto Medium", 18))
        self.lbl_title.pack(pady=(20, 10))
        
        self.textbox = ctk.CTkTextbox(self, height=200, font=("Roboto", 12))
        self.textbox.pack(fill="x", padx=20, pady=10)
        self.textbox.focus_set()
        
        self.lbl_char_count = ctk.CTkLabel(self, text="0 / 4096", font=("Roboto", 11), text_color="gray")
        self.lbl_char_count.pack(pady=(0, 5))
        
        self.textbox.bind("<KeyRelease>", self.update_char_count)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self.cut_text)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all)

        self.textbox.bind("<Button-3>", self.show_context_menu)
        
        self.btn_send = ctk.CTkButton(self, text="Send Message", command=self.send_msg, 
                                      fg_color="#00E676", text_color="black", hover_color="#00C853", width=200)
        self.btn_send.pack(pady=(10, 5))
        
        self.lbl_status_msg = ctk.CTkLabel(self, text="", font=("Roboto", 10), text_color="gray")
        self.lbl_status_msg.pack(pady=(0, 10))

    def update_char_count(self, event=None):
        text = self.textbox.get("1.0", "end-1c")
        count = len(text)
        limit = 4096
        if count > limit:
            over = count - limit
            self.lbl_char_count.configure(text=f"{count} / {limit} (+{over} over - Auto Split Active)", text_color="#FF9800")
        else:
            self.lbl_char_count.configure(text=f"{count} / {limit}", text_color="gray")

    def show_context_menu(self, event):
        try: self.context_menu.tk_popup(event.x_root, event.y_root)
        finally: self.context_menu.grab_release()

    def cut_text(self):
        try:
            self.copy_text()
            self.textbox.delete("sel.first", "sel.last")
            self.update_char_count()
        except: pass

    def copy_text(self):
        try:
            text = self.textbox.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(text)
        except: pass

    def paste_text(self):
        try:
            text = self.clipboard_get()
            self.textbox.insert("insert", text)
            self.update_char_count()
        except: pass

    def select_all(self):
        self.textbox.tag_add("sel", "1.0", "end")
        
    def send_msg(self):
        text = self.textbox.get("1.0", "end-1c").strip()
        if not text: return
        self.btn_send.configure(state="disabled", text="Sending...")
        self.lbl_status_msg.configure(text="Processing...", text_color="gray")
        
        chunk_size = 4000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        if self.parent.app.client: 
            asyncio.run_coroutine_threadsafe(self.async_send_chunks(chunks), self.parent.app.loop)
        else: 
            threading.Thread(target=self.http_send_chunks, args=(chunks,), daemon=True).start()
        
    async def async_send_chunks(self, chunks):
        try:
            target_id = int(self.parent.entry_chat_id.get())
            total = len(chunks)
            for i, chunk in enumerate(chunks):
                self.lbl_status_msg.configure(text=f"Sending part {i+1}/{total}...", text_color="#FFA726")
                await self.parent.app.client.send_message(target_id, chunk)
                if self.parent.app.dashboard:
                    utc_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                    ist_dt = utc_dt + datetime.timedelta(hours=5, minutes=30)
                    time_str = ist_dt.strftime("%I:%M %p")
                    self.parent.app.dashboard.log_text(f"You (Part {i+1}/{total})", chunk, time_str)
                if i < total - 1: await asyncio.sleep(2) 
            self.lbl_status_msg.configure(text="Last message status: Sent successfully", text_color="#00E676")
            self.textbox.delete("1.0", "end")
            self.update_char_count()
        except Exception as e:
            self.lbl_status_msg.configure(text=f"Failed: {str(e)}", text_color="#FF1744")
        finally:
            self.btn_send.configure(state="normal", text="Send Message")

    def http_send_chunks(self, chunks):
        try:
            target_id = self.parent.entry_chat_id.get()
            url = f"https://api.telegram.org/bot{self.parent.app.bot_token}/sendMessage"
            total = len(chunks)
            for i, chunk in enumerate(chunks):
                self.lbl_status_msg.configure(text=f"Sending part {i+1}/{total}...", text_color="#FFA726")
                data = {"chat_id": target_id, "text": chunk}
                r = requests.post(url, data=data)
                if r.status_code == 200:
                    if self.parent.app.dashboard:
                        utc_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                        ist_dt = utc_dt + datetime.timedelta(hours=5, minutes=30)
                        time_str = ist_dt.strftime("%I:%M %p")
                        self.parent.app.dashboard.log_text(f"You (Part {i+1}/{total})", chunk, time_str)
                else: raise Exception(f"HTTP Error: {r.text}")
                if i < total - 1: time.sleep(2)
            self.lbl_status_msg.configure(text="Last message status: Sent successfully", text_color="#00E676")
            self.textbox.delete("1.0", "end")
            self.update_char_count()
        except Exception as e:
            self.lbl_status_msg.configure(text=f"Failed: {str(e)}", text_color="#FF1744")
        finally:
            self.btn_send.configure(state="normal", text="Send Message")

class QueueManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Queue Manager")
        self.geometry("600x700") 
        self.attributes("-topmost", True)
        self.lbl_title = ctk.CTkLabel(self, text="Upload Queue", font=("Roboto Medium", 20))
        self.lbl_title.pack(pady=15)
        ctk.CTkLabel(self, text="Drag '≡' to reorder or use arrows", text_color="gray", font=("Roboto", 11)).pack()
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Ordered List", fg_color=("gray90", "#232323"))
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.scroll_frame._parent_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.scroll_frame._parent_canvas.bind("<Button-4>", self._on_mouse_wheel)
        self.scroll_frame._parent_canvas.bind("<Button-5>", self._on_mouse_wheel)
        self.btn_done = ctk.CTkButton(self, text="Save & Close", command=self.close_window, fg_color="#00E676", text_color="black", hover_color="#00C853", height=40)
        self.btn_done.pack(pady=20)
        self.row_widgets = []; self.drag_source_index = None; self.draw_list()

    def _on_mouse_wheel(self, event):
        if event.num == 5 or event.delta < 0: self.scroll_frame._parent_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0: self.scroll_frame._parent_canvas.yview_scroll(-1, "units")

    def draw_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.row_widgets = []
        if not self.parent.selected_files:
            ctk.CTkLabel(self.scroll_frame, text="No files selected.", text_color="gray").pack(pady=20); return
        for index, full_path in enumerate(self.parent.selected_files):
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("white", "#2B2B2B"))
            row_frame.pack(fill="x", pady=4, padx=5)
            lbl_grip = ctk.CTkLabel(row_frame, text="≡", font=("Arial", 20), cursor="hand2", width=30, text_color="gray")
            lbl_grip.pack(side="left", padx=(5, 0))
            lbl_grip.bind("<Button-1>", lambda e, i=index: self.start_drag(e, i))
            lbl_grip.bind("<ButtonRelease-1>", self.stop_drag)
            ctk.CTkLabel(row_frame, text=f"{index + 1}.", width=25, font=("Roboto", 14, "bold")).pack(side="left", padx=5)
            thumb_img = self.parent.get_thumbnail(full_path)
            if thumb_img:
                img_label = ctk.CTkLabel(row_frame, text="", image=thumb_img, width=50) 
                img_label.pack(side="left", padx=5, pady=5)
            else: ctk.CTkLabel(row_frame, text="FILE", font=("Arial", 10), width=50).pack(side="left", padx=5)
            filename = os.path.basename(full_path)
            display_name = (filename[:18] + '..') if len(filename) > 18 else filename
            ctk.CTkLabel(row_frame, text=display_name, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
            meta_info = self.parent.get_file_metadata(full_path)
            ctk.CTkLabel(row_frame, text=meta_info, anchor="e", font=("Roboto", 11), text_color="gray").pack(side="left", padx=10, fill="x", expand=True)
            btn_del = ctk.CTkButton(row_frame, text="X", width=30, height=30, fg_color="#FF1744", hover_color="#D50000", text_color="white", command=lambda i=index: self.remove_file(i))
            btn_del.pack(side="right", padx=5)
            arrow_bg = ("gray80", "#444"); arrow_fg = ("black", "white"); disabled_bg = "transparent"; disabled_fg = "#555"
            btn_down = ctk.CTkButton(row_frame, text="▼", width=30, height=30, fg_color=arrow_bg, text_color=arrow_fg, hover_color="#555")
            if index < len(self.parent.selected_files) - 1: btn_down.configure(command=lambda i=index: self.move_down(i))
            else: btn_down.configure(state="disabled", fg_color=disabled_bg, text_color=disabled_fg)
            btn_down.pack(side="right", padx=2)
            btn_up = ctk.CTkButton(row_frame, text="▲", width=30, height=30, fg_color=arrow_bg, text_color=arrow_fg, hover_color="#555")
            if index > 0: btn_up.configure(command=lambda i=index: self.move_up(i))
            else: btn_up.configure(state="disabled", fg_color=disabled_bg, text_color=disabled_fg)
            btn_up.pack(side="right", padx=2)
            self.row_widgets.append(row_frame)

    def start_drag(self, event, index): self.drag_source_index = index; self.configure(cursor="fleur")
    def stop_drag(self, event):
        self.configure(cursor="arrow")
        if self.drag_source_index is None: return
        y_root = self.winfo_pointery()
        target_index = -1
        for i, row in enumerate(self.row_widgets):
            row_top = row.winfo_rooty(); row_bottom = row_top + row.winfo_height()
            if row_top - 5 <= y_root <= row_bottom + 5: target_index = i; break
        if target_index != -1 and target_index != self.drag_source_index:
            item = self.parent.selected_files.pop(self.drag_source_index)
            self.parent.selected_files.insert(target_index, item)
            self.draw_list(); self.parent.refresh_ui_selection()
        self.drag_source_index = None
    def move_up(self, index):
        if index > 0:
            self.parent.selected_files[index], self.parent.selected_files[index-1] = self.parent.selected_files[index-1], self.parent.selected_files[index]
            self.draw_list(); self.parent.refresh_ui_selection()
    def move_down(self, index):
        if index < len(self.parent.selected_files) - 1:
            self.parent.selected_files[index], self.parent.selected_files[index+1] = self.parent.selected_files[index+1], self.parent.selected_files[index]
            self.draw_list(); self.parent.refresh_ui_selection()
    def remove_file(self, index):
        file_to_remove = self.parent.selected_files[index]
        self.parent.remove_by_path(file_to_remove); self.draw_list()
    def close_window(self): self.destroy()
class DownloadItem(ctk.CTkFrame):
    def __init__(self, parent, event, sender_info, time_str, app, is_http=False, file_info=None):
        super().__init__(parent, fg_color="#2B2B2B")
        self.app = app
        self.event = event 
        self.is_http = is_http
        self.file_info = file_info 
        
        self.pack(fill="x", pady=5, padx=5)
        self.is_paused = False 
        
        # --- SMART FILENAME DETECTION ---
        if self.is_http and self.file_info:
            self.real_filename = self.file_info.get("file_name", f"download_{int(time.time())}.bin")
            self.total_size = self.file_info.get("file_size", 0)
        else:
            # Telethon: Try to get the original name
            raw_name = getattr(event.file, 'name', None)
            
            # If .name is None, check attributes
            if not raw_name and hasattr(event.file, 'attributes'):
                for attr in event.file.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name:
                        raw_name = attr.file_name
                        break
            
            # Fallback if still no name
            if not raw_name:
                ext = ".bin"
                if event.message.photo: ext = ".jpg"
                elif event.message.voice: ext = ".ogg"
                elif event.message.video: ext = ".mp4"
                raw_name = f"file_{event.id}{ext}"
            
            self.real_filename = raw_name
            self.total_size = event.file.size if event.file else 0
            
        self.filename = (self.real_filename[:40] + '...') if len(self.real_filename) > 40 else self.real_filename
        self.target_path = os.path.join(self.app.current_download_folder, self.real_filename)

        # --- UI Layout ---
        self.top_row = ctk.CTkFrame(self, fg_color="transparent")
        self.top_row.pack(fill="x", padx=10, pady=8)
        
        self.thumb_label = ctk.CTkLabel(self.top_row, text="📄", font=("Arial", 24), width=50, height=50, fg_color="#333", corner_radius=5)
        self.thumb_label.pack(side="left", padx=(0, 10))
        
        info_frame = ctk.CTkFrame(self.top_row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        sender_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        sender_row.pack(anchor="w")
        
        ctk.CTkLabel(sender_row, text=sender_info, font=("Roboto", 12, "bold"), text_color="white").pack(side="left")

        ctk.CTkLabel(info_frame, text=f"📄 {self.filename}", font=("Roboto", 11), text_color="silver", anchor="w").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"📅 {time_str}", font=("Roboto", 10), text_color="gray60", anchor="w").pack(anchor="w")

        self.lbl_meta = ctk.CTkLabel(self.top_row, text=f"{self.format_size(self.total_size)}", font=("Roboto", 11), text_color="gray")
        self.lbl_meta.pack(side="left", padx=5)
        
        # --- BUTTONS ---
        self.btn_cancel = ctk.CTkButton(self.top_row, text="Cancel", width=60, height=28, fg_color="#D32F2F", hover_color="#B71C1C", command=self.cancel_download, state="disabled")
        self.btn_cancel.pack(side="right", padx=(5, 0))
        
        # Only show Pause button if in HTTP mode
        if self.is_http:
            self.btn_pause = ctk.CTkButton(self.top_row, text="Pause", width=60, height=28, fg_color="gray", command=self.toggle_pause) 
            self.btn_pause.pack(side="right", padx=(5, 0))
        else:
            self.btn_pause = None

        self.btn_action = ctk.CTkButton(self.top_row, text="DOWNLOAD", width=95, height=28, fg_color="#00E676", text_color="black", hover_color="#00C853", command=self.start_download)
        self.btn_action.pack(side="right")
        
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=10)
        self.progress_bar.pack(fill="x", pady=(5, 5))
        self.progress_bar.set(0)
        self.lbl_status = ctk.CTkLabel(self.progress_frame, text="Waiting...", font=("Roboto", 11), text_color="gray")
        self.lbl_status.pack(anchor="w")

        if not self.is_http:
            asyncio.run_coroutine_threadsafe(self.load_thumbnail(), self.app.loop)

    async def load_thumbnail(self):
        try:
            msg = self.event.message
            should_download = False
            if msg.photo: should_download = True
            elif msg.document and msg.document.thumbs: should_download = True
            if should_download:
                temp_thumb = os.path.join(tempfile.gettempdir(), f"thumb_{self.event.id}_{int(time.time()*1000)}.jpg")
                path = await self.app.client.download_media(msg, file=temp_thumb, thumb=-1)
                if path and os.path.exists(path):
                    self.app.dashboard.after(0, lambda: self.display_thumbnail(path))
        except: pass

    def display_thumbnail(self, path):
        try:
            pil_img = Image.open(path)
            pil_img.thumbnail((50, 50))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(50, 50))
            self.thumb_label.configure(image=ctk_img, text="")
        except: pass

    def format_size(self, size_bytes):
        if size_bytes == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB"); i = int(math.floor(math.log(size_bytes, 1024))); p = math.pow(1024, i)
        return f"{round(size_bytes / p, 2)} {size_name[i]}"

    def start_download(self):
        self.is_cancelled = False
        self.is_paused = False
        self.btn_action.configure(state="disabled", text="Downloading...")
        self.btn_cancel.configure(state="normal")
        if self.btn_pause: self.btn_pause.configure(state="normal")
        self.progress_frame.pack(fill="x", padx=10, pady=(0, 10)) 
        
        if self.is_http:
             threading.Thread(target=self.http_download_logic, daemon=True).start()
        else:
             asyncio.run_coroutine_threadsafe(self.async_download_fast(), self.app.loop)

    def toggle_pause(self):
        if not self.btn_pause: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.configure(text="Resume", fg_color="#FF9800")
            self.lbl_status.configure(text="Paused", text_color="#FF9800")
        else:
            self.btn_pause.configure(text="Pause", fg_color="gray")
            self.lbl_status.configure(text="Resuming...", text_color="white")

    def cancel_download(self):
        self.is_cancelled = True
        self.is_paused = False 
        self.btn_cancel.configure(state="disabled")
        self.lbl_status.configure(text="Stopping...", text_color="#FF1744")

    # --- HTTP DOWNLOAD LOGIC ---
    def http_download_logic(self):
        try:
            file_id = self.file_info['file_id']
            url = f"https://api.telegram.org/bot{self.app.bot_token}/getFile?file_id={file_id}"
            r = requests.get(url)
            if r.status_code != 200: raise Exception("Failed to get file path")
            
            res = r.json()
            if not res['ok']: raise Exception("Telegram API Error")
            
            file_path_rel = res['result']['file_path']
            dl_url = f"https://api.telegram.org/file/bot{self.app.bot_token}/{file_path_rel}"
            
            with requests.get(dl_url, stream=True) as r:
                r.raise_for_status()
                total_len = int(r.headers.get('content-length', 0))
                dl = 0
                last_update = time.time()
                last_bytes = 0
                
                with open(self.target_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if self.is_cancelled: 
                            f.close()
                            try: os.remove(self.target_path)
                            except: pass
                            self.app.dashboard.after(0, lambda: self.lbl_status.configure(text="Cancelled."))
                            self.app.dashboard.after(2000, self.reset_download_ui)
                            return
                        
                        while self.is_paused:
                            if self.is_cancelled: return
                            time.sleep(0.5)

                        if chunk:
                            f.write(chunk)
                            dl += len(chunk)
                            
                            now = time.time()
                            if now - last_update > 0.5:
                                # Fix Speed Glitch: Capture values
                                self.app.dashboard.after(0, lambda d=dl, t=total_len, n=now, l=last_update, b=last_bytes: 
                                                         self.calc_stats(d, t, n, l, b))
                                last_update = now; last_bytes = dl
            
            self.app.dashboard.after(0, self.finish_ui)

        except Exception as e:
            self.app.dashboard.after(0, lambda: self.lbl_status.configure(text=f"Error: {e}"))
            self.app.dashboard.after(3000, self.reset_download_ui)

    # --- FAST TELETHON DOWNLOAD (Fixes Speed Glitch) ---
    async def async_download_fast(self):
        self.last_update_time = time.time()
        self.last_bytes_dl = 0
        
        def callback(current, total):
            if self.is_cancelled: raise Exception("CANCELLED_BY_USER")
            now = time.time()
            if now - self.last_update_time > 0.5:
                # Fix Speed Glitch: Capture values (c=current, t=total...)
                self.app.dashboard.after(0, lambda c=current, t=total, n=now, l=self.last_update_time, b=self.last_bytes_dl: 
                                         self.calc_stats(c, t, n, l, b))
                self.last_update_time = now
                self.last_bytes_dl = current

        try:
            path = await self.app.client.download_media(self.event.message, file=self.target_path, progress_callback=callback)
            if path: self.app.dashboard.after(0, self.finish_ui)
            else: raise Exception("Download failed")
        except Exception as e:
            if "CANCELLED_BY_USER" in str(e):
                self.app.dashboard.after(0, lambda: self.lbl_status.configure(text="Cancelled.", text_color="orange"))
                if os.path.exists(self.target_path): 
                    try: os.remove(self.target_path) 
                    except: pass
                self.app.dashboard.after(2000, self.reset_download_ui)
            else:
                self.app.dashboard.after(0, lambda: self.lbl_status.configure(text=f"Error: {e}"))
                self.app.dashboard.after(3000, self.reset_download_ui)

    def calc_stats(self, curr, tot, now, last_up, last_byte):
        percent = curr / tot if tot else 0
        
        # Calculate speed correctly
        time_diff = now - last_up
        byte_diff = curr - last_byte
        
        speed = byte_diff / time_diff if time_diff > 0 else 0
        spd_str = f"{speed/(1024*1024):.2f} MB/s"
        
        eta = "--:--"
        if speed > 0:
            rem = tot - curr
            sec = int(rem / speed)
            m, s = divmod(sec, 60); h, m = divmod(m, 60)
            eta = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
        
        self.update_ui(percent, spd_str, eta, curr, tot)

    def update_ui(self, p, spd, eta, curr, tot):
        self.progress_bar.set(p)
        self.lbl_status.configure(text=f"{self.format_size(curr)}/{self.format_size(tot)} | {spd} | ETA: {eta}")

    def finish_ui(self):
        self.progress_bar.set(1)
        self.lbl_status.configure(text="✅ Done!", text_color="#00E676")
        
        if self.btn_pause: self.btn_pause.destroy()
        self.btn_cancel.destroy()
        self.btn_action.destroy()
        
        self.btn_open = ctk.CTkButton(self.top_row, text="Open", width=80, command=self.open_file, fg_color="#1F6AA5")
        self.btn_open.pack(side="right", padx=5)

        self.btn_delete = ctk.CTkButton(self.top_row, text="🗑", width=40, fg_color="#D32F2F", hover_color="#B71C1C", command=self.delete_file)
        self.btn_delete.pack(side="right", padx=5)

    def delete_file(self):
        try:
            if os.path.exists(self.target_path): os.remove(self.target_path)
            self.destroy() 
        except: pass

    def reset_download_ui(self):
        self.progress_frame.pack_forget()
        self.btn_action.configure(text="DOWNLOAD", state="normal", fg_color="#00E676")
        self.btn_cancel.configure(state="disabled")
        if self.btn_pause:
            self.btn_pause.configure(state="disabled", text="Pause", fg_color="gray")

    def open_file(self):
        os.system(f'xdg-open "{self.target_path}"')
# ================= FRAMES (SCREENS) =================

class ModeSelectFrame(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        
        self.lbl_title = ctk.CTkLabel(self, text="SuperTool Login Mode", font=("Roboto Medium", 22))
        self.lbl_title.pack(pady=(100, 30))
        
        self.btn_full = ctk.CTkButton(self, text="⚡ Full Access\n(API ID + Hash + Token)", width=300, height=80, 
                                      font=("Roboto", 16, "bold"), fg_color="#1F6AA5", hover_color="#144870",
                                      command=lambda: self.app.show_login("full"))
        self.btn_full.pack(pady=15)
        
        self.btn_simple = ctk.CTkButton(self, text="📦 Limited Access\n(Bot Token Only)", width=300, height=80, 
                                        font=("Roboto", 16, "bold"), fg_color="#00897B", hover_color="#00695C",
                                        command=lambda: self.app.show_login("simple"))
        self.btn_simple.pack(pady=15)

class LoginFrame(ctk.CTkFrame):
    def __init__(self, app, mode):
        super().__init__(app)
        self.app = app
        self.mode = mode
        
        saved_api_id, saved_api_hash, saved_bot_token, saved_cid = "", "", "", str(default_fallback_id)
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    saved_api_id = data.get("api_id", "")
                    saved_api_hash = data.get("api_hash", "")
                    saved_bot_token = data.get("bot_token", "")
                    saved_cid = str(data.get("chat_id", default_fallback_id))
            except: pass

        self.lbl_title = ctk.CTkLabel(self, text="Bot Authorization", font=("Roboto Medium", 22))
        self.lbl_title.pack(pady=(40, 30))
        
        # Center contents
        if self.mode == "full":
            self.lbl_api_id = ctk.CTkLabel(self, text="API ID", font=("Roboto", 12, "bold"), text_color="gray")
            self.lbl_api_id.pack(pady=(0, 2))
            self.entry_api_id = ctk.CTkEntry(self, placeholder_text="Enter API ID...", width=300, height=35, show="•")
            self.entry_api_id.pack(pady=(0, 15))
            self.entry_api_id.insert(0, str(saved_api_id))

            self.lbl_api_hash = ctk.CTkLabel(self, text="API Hash", font=("Roboto", 12, "bold"), text_color="gray")
            self.lbl_api_hash.pack(pady=(0, 2))
            self.entry_api_hash = ctk.CTkEntry(self, placeholder_text="Enter API Hash...", width=300, height=35, show="•")
            self.entry_api_hash.pack(pady=(0, 15))
            self.entry_api_hash.insert(0, saved_api_hash)
        else:
            self.entry_api_id = None
            self.entry_api_hash = None

        self.lbl_token = ctk.CTkLabel(self, text="Bot Token", font=("Roboto", 12, "bold"), text_color="gray")
        self.lbl_token.pack(pady=(0, 2))
        self.entry_token = ctk.CTkEntry(self, placeholder_text="Enter Bot Token...", width=300, height=35, show="•")
        self.entry_token.pack(pady=(0, 15))
        self.entry_token.insert(0, saved_bot_token)

        self.lbl_chat_id = ctk.CTkLabel(self, text="Default Chat ID (Optional)", font=("Roboto", 12, "bold"), text_color="gray")
        self.lbl_chat_id.pack(pady=(0, 2))
        self.entry_chat_id = ctk.CTkEntry(self, placeholder_text="Enter Chat ID...", width=300, height=35)
        self.entry_chat_id.pack(pady=(0, 15))
        self.entry_chat_id.insert(0, saved_cid)
        
        btn_text = "Login (Telethon)" if self.mode == "full" else "Login (HTTP)"
        btn_color = "#1F6AA5" if self.mode == "full" else "#00897B"
        
        self.btn_login = ctk.CTkButton(self, text=btn_text, width=300, height=45, command=self.attempt_login, font=("Roboto Medium", 15), fg_color=btn_color)
        self.btn_login.pack(pady=(20, 10))

        self.btn_reset = ctk.CTkButton(self, text="Clear Data", width=300, fg_color="#FF1744", hover_color="#D50000", command=self.reset_config, text_color="white")
        self.btn_reset.pack(pady=5)
        
        self.btn_back = ctk.CTkButton(self, text="Back to Mode Selection", width=300, fg_color="transparent", border_width=1, text_color="gray", hover_color="#333", command=self.app.show_mode_selection)
        self.btn_back.pack(pady=5)
        
        self.lbl_status = ctk.CTkLabel(self, text="Ready to connect...", text_color="gray")
        self.lbl_status.pack(pady=10)

    def reset_config(self):
        if os.path.exists(config_file): os.remove(config_file)
        if self.entry_api_id: self.entry_api_id.delete(0, tk.END)
        if self.entry_api_hash: self.entry_api_hash.delete(0, tk.END)
        self.entry_token.delete(0, tk.END); self.entry_chat_id.delete(0, tk.END)
        self.lbl_status.configure(text="Config deleted. Data cleared.", text_color="#FF1744")

    def attempt_login(self):
        s_bot_token = self.entry_token.get().strip()
        s_chat_id = self.entry_chat_id.get().strip()
        
        s_api_id, s_api_hash = "0", ""
        if self.mode == "full":
            s_api_id = self.entry_api_id.get().strip()
            s_api_hash = self.entry_api_hash.get().strip()
            if not s_api_id or not s_api_hash:
                self.lbl_status.configure(text="API Fields Required!", text_color="red"); return
        if not s_bot_token:
            self.lbl_status.configure(text="Token Required!", text_color="red"); return

        self.btn_login.configure(state="disabled", text="Connecting..."); self.btn_reset.configure(state="disabled")
        self.lbl_status.configure(text="Initializing...", text_color="#00E676")
        
        data = {"bot_token": s_bot_token, "chat_id": s_chat_id}
        if self.mode == "full":
            try: int_api_id = int(s_api_id)
            except: self.lbl_status.configure(text="API ID must be number", text_color="red"); return
            data["api_id"] = int_api_id
            data["api_hash"] = s_api_hash
        
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f: old_data = json.load(f)
                old_data.update(data)
                data = old_data
            except: pass
            
        with open(config_file, "w") as f: json.dump(data, f)
        
        self.app.saved_chat_id = s_chat_id
        self.app.bot_token = s_bot_token
        
        if self.mode == "full":
            threading.Thread(target=self.run_async_login, args=(int(s_api_id), s_api_hash, s_bot_token), daemon=True).start()
        else:
            threading.Thread(target=self.run_http_listener, args=(s_bot_token,), daemon=True).start()

    # --- HTTP LISTENER (Limited Access) ---
    def run_http_listener(self, bot_token):
        try:
            r = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            if r.status_code != 200 or not r.json()['ok']: raise Exception("Invalid Token")
            me = r.json()['result']
            self.app.bot_info = f"{me['first_name']} (@{me['username']})"
            self.app.is_running = True
            
            self.after(0, self.app.show_uploader)
            
            last_update_id = 0
            while self.app.is_running:
                try:
                    res = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates", 
                                       params={'offset': last_update_id + 1, 'timeout': 20})
                    if res.status_code == 200:
                        updates = res.json().get('result', [])
                        for update in updates:
                            last_update_id = update['update_id']
                            if 'message' not in update: continue
                            msg = update['message']
                            
                            if self.app.dashboard:
                                # Filtering (All Chats vs Target)
                                try:
                                    if not self.app.dashboard.all_chats_var.get():
                                        target = self.app.dashboard.entry_chat_id.get().strip()
                                        if target and str(msg['chat']['id']) != target: continue
                                except: pass
                                
                                # Formatting (Group vs DM)
                                sender_info = ""
                                user = msg.get('from', {})
                                chat = msg.get('chat', {})
                                u_name = user.get('first_name', 'Unknown')
                                u_user = user.get('username', '')
                                u_id = str(user.get('id', ''))
                                
                                user_detail = f"{u_name}"
                                if u_user: user_detail += f" (@{u_user})"
                                
                                if chat.get('type') in ['group', 'supergroup', 'channel']:
                                    g_title = chat.get('title', 'Group')
                                    g_id = chat.get('id', '')
                                    sender_info = f"Group: {g_title} (ID: {g_id}) | User: {user_detail}"
                                else:
                                    sender_info = f"DM: {user_detail} [ID: {u_id}]"

                                ts = time.strftime("%I:%M %p", time.localtime(msg.get('date', time.time())))
                                
                                # File Handling
                                file_info = None
                                if 'document' in msg: file_info = msg['document']
                                elif 'video' in msg: file_info = msg['video']
                                elif 'photo' in msg: file_info = msg['photo'][-1]
                                elif 'audio' in msg: file_info = msg['audio']
                                elif 'voice' in msg: file_info = msg['voice']
                                
                                if file_info:
                                    f_id = file_info.get('file_id')
                                    f_name = file_info.get('file_name', f"file_{f_id[:5]}.bin")
                                    f_size = file_info.get('file_size', 0)
                                    self.app.dashboard.add_item_http({'file_id': f_id, 'file_name': f_name, 'file_size': f_size}, sender_info, ts)
                                elif 'text' in msg:
                                    self.app.dashboard.log_text(sender_info, msg['text'], ts)
                                    
                except Exception as e:
                    time.sleep(2)
        except Exception as e:
            self.after(0, lambda: ModernPopup(self, "Login Error", str(e), is_error=True))
            self.after(0, self.reset_ui)

    # --- TELETHON LISTENER (Full Access) ---
    def run_async_login(self, api_id, api_hash, bot_token):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        client = TelegramClient('supertool_session', api_id, api_hash, loop=loop, connection_retries=10)
        
        async def connect():
            try:
                await client.start(bot_token=bot_token)
                me = await client.get_me()
                self.app.bot_info = f"{me.first_name} (@{me.username})"
                return True
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: ModernPopup(self, "Login Failed", err_msg, is_error=True)) 
                return False

        try:
            if loop.run_until_complete(connect()):
                self.app.client = client
                self.app.loop = loop
                self.app.is_running = True
                
                @client.on(events.NewMessage)
                async def handler(event):
                    if not self.app.is_running: return
                    
                    if self.app.dashboard:
                        # Filtering
                        try:
                            if not self.app.dashboard.all_chats_var.get():
                                target_str = self.app.dashboard.entry_chat_id.get().strip()
                                if target_str:
                                    target_id = int(target_str)
                                    if event.chat_id != target_id: return
                        except: pass

                        utc_dt = event.date
                        ist_dt = utc_dt + datetime.timedelta(hours=5, minutes=30)
                        time_str = ist_dt.strftime("%I:%M %p") 
                        
                        sender = await event.get_sender()
                        chat = await event.get_chat()
                        
                        user_first = getattr(sender, 'first_name', 'Unknown') or 'Unknown'
                        user_uname = getattr(sender, 'username', None)
                        user_id_str = str(getattr(sender, 'id', 'Unknown'))
                        
                        sender_info = ""
                        
                        # Formatting
                        if event.is_group or event.is_channel:
                            group_title = getattr(chat, 'title', 'Group')
                            group_id = getattr(chat, 'id', 'Unknown')
                            user_detail = f"{user_first}"
                            if user_uname: user_detail += f" (@{user_uname})"
                            sender_info = f"Group: {group_title} (ID: {group_id}) | User: {user_detail}"
                        else:
                            sender_info = f"DM: {user_first}"
                            if user_uname: sender_info += f" (@{user_uname})"
                            sender_info += f" [ID: {user_id_str}]"

                        if event.file:
                            self.app.dashboard.add_item(event, sender_info, time_str)
                        elif event.text:
                            self.app.dashboard.log_text(sender_info, event.text, time_str)

                threading.Thread(target=loop.run_forever, daemon=True).start()
                self.after(0, self.app.show_uploader)
            else: self.after(0, self.reset_ui)
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: ModernPopup(self, "Critical Error", err_msg, is_error=True))
            self.after(0, self.reset_ui)

    def reset_ui(self):
        self.btn_login.configure(state="normal", text="Login & Connect"); self.btn_reset.configure(state="normal")
        self.lbl_status.configure(text="Connection failed.", text_color="red")
class UploaderFrame(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        
        self.current_folder = default_upload_folder
        self.previous_folder = None 
        
        self.selected_files = [] 
        self.file_widgets = {} 
        self.is_cancelled = False
        self.last_update_time = 0; self.last_bytes_sent = 0
        self.upload_task = None 
        self.thumbnails_cache = {} 
        self.meta_cache = {} 
        self.use_caption = tk.BooleanVar(value=True)
        self.use_album = tk.BooleanVar(value=False)
        
        # --- BACKGROUND TOGGLE VARIABLE ---
        self.bg_var = ctk.BooleanVar(value=False)

        # --- HEADER (ROW 1) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=30, pady=(20, 5))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Batch Uploader", font=("Roboto Medium", 26))
        self.title_label.pack(side="left")
        
        status_txt = "Online | Turbo Mode" if self.app.client else "Online | 50MB Limit"
        self.status_dot = ctk.CTkLabel(self.header_frame, text=status_txt, font=("Roboto", 12), text_color="#00E676")
        self.status_dot.pack(side="left", padx=15, pady=(8,0))

        # Right Side of Header (Navigation)
        self.btn_logout = ctk.CTkButton(self.header_frame, text="Logout", width=80, height=30, fg_color="#D32F2F", hover_color="#B71C1C", command=self.app.logout)
        self.btn_logout.pack(side="right", padx=0)

        self.btn_switch = ctk.CTkButton(self.header_frame, text="⬇ Go to Downloader", width=140, height=30, 
                                        fg_color="#F57C00", hover_color="#E65100", command=self.app.switch_tool)
        self.btn_switch.pack(side="right", padx=10)

        # --- SETTINGS ROW (ROW 2 - Fixes Squishing) ---
        self.settings_row = ctk.CTkFrame(self, fg_color="transparent")
        self.settings_row.pack(fill="x", padx=30, pady=(5, 20))

        # Target Chat Input & Check
        ctk.CTkLabel(self.settings_row, text="Target Chat:", font=("Roboto", 12, "bold")).pack(side="left", padx=(0, 5))
        
        self.entry_chat_id = ctk.CTkEntry(self.settings_row, width=150, font=("Roboto", 14), height=32)
        self.entry_chat_id.pack(side="left", padx=5)
        self.entry_chat_id.insert(0, str(self.app.saved_chat_id))
        
        self.btn_verify = ctk.CTkButton(self.settings_row, text="Check ID", width=90, height=32, command=self.verify_user)
        self.btn_verify.pack(side="left", padx=5)

        # Background Toggle (Now has space on the right)
        self.switch_bg = ctk.CTkSwitch(self.settings_row, text="Background Mode", variable=self.bg_var, onvalue=True, offvalue=False, progress_color="#7B1FA2")
        self.switch_bg.pack(side="right", padx=5)

        # --- CONTROLS ---
        self.mid_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.mid_bar.pack(fill="x", padx=30, pady=(0, 10))
        self.main_label = ctk.CTkLabel(self.mid_bar, text="Select Files:", font=("Roboto Medium", 16))
        self.main_label.pack(side="left")

        self.sort_var = ctk.StringVar(value="Newest First")
        self.sort_menu = ctk.CTkOptionMenu(self.mid_bar, values=["Newest First", "Oldest First", "Size (Largest)", "Size (Smallest)", "File Type", "Duration (Longest)", "Duration (Shortest)"], command=self.sort_changed, variable=self.sort_var, width=150, height=32)
        self.sort_menu.pack(side="right", padx=5)
        
        self.btn_theme = ctk.CTkButton(self.mid_bar, text="Theme", width=50, height=32, command=self.toggle_theme)
        self.btn_theme.pack(side="right", padx=5)
        
        # UTILITY BUTTONS
        self.btn_refresh = ctk.CTkButton(self.mid_bar, text="Reload", width=70, height=32, fg_color=("gray85", "#555555"), text_color=("black", "white"), hover_color=("gray75", "#444"), command=self.load_thumbnails)
        self.btn_refresh.pack(side="right", padx=5)
        
        self.btn_folder = ctk.CTkButton(self.mid_bar, text="Folder", width=70, height=32, fg_color=("gray80", "#455A64"), text_color=("black", "white"), hover_color=("gray70", "#37474F"), command=self.change_folder)
        self.btn_folder.pack(side="right", padx=5)
        
        self.btn_default = ctk.CTkButton(self.mid_bar, text="Default", width=70, height=32, fg_color=("gray80", "#455A64"), text_color=("black", "white"), hover_color=("gray70", "#37474F"), command=self.reset_folder)
        self.btn_default.pack(side="right", padx=5)
        
        self.btn_downloads = ctk.CTkButton(self.mid_bar, text="Downloads", width=80, height=32, fg_color=("gray80", "#455A64"), text_color=("black", "white"), hover_color=("gray70", "#37474F"), command=self.open_downloads_folder)
        self.btn_downloads.pack(side="right", padx=5)
        
        self.btn_recent = ctk.CTkButton(self.mid_bar, text="Recent", width=70, height=32, fg_color=("gray80", "#455A64"), text_color=("black", "white"), hover_color=("gray70", "#37474F"), command=self.switch_recent_folder)
        self.btn_recent.pack(side="right", padx=5)

        self.path_label = ctk.CTkLabel(self.mid_bar, text=f"Path: {os.path.basename(self.current_folder)}", font=("Roboto", 13), text_color="gray")
        self.path_label.pack(side="right", padx=20)

        # --- FILES AREA ---
        # !!! FIX: Height reduced to 300 for smaller screens
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Files Folder", height=300, corner_radius=10)
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.scroll_frame._parent_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.scroll_frame._parent_canvas.bind("<Button-4>", self._on_mouse_wheel)
        self.scroll_frame._parent_canvas.bind("<Button-5>", self._on_mouse_wheel)

        # --- INFO ---
        self.info_frame = ctk.CTkFrame(self, fg_color=("gray85", "#232323"), corner_radius=10)
        self.info_frame.pack(fill="x", padx=30, pady=10)
        self.lbl_count = ctk.CTkLabel(self.info_frame, text="Files: 0", font=("Roboto", 14))
        self.lbl_count.pack(side="left", padx=30, pady=15)
        self.lbl_size = ctk.CTkLabel(self.info_frame, text="Size: 0 MB", font=("Roboto", 14))
        self.lbl_size.pack(side="left", padx=30, pady=15)
        self.lbl_status = ctk.CTkLabel(self.info_frame, text="Status: Ready", font=("Roboto", 14), text_color="#00E676")
        self.lbl_status.pack(side="right", padx=30, pady=15)

        # --- BUTTONS ---
        self.progress = ctk.CTkProgressBar(self, height=12)
        self.progress.pack(fill="x", padx=30, pady=(0, 20))
        self.progress.set(0)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=30, pady=10)
        
        self.btn_select_all = ctk.CTkButton(self.btn_frame, text="Select All", width=80, height=45, fg_color=("gray80", "#455A64"), text_color=("black", "white"), hover_color=("gray70", "#37474F"), command=self.toggle_select_all)
        self.btn_select_all.pack(side="left", padx=(0, 10))

        self.btn_queue = ctk.CTkButton(self.btn_frame, text="Queue", width=80, height=45, fg_color="#FF9800", text_color="black", hover_color="#F57C00", command=self.open_queue_manager)
        self.btn_queue.pack(side="left", padx=(0, 10))
        
        self.btn_msg = ctk.CTkButton(self.btn_frame, text="Msg", width=60, height=45, fg_color="#448AFF", text_color="white", hover_color="#2979FF", command=self.open_msg_window)
        self.btn_msg.pack(side="left", padx=(0, 10))
        
        self.switch_caption = ctk.CTkSwitch(self.btn_frame, text="Caption", variable=self.use_caption, width=60, progress_color="#00E676")
        self.switch_caption.pack(side="left", padx=15)
        
        if self.app.client:
             self.switch_album = ctk.CTkSwitch(self.btn_frame, text="Album", variable=self.use_album, width=60, progress_color="#FF9800")
             self.switch_album.pack(side="left", padx=15)

        self.btn_upload = ctk.CTkButton(self.btn_frame, text="START UPLOAD", width=220, height=45, font=("Roboto Medium", 16), fg_color="#00E676", text_color="black", hover_color="#00C853", command=self.start_upload, state="disabled")
        self.btn_upload.pack(side="right")
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="STOP", width=120, height=45, fg_color="#FF1744", text_color="white", hover_color="#D50000", command=self.cancel_upload, state="disabled")
        self.btn_cancel.pack(side="right", padx=15)

        self.footer = ctk.CTkLabel(self, text=f"Logged in as: {self.app.bot_info}", text_color="gray", font=("Roboto", 11))
        self.footer.pack(pady=5)

        self.load_thumbnails()

    def _on_mouse_wheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.scroll_frame._parent_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.scroll_frame._parent_canvas.yview_scroll(-1, "units")

    # --- FUNCTIONALITY ---
    def open_msg_window(self):
        try: int(self.entry_chat_id.get())
        except: ModernPopup(self, "Error", "Invalid Target ID!", is_error=True); return
        MessageDialog(self)

    def open_queue_manager(self):
        if not self.selected_files:
            ModernPopup(self, "Queue Manager", "Please select files first to manage the queue.")
            return
        QueueManagerWindow(self)

    def change_folder(self):
        new_folder = filedialog.askdirectory()
        if new_folder:
            self.previous_folder = self.current_folder
            self.current_folder = new_folder
            self.path_label.configure(text=f"Path: {os.path.basename(self.current_folder)}")
            self.load_thumbnails()

    def reset_folder(self):
        self.previous_folder = self.current_folder
        self.current_folder = default_upload_folder
        self.path_label.configure(text=f"Path: {os.path.basename(self.current_folder)}")
        self.load_thumbnails()

    def open_downloads_folder(self):
        codespace_dl = "/home/codespace/Downloads"
        home_dl = os.path.join(home, "Downloads")
        target = codespace_dl if os.path.exists(codespace_dl) else (home_dl if os.path.exists(home_dl) else "")
        if target:
            self.previous_folder = self.current_folder
            self.current_folder = target
            self.path_label.configure(text=f"Path: {os.path.basename(self.current_folder)}")
            self.load_thumbnails()
        else:
            ModernPopup(self, "Error", "Downloads folder not found!", is_error=True)
            
    def switch_recent_folder(self):
        if not self.previous_folder or not os.path.exists(self.previous_folder):
            ModernPopup(self, "No History", "No recent folder recorded yet.")
            return
        temp = self.current_folder
        self.current_folder = self.previous_folder
        self.previous_folder = temp
        self.path_label.configure(text=f"Path: {os.path.basename(self.current_folder)}")
        self.load_thumbnails()

    def toggle_select_all(self):
        visible_files = list(self.file_widgets.keys())
        if not visible_files: return
        visible_full_paths = [os.path.join(self.current_folder, f) for f in visible_files]
        all_visible_selected = all(p in self.selected_files for p in visible_full_paths)
        if all_visible_selected:
            for f in visible_files:
                p = os.path.join(self.current_folder, f)
                if p in self.selected_files: self.selected_files.remove(p)
                try: 
                    self.file_widgets[f].configure(fg_color="#333333")
                    for w in self.file_widgets[f].winfo_children(): w.configure(text_color="white")
                except: pass
        else:
            for f in visible_files:
                p = os.path.join(self.current_folder, f)
                if p not in self.selected_files: self.selected_files.append(p)
                try: 
                    self.file_widgets[f].configure(fg_color="#00E676") 
                    for w in self.file_widgets[f].winfo_children(): w.configure(text_color="black")
                except: pass
        self.update_info_panel()

    def refresh_ui_selection(self):
        for f, widget in self.file_widgets.items():
            full_path = os.path.join(self.current_folder, f)
            if full_path in self.selected_files:
                widget.configure(fg_color="#00E676")
                for w in widget.winfo_children(): w.configure(text_color="black")
            else:
                widget.configure(fg_color="#333333")
                for w in widget.winfo_children(): w.configure(text_color="white")
        self.update_info_panel()

    def toggle_theme(self):
        if ctk.get_appearance_mode() == "Dark": ctk.set_appearance_mode("Light")
        else: ctk.set_appearance_mode("Dark")

    def sort_changed(self, choice):
        self.sort_var.set(choice)
        self.load_thumbnails()

    def verify_user(self):
        target_id_str = self.entry_chat_id.get().strip()
        try: target_id = int(target_id_str)
        except ValueError: ModernPopup(self, "Error", "Invalid ID format.", is_error=True); return
        self.btn_verify.configure(state="disabled", text="...")
        
        if self.app.client:
            asyncio.run_coroutine_threadsafe(self.async_verify(target_id), self.app.loop)
        else:
            threading.Thread(target=self.http_verify, args=(target_id,), daemon=True).start()

    async def async_verify(self, target_id):
        try:
            entity = await self.app.client.get_entity(target_id)
            if hasattr(entity, 'title'): 
                title = entity.title; count = getattr(entity, 'participants_count', 'Unknown')
                if count == 'Unknown':
                    try: p = await self.app.client.get_participants(entity, limit=0); count = p.total
                    except: pass
                msg = f"GROUP / CHANNEL\nName: {title}\nMembers: {count}"
            else:
                name = f"{entity.first_name} {entity.last_name or ''}".strip()
                username = f"@{entity.username}" if entity.username else "No Username"
                msg = f"USER\nName: {name}\nUser: {username}"
            self.after(0, lambda: ModernPopup(self, f"Verified: {target_id}", msg)) 
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: ModernPopup(self, "Not Found", err_msg, is_error=True))
        finally: self.after(0, lambda: self.btn_verify.configure(state="normal", text="Check"))

    def http_verify(self, target_id):
        try:
            r = requests.get(f"https://api.telegram.org/bot{self.app.bot_token}/getChat", params={"chat_id": target_id})
            if r.status_code == 200:
                res = r.json()
                if res['ok']:
                    c = res['result']
                    t = c.get('type', 'private')
                    title = c.get('title', c.get('first_name', 'Unknown'))
                    msg = f"Target Found (HTTP)\nType: {t}\nName: {title}"
                    self.after(0, lambda: ModernPopup(self, f"Verified: {target_id}", msg))
                else: raise Exception("Chat not found")
            else: raise Exception(f"HTTP Error: {r.text}")
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: ModernPopup(self, "Error", err_msg, is_error=True))
        finally:
            self.after(0, lambda: self.btn_verify.configure(state="normal", text="Check"))
    def start_upload(self):
        if not self.selected_files: ModernPopup(self, "Oops", "Select files first!", is_error=True); return
        try: target = int(self.entry_chat_id.get())
        except: ModernPopup(self, "Error", "Invalid Chat ID", is_error=True); return
        
        self.is_cancelled = False
        self.btn_upload.configure(state="disabled"); self.btn_cancel.configure(state="normal")
        
        if self.app.client:
            self.lbl_status.configure(text="Queueing (Telethon)...", text_color="#00E676")
            self.upload_task = asyncio.run_coroutine_threadsafe(self.async_upload_sequence(target), self.app.loop)
        else:
            self.lbl_status.configure(text="Starting HTTP Upload...", text_color="#00E676")
            threading.Thread(target=self.http_upload_sequence, args=(target,), daemon=True).start()

    async def async_upload_sequence(self, target_id):
        try:
            total_size = sum([os.path.getsize(f) for f in self.selected_files])
            uploaded_so_far = 0; self.last_update_time = time.time(); self.last_bytes_sent = 0; start_time = time.time()

            def chunks(lst, n):
                for i in range(0, len(lst), n):
                    yield lst[i:i + n]

            file_batches = list(chunks(self.selected_files, 10)) if self.use_album.get() else [[f] for f in self.selected_files]
            
            for batch_index, batch in enumerate(file_batches):
                if self.is_cancelled: raise asyncio.CancelledError
                
                album_handles = []
                album_captions = []
                album_thumbs = []
                album_attrs = []
                
                for i, path in enumerate(batch):
                    if self.is_cancelled: raise asyncio.CancelledError
                    
                    current_file_size = os.path.getsize(path)
                    f_name = os.path.basename(path)
                    cap_text = f_name if self.use_caption.get() else ""
                    
                    global_index = (batch_index * 10) + i + 1
                    status_text = f"Uploading ({global_index}/{len(self.selected_files)}): {f_name[:20]}..."
                    self.after(0, lambda txt=status_text: self.lbl_status.configure(text=txt))
                    
                    attrs = []; thumb_path = None; uploaded_thumb = None
                    try:
                        if path.lower().endswith(('.mp4', '.mkv', '.avi')):
                            cap = cv2.VideoCapture(path)
                            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            fps = cap.get(cv2.CAP_PROP_FPS); dur = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps) if fps > 0 else 0
                            ret, frame = cap.read()
                            if ret:
                                thumb_h, thumb_w, _ = frame.shape
                                if thumb_w > 320:
                                    scale = 320 / thumb_w; new_h = int(thumb_h * scale)
                                    frame = cv2.resize(frame, (320, new_h), interpolation=cv2.INTER_AREA)
                                thumb_path = os.path.join("/tmp", f"thumb_{int(time.time())}_{i}.jpg")
                                cv2.imwrite(thumb_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                            cap.release()
                            attrs = [DocumentAttributeVideo(duration=dur, w=w, h=h, supports_streaming=True)]
                    except: pass

                    if not attrs and path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                         attrs = [DocumentAttributeVideo(duration=0, w=0, h=0, supports_streaming=True)]

                    async def callback(curr, tot):
                        if self.is_cancelled: raise asyncio.CancelledError
                        total_uploaded_now = uploaded_so_far + curr
                        percent = total_uploaded_now / total_size
                        now = time.time()
                        
                        if now - self.last_update_time > 0.5:
                            speed = (total_uploaded_now - self.last_bytes_sent) / (now - self.last_update_time)
                            spd_str = f"{speed/(1024*1024):.2f} MB/s"
                            rem_bytes = total_size - total_uploaded_now
                            sec = int(rem_bytes / speed) if speed > 0 else 0
                            m, s = divmod(sec, 60); h, m = divmod(m, 60); eta = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
                            
                            self.last_update_time = now
                            self.last_bytes_sent = total_uploaded_now
                            
                            curr_mb = total_uploaded_now / (1024 * 1024); tot_mb = total_size / (1024 * 1024)
                            status_text = f"Size: {curr_mb:.1f}/{tot_mb:.1f} MB | Speed: {spd_str} | ETA: {eta}"
                            
                            self.after(0, lambda: self.lbl_status.configure(text=status_text))
                            self.after(0, lambda: self.progress.set(percent))

                    try:
                        if thumb_path and os.path.exists(thumb_path): 
                            uploaded_thumb = await self.app.client.upload_file(thumb_path)
                        
                        uploaded_file = await self.app.client.upload_file(path, progress_callback=callback, part_size_kb=512)
                        uploaded_so_far += current_file_size 
                        
                        album_handles.append(uploaded_file)
                        album_captions.append(cap_text)
                        album_thumbs.append(uploaded_thumb)
                        album_attrs.append(attrs) 
                        
                    except Exception as e:
                        if self.is_cancelled or "Cancelled" in str(e): raise asyncio.CancelledError
                        err_msg = str(e)
                        self.after(0, lambda: ModernPopup(self, "Upload Error", err_msg, is_error=True))
                        return
                    finally:
                        if thumb_path and os.path.exists(thumb_path):
                            try: os.remove(thumb_path)
                            except: pass
                
                if not self.is_cancelled and album_handles:
                    self.after(0, lambda: self.lbl_status.configure(text="Sending Media..."))
                    try:
                        if len(album_handles) == 1:
                            if album_attrs[0]:
                                await self.app.client.send_file(
                                    target_id, 
                                    album_handles[0],
                                    caption=album_captions[0], 
                                    thumb=album_thumbs[0],
                                    attributes=album_attrs[0],
                                    supports_streaming=True
                                )
                            else:
                                await self.app.client.send_file(
                                    target_id, 
                                    album_handles[0], 
                                    caption=album_captions[0], 
                                    thumb=album_thumbs[0],
                                    supports_streaming=True
                                )
                        else:
                            await self.app.client.send_file(
                                target_id, 
                                album_handles, 
                                caption=album_captions, 
                                thumb=album_thumbs,
                                attributes=album_attrs,
                                supports_streaming=True
                            )
                    except Exception as e:
                        err_msg = str(e)
                        self.after(0, lambda: ModernPopup(self, "Send Error", err_msg, is_error=True))

            if not self.is_cancelled:
                end_time = time.time(); duration_seconds = end_time - start_time
                m, s = divmod(duration_seconds, 60); h, m = divmod(m, 60)
                time_str = f"{int(h)}h {int(m)}m {int(s)}s" if h else f"{int(m)}m {int(s)}s"
                try:
                    entity = await self.app.client.get_entity(target_id)
                    name = entity.title if hasattr(entity, 'title') else (entity.first_name or "Unknown")
                    target_display = name
                except: target_display = f"ID: {target_id}"
                final_msg = f"Successfully sent to: {target_display}\n\nFiles: {len(self.selected_files)}\nTotal Size: {self.format_size(total_size)}\nTime Taken: {time_str}"
                self.after(0, lambda: self.lbl_status.configure(text="DONE", text_color="#00E676"))
                self.after(0, lambda: ModernPopup(self, "Upload Complete", final_msg)) 
            self.after(0, self.reset_ui)
        except asyncio.CancelledError:
            self.after(0, self.start_cooldown)

    def http_upload_sequence(self, target_id):
        try:
            total = len(self.selected_files)
            for i, path in enumerate(self.selected_files):
                if self.is_cancelled: break
                f_name = os.path.basename(path)
                f_size = os.path.getsize(path)
                cap_text = f_name if self.use_caption.get() else ""
                
                if f_size > 50 * 1024 * 1024:
                    self.after(0, lambda: ModernPopup(self, "Skip", f"{f_name} exceeds 50MB limit for HTTP mode.", is_error=True))
                    continue

                self.after(0, lambda txt=f"HTTP Uploading ({i+1}/{total}): {f_name}...": self.lbl_status.configure(text=txt))
                self.after(0, lambda: self.progress.set((i)/total))
                
                url = f"https://api.telegram.org/bot{self.app.bot_token}/sendDocument"
                try:
                    with open(path, 'rb') as f:
                        files = {'document': f}
                        data = {'chat_id': target_id, 'caption': cap_text}
                        r = requests.post(url, data=data, files=files)
                        if r.status_code != 200:
                            raise Exception(f"HTTP {r.status_code}: {r.text}")
                except Exception as e:
                    err_msg = str(e)
                    self.after(0, lambda: ModernPopup(self, "HTTP Error", err_msg, is_error=True))
                    return

            if not self.is_cancelled:
                self.after(0, lambda: self.progress.set(1.0))
                self.after(0, lambda: self.lbl_status.configure(text="DONE", text_color="#00E676"))
                self.after(0, lambda: ModernPopup(self, "Success", "All compatible files sent via HTTP."))
            
            self.after(0, self.reset_ui)
        except Exception as e:
            self.after(0, self.reset_ui)

    def start_cooldown(self):
        self.btn_upload.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")
        self.progress.set(0)
        self.run_cooldown_timer(5)

    def run_cooldown_timer(self, seconds_left):
        if seconds_left > 0:
            self.lbl_status.configure(text=f"Cooldown active: {seconds_left}s - Please wait...", text_color="#FF1744")
            self.after(1000, lambda: self.run_cooldown_timer(seconds_left - 1))
        else:
            self.finish_cooldown()

    def finish_cooldown(self):
        try:
            self.lbl_status.configure(text="Ready to Upload", text_color="#00E676")
            self.btn_upload.configure(state="normal")
            self.btn_cancel.configure(state="disabled")
        except: pass

    def cancel_upload(self):
        self.is_cancelled = True
        self.lbl_status.configure(text="Stopping...", text_color="#FF1744")
        if self.upload_task: self.upload_task.cancel()

    def reset_ui(self):
        self.btn_upload.configure(state="normal"); self.btn_cancel.configure(state="disabled")
        self.progress.set(0)

    def get_thumbnail(self, path):
        if path in self.thumbnails_cache: return self.thumbnails_cache[path]
        try:
            if path.lower().endswith(('.mp4', '.mkv', '.avi')):
                cap = cv2.VideoCapture(path); ret, frame = cap.read(); cap.release()
                if ret: 
                    img = ctk.CTkImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), size=(70,70))
                    self.thumbnails_cache[path] = img; return img
            elif path.lower().endswith(('.jpg', '.png')): 
                img = ctk.CTkImage(Image.open(path), size=(70,70))
                self.thumbnails_cache[path] = img; return img
        except: return None

    def get_file_metadata(self, path):
        if path in self.meta_cache: return self.meta_cache[path]
        try:
            size = os.path.getsize(path)
            size_str = self.format_size(size)
            duration_str = ""
            if path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                try:
                    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS); frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if fps > 0:
                        seconds = int(frame_count / fps); m, s = divmod(seconds, 60); h, m = divmod(m, 60)
                        if h > 0: duration_str = f"Time: {h}:{m:02d}:{s:02d}"
                        else: duration_str = f"Time: {m}:{s:02d}"
                    cap.release()
                except: pass
            info_text = f"{size_str}"
            if duration_str: info_text += f"  |  {duration_str}"
            self.meta_cache[path] = info_text
            return info_text
        except: return ""

    def format_size(self, size_bytes):
        if size_bytes == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB"); i = int(math.floor(math.log(size_bytes, 1024))); p = math.pow(1024, i)
        return f"{round(size_bytes / p, 2)} {size_name[i]}"

    def load_thumbnails(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.file_widgets = {} 
        self.update_info_panel()
        try:
            if not os.access(self.current_folder, os.R_OK):
                ModernPopup(self, "Permission Error", "Cannot access this folder. Please choose another one.")
                return

            all_files = [f for f in os.listdir(self.current_folder) if not f.startswith('.')]
            
            def get_sort_key(f):
                full_p = os.path.join(self.current_folder, f)
                try:
                    sort_mode = self.sort_var.get()
                    if sort_mode == "Newest First" or sort_mode == "Oldest First":
                        return os.path.getmtime(full_p)
                    elif "Size" in sort_mode:
                        return os.path.getsize(full_p)
                    elif "Duration" in sort_mode:
                        if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')):
                            cap = cv2.VideoCapture(full_p)
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                            cap.release()
                            if fps > 0:
                                return int(frame_count / fps)
                        return 0
                    return f.lower()
                except OSError:
                    return 0

            reverse_sort = "Largest" in self.sort_var.get() or "Newest" in self.sort_var.get() or "Longest" in self.sort_var.get()
            all_files.sort(key=get_sort_key, reverse=reverse_sort)

            row = 0; col = 0
            for f in all_files:
                full_path = os.path.join(self.current_folder, f)
                if not os.path.isfile(full_path): continue

                frame = ctk.CTkFrame(self.scroll_frame, fg_color="#333333"); frame.grid(row=row, column=col, padx=8, pady=8)
                thumb = self.get_thumbnail(full_path)
                cmd = lambda x=full_path: self.toggle_selection(x) 
                
                if thumb:
                    btn = ctk.CTkButton(frame, text="", image=thumb, command=cmd, width=70, height=70, fg_color="transparent", hover_color="#444")
                else:
                    btn = ctk.CTkButton(frame, text="FILE", width=70, height=70, command=cmd, fg_color="#444", hover_color="#555")
                btn.pack()
                ctk.CTkLabel(frame, text=f[:8]+"..", font=("Roboto", 10)).pack()
                self.file_widgets[f] = frame; col += 1
                if col >= 8: col = 0; row += 1
                
                if full_path in self.selected_files:
                    frame.configure(fg_color="#00E676")
                    for w in frame.winfo_children():
                        try: w.configure(text_color="black")
                        except: pass
        except Exception as e:
             ModernPopup(self, "Folder Error", str(e), is_error=True)

    def toggle_selection(self, full_path):
        filename = os.path.basename(full_path)
        if full_path in self.selected_files:
            self.selected_files.remove(full_path)
            try: 
                if filename in self.file_widgets:
                    self.file_widgets[filename].configure(fg_color="#333333")
                    for w in self.file_widgets[filename].winfo_children(): w.configure(text_color="white")
            except: pass
        else:
            self.selected_files.append(full_path) 
            try: 
                if filename in self.file_widgets:
                    self.file_widgets[filename].configure(fg_color="#00E676") 
                    for w in self.file_widgets[filename].winfo_children(): w.configure(text_color="black")
            except: pass
        self.update_info_panel()
        
    def remove_by_path(self, full_path):
        if full_path in self.selected_files:
            self.selected_files.remove(full_path)
            filename = os.path.basename(full_path)
            if filename in self.file_widgets and os.path.dirname(full_path) == self.current_folder:
                 try:
                    self.file_widgets[filename].configure(fg_color="#333333")
                    for w in self.file_widgets[filename].winfo_children(): w.configure(text_color="white")
                 except: pass
        self.update_info_panel()

    def update_info_panel(self):
        count = len(self.selected_files); total = sum([os.path.getsize(f) for f in self.selected_files])
        self.lbl_count.configure(text=f"Files: {count}"); self.lbl_size.configure(text=f"Size: {self.format_size(total)}")
        if count > 0: self.btn_upload.configure(state="normal"); self.lbl_status.configure(text="Ready to Upload")
        else: self.btn_upload.configure(state="disabled"); self.lbl_status.configure(text="Select files first")
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app); self.app = app; self.app.dashboard = self
        
        # --- BACKGROUND TOGGLE VARIABLE ---
        self.bg_var = ctk.BooleanVar(value=False)
        self.all_chats_var = ctk.BooleanVar(value=False)
        self.auto_dl_var = ctk.BooleanVar(value=False)

        # --- HEADER (ROW 1) ---
        header = ctk.CTkFrame(self, fg_color="transparent"); header.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(header, text=f"Connected: {self.app.bot_info}", font=("Roboto Medium", 18), text_color="#00E676").pack(side="left")
        
        # Right Side Buttons
        ctk.CTkButton(header, text="Logout", width=80, fg_color="#D32F2F", command=self.app.logout).pack(side="right", padx=0)
        
        self.btn_switch = ctk.CTkButton(header, text="⬆ Go to Uploader", width=140, height=30, 
                                        fg_color="#00897B", hover_color="#00695C", command=self.app.switch_tool)
        self.btn_switch.pack(side="right", padx=10)

        # --- TOGGLES ROW (ROW 2 - Fixes Squishing) ---
        toggles_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=20, pady=(5, 10))

        # All Chats
        self.switch_all = ctk.CTkSwitch(toggles_frame, text="All Chats", variable=self.all_chats_var, progress_color="#FF9800")
        self.switch_all.pack(side="left", padx=(0, 15))

        # Auto Download
        self.switch_auto = ctk.CTkSwitch(toggles_frame, text="Auto Download", variable=self.auto_dl_var, progress_color="#00E676")
        self.switch_auto.pack(side="left", padx=15)
        
        # Background Toggle (Right aligned in Row 2)
        self.switch_bg = ctk.CTkSwitch(toggles_frame, text="Background Mode", variable=self.bg_var, onvalue=True, offvalue=False, progress_color="#7B1FA2")
        self.switch_bg.pack(side="right", padx=5)

        # --- TARGET CONTROLS (ROW 3) ---
        target_frame = ctk.CTkFrame(self, fg_color="transparent")
        target_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(target_frame, text="Target Chat:", font=("Roboto", 12, "bold")).pack(side="left")
        
        self.entry_chat_id = ctk.CTkEntry(target_frame, width=160, font=("Roboto", 14), height=30)
        self.entry_chat_id.pack(side="left", padx=5)
        self.entry_chat_id.insert(0, str(self.app.saved_chat_id))
        
        self.btn_verify = ctk.CTkButton(target_frame, text="Check ID", width=80, height=30, command=self.verify_user, fg_color="#555", hover_color="#444")
        self.btn_verify.pack(side="left", padx=5)
        
        self.btn_msg = ctk.CTkButton(target_frame, text="✎ Send Msg", width=100, height=30, fg_color="#448AFF", hover_color="#2979FF", command=self.open_msg_window)
        self.btn_msg.pack(side="left", padx=15)

        # Files Area
        self.file_list = ctk.CTkScrollableFrame(self, label_text="Incoming Files & Messages", fg_color="#1a1a1a")
        self.file_list.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- PATH LABEL ---
        self.lbl_path = ctk.CTkLabel(self, text=f"📂 {os.path.basename(self.app.current_download_folder)}", font=("Roboto", 11), text_color="gray")
        self.lbl_path.pack(pady=(0, 5))

        # --- FOOTER ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent"); btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Open Folder", command=self.open_folder, width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Set Folder", command=self.change_folder, width=150, fg_color="#F57C00", hover_color="#E65100").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Clear List", command=lambda: [w.destroy() for w in self.file_list.winfo_children()], width=150, fg_color="#455A64").pack(side="right", padx=5)

    def change_folder(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.app.current_download_folder = new_path
            self.lbl_path.configure(text=f"📂 {os.path.basename(new_path)}")
            
    def open_folder(self):
        os.system(f'xdg-open "{self.app.current_download_folder}"')

    def open_msg_window(self):
        try: int(self.entry_chat_id.get())
        except: ModernPopup(self, "Error", "Invalid Target ID!", is_error=True); return
        MessageDialog(self)

    def verify_user(self):
        target_id_str = self.entry_chat_id.get().strip()
        try: target_id = int(target_id_str)
        except ValueError: ModernPopup(self, "Error", "Invalid ID format.", is_error=True); return
        self.btn_verify.configure(state="disabled", text="...")
        
        if self.app.client:
            asyncio.run_coroutine_threadsafe(self.async_verify(target_id), self.app.loop)
        else:
            threading.Thread(target=self.http_verify, args=(target_id,), daemon=True).start()

    async def async_verify(self, target_id):
        try:
            entity = await self.app.client.get_entity(target_id)
            if hasattr(entity, 'title'): 
                title = entity.title; count = getattr(entity, 'participants_count', 'Unknown')
                if count == 'Unknown':
                    try: p = await self.app.client.get_participants(entity, limit=0); count = p.total
                    except: pass
                msg = f"GROUP / CHANNEL\nName: {title}\nMembers: {count}"
            else:
                name = f"{entity.first_name} {entity.last_name or ''}".strip()
                username = f"@{entity.username}" if entity.username else "No Username"
                msg = f"USER\nName: {name}\nUser: {username}"
            self.after(0, lambda: ModernPopup(self, f"Verified: {target_id}", msg)) 
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: ModernPopup(self, "Not Found", err_msg, is_error=True))
        finally: self.after(0, lambda: self.btn_verify.configure(state="normal", text="Check ID"))

    def http_verify(self, target_id):
        try:
            r = requests.get(f"https://api.telegram.org/bot{self.app.bot_token}/getChat", params={"chat_id": target_id})
            if r.status_code == 200:
                res = r.json()
                if res['ok']:
                    c = res['result']
                    t = c.get('type', 'private')
                    title = c.get('title', c.get('first_name', 'Unknown'))
                    msg = f"Target Found (HTTP)\nType: {t}\nName: {title}"
                    self.after(0, lambda: ModernPopup(self, f"Verified: {target_id}", msg))
                else: raise Exception("Chat not found")
            else: raise Exception(f"HTTP Error: {r.text}")
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: ModernPopup(self, "Error", err_msg, is_error=True))
        finally:
            self.after(0, lambda: self.btn_verify.configure(state="normal", text="Check ID"))

    # --- UPDATED: Telethon Add Item ---
    def add_item(self, event, sender_info, time_str):
        def _add():
            item = DownloadItem(self.file_list, event, sender_info, time_str, self.app, is_http=False)
            if self.auto_dl_var.get(): item.start_download()
        self.after(0, _add)

    # --- NEW: HTTP Add Item ---
    def add_item_http(self, file_info, sender_info, time_str):
        def _add():
            # Pass None as event, but pass file_info dict
            item = DownloadItem(self.file_list, None, sender_info, time_str, self.app, is_http=True, file_info=file_info)
            if self.auto_dl_var.get(): item.start_download()
        self.after(0, _add)

    def log_text(self, sender_info, msg, time_str):
        def _add_log():
            frame = ctk.CTkFrame(self.file_list, fg_color="#2B2B2B")
            frame.pack(fill="x", padx=5, pady=2)
            name_row = ctk.CTkFrame(frame, fg_color="transparent")
            name_row.pack(anchor="w", padx=5, pady=(5,0))
            ctk.CTkLabel(name_row, text=f"💬 {sender_info}", font=("Roboto", 12, "bold"), text_color="white").pack(side="left")
            ctk.CTkLabel(frame, text=msg, anchor="w", text_color="silver", wraplength=700).pack(fill="x", padx=5)
            ctk.CTkLabel(frame, text=f"📅 {time_str}", font=("Roboto", 9), text_color="gray60", anchor="w").pack(padx=5, pady=(0,5))
        self.after(0, _add_log)
# ================= MAIN APPLICATION CLASS =================

class SuperToolApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Super Tool Pro (Uploader & Downloader)")
        
        # --- RESIZE FIX APPLIED HERE ---
        # Changed from "1000x950" to "850x650" to fit all screens
        self.geometry("850x650") 
        
        self.client = None
        self.loop = None
        self.bot_info = ""
        self.bot_token = ""
        self.mode = "full" 
        self.saved_chat_id = "" 
        
        # --- PERSISTENT FRAMES STORAGE ---
        # We store the frames here so they CAN stay alive if the toggle is ON
        self.view_uploader = None
        self.view_downloader = None
        
        self.current_tool = "UPLOADER"
        self.current_download_folder = default_download_folder
        self.dashboard = None # Reference used by background listeners
        self.is_running = True

        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.show_mode_selection()

    def clear_window(self):
        # Only destroy widgets that are NOT our tool frames (keep tools safe)
        for widget in self.winfo_children():
            if widget != self.view_uploader and widget != self.view_downloader:
                widget.destroy()

    def show_mode_selection(self):
        # Fully reset on Logout/Start
        if self.view_uploader: self.view_uploader.destroy(); self.view_uploader = None
        if self.view_downloader: self.view_downloader.destroy(); self.view_downloader = None
        self.dashboard = None
        
        self.clear_window()
        ModeSelectFrame(self).pack(fill="both", expand=True)

    def show_login(self, mode):
        self.clear_window()
        self.mode = mode
        LoginFrame(self, mode).pack(fill="both", expand=True)

    def show_uploader(self):
        self.current_tool = "UPLOADER"
        self.clear_window() 
        
        # 1. HANDLE DOWNLOADER (The tool we are leaving)
        if self.view_downloader:
            # Check the Toggle Switch in Downloader
            if self.view_downloader.bg_var.get(): 
                self.view_downloader.pack_forget() # Hide (Background Mode ON)
            else:
                self.view_downloader.destroy() # Kill (Background Mode OFF)
                self.view_downloader = None
                self.dashboard = None # Stop listeners updating dead UI

        # 2. HANDLE UPLOADER (The tool we are showing)
        if self.view_uploader:
            self.view_uploader.pack(fill="both", expand=True) # Restore from background
        else:
            self.view_uploader = UploaderFrame(self) # Create new
            self.view_uploader.pack(fill="both", expand=True)
        
    def show_downloader(self):
        self.current_tool = "DOWNLOADER"
        self.clear_window()
        
        # 1. HANDLE UPLOADER (The tool we are leaving)
        if self.view_uploader:
            # Check the Toggle Switch in Uploader
            if self.view_uploader.bg_var.get():
                self.view_uploader.pack_forget() # Hide (Background Mode ON)
            else:
                self.view_uploader.destroy() # Kill (Background Mode OFF)
                self.view_uploader = None
        
        # 2. HANDLE DOWNLOADER (The tool we are showing)
        if self.view_downloader:
            self.view_downloader.pack(fill="both", expand=True) # Restore from background
        else:
            self.view_downloader = DashboardFrame(self) # Create new
            self.dashboard = self.view_downloader # Link listeners
            self.view_downloader.pack(fill="both", expand=True)

    def switch_tool(self):
        if self.current_tool == "UPLOADER": self.show_downloader()
        else: self.show_uploader()

    def on_exit(self):
        self.is_running = False
        try: 
            if self.loop: self.loop.stop()
            if self.client: self.client.disconnect()
        except: pass
        self.destroy()
        sys.exit()
    
    def logout(self):
        self.is_running = False
        if self.client:
            try: self.client.disconnect()
            except: pass
            self.client = None
        
        self.bot_info = ""
        self.bot_token = ""
        self.saved_chat_id = ""
        self.show_mode_selection()

if __name__ == "__main__":
    app = SuperToolApp()
    app.mainloop()
