import os
import json
import shutil
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime


class PhotoOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Photos Organizer")
        self.root.geometry("640x480")
        self.root.configure(padx=20, pady=20)

        style = ttk.Style()
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 9, "italic"))

        self.months = {
            1: "styczeń", 2: "luty", 3: "marzec", 4: "kwiecień",
            5: "maj", 6: "czerwiec", 7: "lipiec", 8: "sierpień",
            9: "wrzesień", 10: "październik", 11: "listopad", 12: "grudzień"
        }
        self.ext_pattern = re.compile(r"\.(jpg|jpeg|png|mp4|mov|heic|webp|gif|avi)$", re.IGNORECASE)

        # Variables
        self.src_path = tk.StringVar()
        self.dst_path = tk.StringVar()
        self.file_op = tk.IntVar(value=0)

        ttk.Label(root, text="Source (Google Takeout Directory)", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 5))
        src_frame = ttk.Frame(root)
        src_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        ttk.Entry(src_frame, textvariable=self.src_path).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(src_frame, text="Browse", command=self.browse_src).pack(side="right")

        ttk.Label(root, text="Destination Directory", style="Header.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 5))
        dst_frame = ttk.Frame(root)
        dst_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        ttk.Entry(dst_frame, textvariable=self.dst_path).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(dst_frame, text="Browse", command=self.browse_dst).pack(side="right")

        ttk.Label(root, text="Operation Type", style="Header.TLabel").grid(row=4, column=0, sticky="w", pady=(0, 5))
        op_frame = ttk.Frame(root)
        op_frame.grid(row=5, column=0, sticky="w", pady=(0, 20))
        ttk.Radiobutton(op_frame, text="Copy Files", variable=self.file_op, value=0).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(op_frame, text="Move Files", variable=self.file_op, value=1).pack(side="left")

        self.start_btn = ttk.Button(root, text="START", command=self.process)
        self.start_btn.grid(row=6, column=0, sticky="ew", ipady=10)

        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate")
        self.progress.grid(row=7, column=0, sticky="ew", pady=(20, 5))

        self.status_label = ttk.Label(root, text="Ready", style="Status.TLabel")
        self.status_label.grid(row=8, column=0, sticky="w")

        root.columnconfigure(0, weight=1)

    def browse_src(self):
        path = filedialog.askdirectory()
        if path: self.src_path.set(path)

    def browse_dst(self):
        path = filedialog.askdirectory()
        if path: self.dst_path.set(path)

    def log(self, message):
        self.status_label.config(text=message)
        self.root.update()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def process(self):
        src, dst = self.src_path.get(), self.dst_path.get()
        if not src or not dst:
            messagebox.showwarning("Incomplete Paths", "Please select both source and destination folders.")
            return

        self.start_btn.state(['disabled'])
        global_metadata = {}
        stats = {"json_match": 0, "fallback": 0, "errors": 0}

        try:
            self.log("Step 1: Indexing JSON files (Global Scan)...")
            for root, _, files in os.walk(src):
                for f in files:
                    if f.lower().endswith('.json') and f.lower() != 'metadata.json':
                        try:
                            with open(os.path.join(root, f), 'r', encoding='utf-8') as jfile:
                                data = json.load(jfile)
                                title, ts = data.get('title'), data.get('photoTakenTime', {}).get('timestamp')
                                if title and ts:
                                    global_metadata[title] = datetime.fromtimestamp(int(ts))
                        except:
                            continue

            self.log("Step 2: Locating media...")
            media_files = []
            for root, _, files in os.walk(src):
                for f in files:
                    if self.ext_pattern.search(f):
                        media_files.append(os.path.join(root, f))

            total = len(media_files)
            self.progress["maximum"] = total

            for i, file_path in enumerate(media_files):
                file_name = os.path.basename(file_path)
                photo_date = global_metadata.get(file_name)

                if photo_date:
                    stats["json_match"] += 1
                else:
                    stats["fallback"] += 1
                    photo_date = datetime.fromtimestamp(os.path.getmtime(file_path))

                target_dir = os.path.join(dst, str(photo_date.year), self.months.get(photo_date.month))
                os.makedirs(target_dir, exist_ok=True)

                dest_path = os.path.join(target_dir, file_name)
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(file_name)
                    cnt = 1
                    while os.path.exists(os.path.join(target_dir, f"{base}_{cnt}{ext}")):
                        cnt += 1
                    dest_path = os.path.join(target_dir, f"{base}_{cnt}{ext}")

                try:
                    if self.file_op.get() == 0:
                        shutil.copy2(file_path, dest_path)
                    else:
                        shutil.move(file_path, dest_path)
                except:
                    stats["errors"] += 1

                if i % 10 == 0 or i == total - 1:
                    self.progress["value"] = i + 1
                    self.status_label.config(text=f"Moving/Copying: {i + 1}/{total}")
                    self.root.update()

            messagebox.showinfo("Done",f"Finished!\n\nMatches: {stats['json_match']}\nFallbacks: {stats['fallback']}\nErrors: {stats['errors']}")

        except Exception as e:
            messagebox.showerror("Critical Error", str(e))
        finally:
            self.start_btn.state(['!disabled'])
            self.log("Ready")
            self.progress["value"] = 0


if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap("")
    except:
        pass
    app = PhotoOrganizerGUI(root)
    root.mainloop()