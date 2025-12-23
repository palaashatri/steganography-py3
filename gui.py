#!/usr/bin/env python3
"""
Tkinter GUI for Steganography Application
Provides a user-friendly interface for image, MP3, and MP4 steganography
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import subprocess
import threading
from pathlib import Path


class SteganographyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Steganography Suite - GUI")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('aqua' if os.name == 'posix' else 'clam')
        
        # Variables for file paths
        self.image_cover_path = tk.StringVar()
        self.image_stego_path = tk.StringVar()
        self.mp3_path = tk.StringVar()
        self.mp4_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.secret_image_path = tk.StringVar()
        self.secret_file_path = tk.StringVar()
        self.secret_mp3_path = tk.StringVar()
        
        self.message_text = tk.StringVar()
        self.password_text = tk.StringVar()
        
        # Create notebook with tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_image_encode_tab()
        self.create_image_decode_tab()
        self.create_mp3_encode_tab()
        self.create_mp3_decode_tab()
        self.create_mp4_encode_tab()
        self.create_mp4_decode_tab()
        
        # Status bar
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        self.status_label = ttk.Label(self.status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X)
    
    def create_image_encode_tab(self):
        """Create Image Encode tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Image Encode")
        
        # Main content frame
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Cover image selection
        ttk.Label(content, text="Cover Image:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=self.image_cover_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(content, text="Browse", command=self.select_cover_image).grid(row=0, column=2, padx=5)
        
        # Secret data section
        ttk.Label(content, text="Secret Data:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        
        # Text option
        ttk.Label(content, text="Message:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(content, textvariable=self.message_text, width=50).grid(row=2, column=1, columnspan=2, padx=5)
        
        # Image option
        ttk.Label(content, text="Secret Image:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=self.secret_image_path, width=50).grid(row=3, column=1, padx=5)
        ttk.Button(content, text="Browse", command=self.select_secret_image).grid(row=3, column=2, padx=5)
        
        # File option
        ttk.Label(content, text="Secret File:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=self.secret_file_path, width=50).grid(row=4, column=1, padx=5)
        ttk.Button(content, text="Browse", command=self.select_secret_file).grid(row=4, column=2, padx=5)
        
        # Options section
        ttk.Label(content, text="Options:", font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        
        # Password
        ttk.Label(content, text="Password (optional):").grid(row=6, column=0, sticky=tk.W)
        ttk.Entry(content, textvariable=self.password_text, width=50, show="*").grid(row=6, column=1, columnspan=2, padx=5)
        
        # Output file
        ttk.Label(content, text="Output Image:").grid(row=7, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=self.image_stego_path, width=50).grid(row=7, column=1, padx=5)
        ttk.Button(content, text="Browse", command=self.select_output_image).grid(row=7, column=2, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.grid(row=8, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Embed", command=self.embed_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.clear_vars([self.image_cover_path, self.image_stego_path, self.message_text, self.secret_image_path, self.secret_file_path, self.password_text])).pack(side=tk.LEFT, padx=5)
    
    def create_image_decode_tab(self):
        """Create Image Decode tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Image Decode")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input image
        ttk.Label(content, text="Stego Image:").grid(row=0, column=0, sticky=tk.W, pady=5)
        input_var = tk.StringVar()
        ttk.Entry(content, textvariable=input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(input_var, "Select Stego Image", "png jpg gif bmp")).grid(row=0, column=2, padx=5)
        
        # Password
        password_var = tk.StringVar()
        ttk.Label(content, text="Password (optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=password_var, width=50, show="*").grid(row=1, column=1, columnspan=2, padx=5)
        
        # Output
        output_var = tk.StringVar()
        ttk.Label(content, text="Output File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=output_var, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_save_file(output_var, "Select Output")).grid(row=2, column=2, padx=5)
        
        # Result display
        ttk.Label(content, text="Extracted Data:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        result_text = scrolledtext.ScrolledText(content, height=15, width=70)
        result_text.grid(row=4, column=0, columnspan=3, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Extract", command=lambda: self.extract_image(input_var, password_var, output_var, result_text)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.clear_vars([input_var, password_var, output_var])).pack(side=tk.LEFT, padx=5)
    
    def create_mp3_encode_tab(self):
        """Create MP3 Encode tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="MP3 Encode")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input MP3
        ttk.Label(content, text="Input MP3:").grid(row=0, column=0, sticky=tk.W, pady=5)
        mp3_var = tk.StringVar()
        ttk.Entry(content, textvariable=mp3_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(mp3_var, "Select MP3", "mp3")).grid(row=0, column=2, padx=5)
        
        # Secret data
        ttk.Label(content, text="Secret Data:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        
        msg_var = tk.StringVar()
        ttk.Label(content, text="Message:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(content, textvariable=msg_var, width=50).grid(row=2, column=1, columnspan=2, padx=5)
        
        img_var = tk.StringVar()
        ttk.Label(content, text="Image:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=img_var, width=50).grid(row=3, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(img_var, "Select Image", "png jpg gif")).grid(row=3, column=2, padx=5)
        
        file_var = tk.StringVar()
        ttk.Label(content, text="File:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=file_var, width=50).grid(row=4, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(file_var, "Select File")).grid(row=4, column=2, padx=5)
        
        # Password
        pwd_var = tk.StringVar()
        ttk.Label(content, text="Password (optional):").grid(row=5, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Entry(content, textvariable=pwd_var, width=50, show="*").grid(row=5, column=1, columnspan=2, padx=5)
        
        # Output
        out_var = tk.StringVar()
        ttk.Label(content, text="Output MP3:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=out_var, width=50).grid(row=6, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_save_file(out_var, "Save MP3", "mp3")).grid(row=6, column=2, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Embed", command=lambda: self.embed_mp3(mp3_var, msg_var, img_var, file_var, pwd_var, out_var)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.clear_vars([mp3_var, msg_var, img_var, file_var, pwd_var, out_var])).pack(side=tk.LEFT, padx=5)
    
    def create_mp3_decode_tab(self):
        """Create MP3 Decode tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="MP3 Decode")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input MP3
        input_var = tk.StringVar()
        ttk.Label(content, text="Input MP3:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(input_var, "Select MP3", "mp3")).grid(row=0, column=2, padx=5)
        
        # Password
        password_var = tk.StringVar()
        ttk.Label(content, text="Password (optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=password_var, width=50, show="*").grid(row=1, column=1, columnspan=2, padx=5)
        
        # Output
        output_var = tk.StringVar()
        ttk.Label(content, text="Output File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=output_var, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_save_file(output_var, "Select Output")).grid(row=2, column=2, padx=5)
        
        # Result display
        ttk.Label(content, text="Extracted Data:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        result_text = scrolledtext.ScrolledText(content, height=15, width=70)
        result_text.grid(row=4, column=0, columnspan=3, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Extract", command=lambda: self.extract_mp3(input_var, password_var, output_var, result_text)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.clear_vars([input_var, password_var, output_var])).pack(side=tk.LEFT, padx=5)
    
    def create_mp4_encode_tab(self):
        """Create MP4 Encode tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="MP4 Encode")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input MP4
        mp4_var = tk.StringVar()
        ttk.Label(content, text="Input MP4:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=mp4_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(mp4_var, "Select MP4", "mp4 mov")).grid(row=0, column=2, padx=5)
        
        # Secret data
        ttk.Label(content, text="Secret Data:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(15, 5))
        
        msg_var = tk.StringVar()
        ttk.Label(content, text="Message:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(content, textvariable=msg_var, width=50).grid(row=2, column=1, columnspan=2, padx=5)
        
        img_var = tk.StringVar()
        ttk.Label(content, text="Image:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=img_var, width=50).grid(row=3, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(img_var, "Select Image", "png jpg gif")).grid(row=3, column=2, padx=5)
        
        mp3_var = tk.StringVar()
        ttk.Label(content, text="MP3:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=mp3_var, width=50).grid(row=4, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(mp3_var, "Select MP3", "mp3")).grid(row=4, column=2, padx=5)
        
        # Password
        pwd_var = tk.StringVar()
        ttk.Label(content, text="Password (optional):").grid(row=5, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Entry(content, textvariable=pwd_var, width=50, show="*").grid(row=5, column=1, columnspan=2, padx=5)
        
        # Output
        out_var = tk.StringVar()
        ttk.Label(content, text="Output MP4:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=out_var, width=50).grid(row=6, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_save_file(out_var, "Save MP4", "mp4")).grid(row=6, column=2, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Embed", command=lambda: self.embed_mp4(mp4_var, msg_var, img_var, mp3_var, pwd_var, out_var)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.clear_vars([mp4_var, msg_var, img_var, mp3_var, pwd_var, out_var])).pack(side=tk.LEFT, padx=5)
    
    def create_mp4_decode_tab(self):
        """Create MP4 Decode tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="MP4 Decode")
        
        content = ttk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input MP4
        input_var = tk.StringVar()
        ttk.Label(content, text="Input MP4:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_file(input_var, "Select MP4", "mp4 mov")).grid(row=0, column=2, padx=5)
        
        # Password
        password_var = tk.StringVar()
        ttk.Label(content, text="Password (optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=password_var, width=50, show="*").grid(row=1, column=1, columnspan=2, padx=5)
        
        # Output
        output_var = tk.StringVar()
        ttk.Label(content, text="Output File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(content, textvariable=output_var, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(content, text="Browse", command=lambda: self.select_save_file(output_var, "Select Output")).grid(row=2, column=2, padx=5)
        
        # Result display
        ttk.Label(content, text="Extracted Data:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        result_text = scrolledtext.ScrolledText(content, height=15, width=70)
        result_text.grid(row=4, column=0, columnspan=3, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Extract", command=lambda: self.extract_mp4(input_var, password_var, output_var, result_text)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.clear_vars([input_var, password_var, output_var])).pack(side=tk.LEFT, padx=5)
    
    # File selection methods
    def select_cover_image(self):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file:
            self.image_cover_path.set(file)
    
    def select_secret_image(self):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file:
            self.secret_image_path.set(file)
    
    def select_secret_file(self):
        file = filedialog.askopenfilename(title="Select Secret File")
        if file:
            self.secret_file_path.set(file)
    
    def select_output_image(self):
        file = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPG files", "*.jpg")])
        if file:
            self.image_stego_path.set(file)
    
    def select_file(self, var, title, filetypes="*"):
        """Generic file selection"""
        if filetypes == "*":
            file = filedialog.askopenfilename(title=title)
        else:
            type_list = [f"*.{ft}" for ft in filetypes.split()]
            file = filedialog.askopenfilename(title=title, filetypes=[(filetypes, " ".join(type_list))])
        if file:
            var.set(file)
    
    def select_save_file(self, var, title, filetype="*"):
        """Save file dialog"""
        if filetype == "*":
            file = filedialog.asksaveasfilename(title=title)
        else:
            file = filedialog.asksaveasfilename(title=title, defaultextension=f".{filetype}", filetypes=[(filetype.upper(), f"*.{filetype}")])
        if file:
            var.set(file)
    
    # Execution methods
    def run_command(self, cmd, callback=None):
        """Run command in background thread"""
        def thread_func():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
                if result.returncode == 0:
                    self.update_status(f"✓ Success: {' '.join(cmd[2:5])}")
                    if callback:
                        callback(True, result.stdout)
                else:
                    self.update_status(f"✗ Error: {result.stderr[:100]}")
                    if callback:
                        callback(False, result.stderr)
            except Exception as e:
                self.update_status(f"✗ Exception: {str(e)[:100]}")
                if callback:
                    callback(False, str(e))
        
        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def clear_vars(self, vars):
        """Clear variables"""
        for var in vars:
            var.set("")
    
    # Embedding operations
    def embed_image(self):
        """Embed data in image"""
        if not self.image_cover_path.get():
            messagebox.showerror("Error", "Please select a cover image")
            return
        if not self.image_stego_path.get():
            messagebox.showerror("Error", "Please select output path")
            return
        
        msg = self.message_text.get()
        img = self.secret_image_path.get()
        file = self.secret_file_path.get()
        pwd = self.password_text.get()
        
        if not (msg or img or file):
            messagebox.showerror("Error", "Please provide message, image, or file to embed")
            return
        
        cmd = ["python3", "1_Implementation/app.py", "encode", "--image", self.image_cover_path.get(), "--out", self.image_stego_path.get()]
        
        if msg:
            cmd.extend(["--message", msg])
        elif img:
            cmd.extend(["--image", img])
        elif file:
            cmd.extend(["--file", file])
        
        if pwd:
            cmd.extend(["--password", pwd])
        
        self.update_status("Embedding data in image...")
        self.run_command(cmd, self.show_result)
    
    def extract_image(self, input_var, password_var, output_var, result_text):
        """Extract data from image"""
        if not input_var.get():
            messagebox.showerror("Error", "Please select a stego image")
            return
        if not output_var.get():
            messagebox.showerror("Error", "Please select output path")
            return
        
        cmd = ["python3", "1_Implementation/app.py", "decode", "--image", input_var.get(), "--out", output_var.get()]
        
        if password_var.get():
            cmd.extend(["--password", password_var.get()])
        
        def callback(success, output):
            if success:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"Extraction successful!\n\nOutput: {output}")
                messagebox.showinfo("Success", "Data extracted successfully!")
            else:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"Error: {output}")
                messagebox.showerror("Error", f"Extraction failed:\n{output}")
        
        self.update_status("Extracting data from image...")
        self.run_command(cmd, callback)
    
    def embed_mp3(self, mp3_var, msg_var, img_var, file_var, pwd_var, out_var):
        """Embed data in MP3"""
        if not mp3_var.get():
            messagebox.showerror("Error", "Please select input MP3")
            return
        if not out_var.get():
            messagebox.showerror("Error", "Please select output MP3")
            return
        
        msg = msg_var.get()
        img = img_var.get()
        file = file_var.get()
        
        if not (msg or img or file):
            messagebox.showerror("Error", "Please provide message, image, or file to embed")
            return
        
        cmd = ["python3", "1_Implementation/app.py", "mp3-encode", "--mp3", mp3_var.get(), "--out", out_var.get()]
        
        if msg:
            cmd.extend(["--message", msg])
        elif img:
            cmd.extend(["--image", img])
        elif file:
            cmd.extend(["--file", file])
        
        if pwd_var.get():
            cmd.extend(["--password", pwd_var.get()])
        
        self.update_status("Embedding data in MP3...")
        self.run_command(cmd, self.show_result)
    
    def extract_mp3(self, input_var, password_var, output_var, result_text):
        """Extract data from MP3"""
        if not input_var.get():
            messagebox.showerror("Error", "Please select input MP3")
            return
        if not output_var.get():
            messagebox.showerror("Error", "Please select output path")
            return
        
        cmd = ["python3", "1_Implementation/app.py", "mp3-decode", "--mp3", input_var.get(), "--out", output_var.get()]
        
        if password_var.get():
            cmd.extend(["--password", password_var.get()])
        
        def callback(success, output):
            if success:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, "Extraction successful!")
                messagebox.showinfo("Success", "Data extracted successfully!")
            else:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"Error: {output}")
                messagebox.showerror("Error", f"Extraction failed:\n{output}")
        
        self.update_status("Extracting data from MP3...")
        self.run_command(cmd, callback)
    
    def embed_mp4(self, mp4_var, msg_var, img_var, mp3_var, pwd_var, out_var):
        """Embed data in MP4"""
        if not mp4_var.get():
            messagebox.showerror("Error", "Please select input MP4")
            return
        if not out_var.get():
            messagebox.showerror("Error", "Please select output MP4")
            return
        
        msg = msg_var.get()
        img = img_var.get()
        mp3 = mp3_var.get()
        
        if not (msg or img or mp3):
            messagebox.showerror("Error", "Please provide message, image, or MP3 to embed")
            return
        
        cmd = ["python3", "1_Implementation/app.py", "mp4-encode", "--mp4", mp4_var.get(), "--out", out_var.get()]
        
        if msg:
            cmd.extend(["--message", msg])
        elif img:
            cmd.extend(["--image", img])
        elif mp3:
            cmd.extend(["--mp3", mp3])
        
        if pwd_var.get():
            cmd.extend(["--password", pwd_var.get()])
        
        self.update_status("Embedding data in MP4...")
        self.run_command(cmd, self.show_result)
    
    def extract_mp4(self, input_var, password_var, output_var, result_text):
        """Extract data from MP4"""
        if not input_var.get():
            messagebox.showerror("Error", "Please select input MP4")
            return
        if not output_var.get():
            messagebox.showerror("Error", "Please select output path")
            return
        
        cmd = ["python3", "1_Implementation/app.py", "mp4-decode", "--mp4", input_var.get(), "--out", output_var.get()]
        
        if password_var.get():
            cmd.extend(["--password", password_var.get()])
        
        def callback(success, output):
            if success:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, "Extraction successful!")
                messagebox.showinfo("Success", "Data extracted successfully!")
            else:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"Error: {output}")
                messagebox.showerror("Error", f"Extraction failed:\n{output}")
        
        self.update_status("Extracting data from MP4...")
        self.run_command(cmd, callback)
    
    def show_result(self, success, output):
        """Show operation result"""
        if success:
            messagebox.showinfo("Success", "Operation completed successfully!")
        else:
            messagebox.showerror("Error", f"Operation failed:\n{output[:500]}")


def main():
    root = tk.Tk()
    app = SteganographyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
