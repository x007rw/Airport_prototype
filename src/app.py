import customtkinter as ctk
import threading
from PIL import Image
import os
import json
from main import ATC

# テーマ設定
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Airport Control Tower")
        self.geometry("1100x700")

        # グリッド構成 (2列)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        
        self.atc = ATC()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Airport ATC", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # URL
        self.url_label = ctk.CTkLabel(self.sidebar_frame, text="Target URL:", anchor="w")
        self.url_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.url_entry = ctk.CTkEntry(self.sidebar_frame)
        self.url_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.url_entry.insert(0, "https://example.com")

        # Selector
        self.selector_label = ctk.CTkLabel(self.sidebar_frame, text="Target Selector:", anchor="w")
        self.selector_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.selector_entry = ctk.CTkEntry(self.sidebar_frame)
        self.selector_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.selector_entry.insert(0, "a")

        # Mode Selection
        self.mode_label = ctk.CTkLabel(self.sidebar_frame, text="Operation Mode:", anchor="w")
        self.mode_label.grid(row=5, column=0, padx=20, pady=(10, 10), sticky="w")
        
        self.mode_var = ctk.StringVar(value="hybrid")
        self.radio_hybrid = ctk.CTkRadioButton(self.sidebar_frame, text="Hybrid (DOM+GUI)", variable=self.mode_var, value="hybrid")
        self.radio_hybrid.grid(row=6, column=0, padx=20, pady=5, sticky="w")
        self.radio_dom = ctk.CTkRadioButton(self.sidebar_frame, text="DOM Only", variable=self.mode_var, value="dom")
        self.radio_dom.grid(row=7, column=0, padx=20, pady=5, sticky="w")
        self.radio_gui = ctk.CTkRadioButton(self.sidebar_frame, text="GUI Only", variable=self.mode_var, value="gui")
        self.radio_gui.grid(row=8, column=0, padx=20, pady=5, sticky="w")

        # Run Button
        self.btn_run = ctk.CTkButton(self.sidebar_frame, text="Take Off (Run Task)", command=self.start_task_thread)
        self.btn_run.grid(row=9, column=0, padx=20, pady=30, sticky="ew")

        # Status
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: Ready", anchor="w")
        self.status_label.grid(row=10, column=0, padx=20, pady=(10, 20), sticky="w")

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Log Area
        self.log_label = ctk.CTkLabel(self.main_frame, text="Flight Recorder (Logs)", font=ctk.CTkFont(size=14, weight="bold"))
        self.log_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5), sticky="w")
        
        self.log_box = ctk.CTkTextbox(self.main_frame, height=150)
        self.log_box.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="nsew")

        # Image Area
        self.img_label_pre = ctk.CTkLabel(self.main_frame, text="Pre-Flight (Before)", font=ctk.CTkFont(size=14, weight="bold"))
        self.img_label_pre.grid(row=2, column=0, padx=10, pady=(10,5))
        self.img_frame_pre = ctk.CTkLabel(self.main_frame, text="No Image", width=320, height=180, fg_color="gray20", corner_radius=10)
        self.img_frame_pre.grid(row=3, column=0, padx=10, pady=10)

        self.img_label_post = ctk.CTkLabel(self.main_frame, text="Post-Flight (After)", font=ctk.CTkFont(size=14, weight="bold"))
        self.img_label_post.grid(row=2, column=1, padx=10, pady=(10,5))
        self.img_frame_post = ctk.CTkLabel(self.main_frame, text="No Image", width=320, height=180, fg_color="gray20", corner_radius=10)
        self.img_frame_post.grid(row=3, column=1, padx=10, pady=10)

    def start_task_thread(self):
        self.btn_run.configure(state="disabled")
        self.status_label.configure(text="Status: Flying...", text_color="yellow")
        self.log_box.delete("0.0", "end")
        self.log_box.insert("0.0", "Initializing task...\n")
        
        url = self.url_entry.get()
        selector = self.selector_entry.get()
        mode = self.mode_var.get()

        thread = threading.Thread(target=self.run_task, args=(url, selector, mode))
        thread.start()

    def run_task(self, url, selector, mode):
        try:
            result = self.atc.execute_task(url, selector, mode)
            self.after(0, self.update_ui, result)
        except Exception as e:
            self.after(0, self.update_ui_error, str(e))

    def update_ui(self, result):
        # Log Update
        pretty_json = json.dumps(result, indent=4)
        self.log_box.delete("0.0", "end")
        self.log_box.insert("0.0", pretty_json)

        # Status Update
        if result.get("result") == "Success":
            self.status_label.configure(text="Status: Mission Complete", text_color="green")
        else:
            self.status_label.configure(text="Status: Mission Failed", text_color="red")

        # Image Update
        if "screenshot_pre" in result and os.path.exists(result["screenshot_pre"]):
            self.show_image(result["screenshot_pre"], self.img_frame_pre)
        
        if "screenshot_post" in result and os.path.exists(result["screenshot_post"]):
            self.show_image(result["screenshot_post"], self.img_frame_post)
        
        self.btn_run.configure(state="normal")

    def update_ui_error(self, error_msg):
        self.log_box.insert("end", f"\nCRITICAL ERROR: {error_msg}")
        self.status_label.configure(text="Status: Crashed", text_color="red")
        self.btn_run.configure(state="normal")

    def show_image(self, path, frame_widget):
        try:
            pil_image = Image.open(path)
            # Resize keeping aspect ratio
            pil_image.thumbnail((400, 300))
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
            frame_widget.configure(image=ctk_image, text="")
        except Exception as e:
            frame_widget.configure(text=f"Img Error: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
