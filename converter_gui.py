#!/usr/bin/env python3

"""
GUI wrapper for convert.sh - Audio Converter
Provides a simple graphical interface for converting audio in video files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import os
from pathlib import Path

class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Converter - AAC to PCM/AC3")
        self.root.geometry("800x700")
        
        # Get the directory where this script is located
        self.script_dir = Path(__file__).parent.absolute()
        self.convert_script = self.script_dir / "convert.sh"
        
        # Check if convert.sh exists
        if not self.convert_script.exists():
            messagebox.showerror("Error", f"convert.sh not found at {self.convert_script}")
            self.root.destroy()
            return
        
        self.is_running = False
        self.process = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Input Directory
        ttk.Label(main_frame, text="Input Directory:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.input_dir_var = tk.StringVar(value=os.getcwd())
        ttk.Entry(main_frame, textvariable=self.input_dir_var).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_input).grid(row=row, column=2, padx=5)
        row += 1
        
        # Output Directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value="")
        ttk.Entry(main_frame, textvariable=self.output_dir_var).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_output).grid(row=row, column=2, padx=5)
        ttk.Label(main_frame, text="(Leave empty to use input directory)", font=("", 8), foreground="gray").grid(row=row+1, column=1, sticky=tk.W, padx=5)
        row += 2
        
        # Audio Codec
        ttk.Label(main_frame, text="Audio Codec:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.audio_codec_var = tk.StringVar(value="lpcm")
        codec_frame = ttk.Frame(main_frame)
        codec_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Combobox(codec_frame, textvariable=self.audio_codec_var, 
                     values=["lpcm", "pcm_s16le", "ac3", "aac", "mp3", "opus"],
                     width=15).pack(side=tk.LEFT)
        ttk.Label(codec_frame, text="(lpcm = PCM 16-bit LE)", font=("", 8), foreground="gray").pack(side=tk.LEFT, padx=10)
        row += 1
        
        # Output Format
        ttk.Label(main_frame, text="Output Format:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="mov")
        ttk.Combobox(main_frame, textvariable=self.format_var, 
                     values=["mov", "mp4", "mkv", "avi"],
                     width=15).grid(row=row, column=1, sticky=tk.W, padx=5)
        row += 1
        
        # Parallel Jobs
        ttk.Label(main_frame, text="Parallel Jobs:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.jobs_var = tk.StringVar(value="1")
        jobs_spinbox = ttk.Spinbox(main_frame, from_=1, to=16, textvariable=self.jobs_var, width=15)
        jobs_spinbox.grid(row=row, column=1, sticky=tk.W, padx=5)
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Options
        ttk.Label(main_frame, text="Options:", font=("", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Dry Run (show what would be done without actually doing it)", 
                       variable=self.dry_run_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=20)
        row += 1
        
        self.keep_original_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Keep Original Files (don't delete after conversion)", 
                       variable=self.keep_original_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=20)
        row += 1
        
        self.force_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Force (transcode regardless of detected audio codec)", 
                       variable=self.force_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=20)
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        self.run_button = ttk.Button(button_frame, text="Start Conversion", command=self.run_conversion, width=20)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_conversion, state=tk.DISABLED, width=15)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Clear Output", command=self.clear_output, width=15).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Output Display
        ttk.Label(main_frame, text="Output:", font=("", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        # Scrolled Text for output
        self.output_text = scrolledtext.ScrolledText(main_frame, height=15, width=80, wrap=tk.WORD, 
                                                      font=("Courier", 9))
        self.output_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(row, weight=1)
        row += 1
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
    def browse_input(self):
        directory = filedialog.askdirectory(initialdir=self.input_dir_var.get())
        if directory:
            self.input_dir_var.set(directory)
            
    def browse_output(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get() or self.input_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
            
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
        
    def append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.update()
        
    def build_command(self):
        """Build the command line for convert.sh"""
        cmd = ["bash", str(self.convert_script)]
        
        # Add input directory
        cmd.extend(["-i", self.input_dir_var.get()])
        
        # Add output directory if specified
        if self.output_dir_var.get():
            cmd.extend(["-o", self.output_dir_var.get()])
            
        # Add audio codec
        cmd.extend(["-a", self.audio_codec_var.get()])
        
        # Add format
        cmd.extend(["-f", self.format_var.get()])
        
        # Add jobs
        cmd.extend(["-j", self.jobs_var.get()])
        
        # Add flags
        if self.dry_run_var.get():
            cmd.append("-n")
        if self.keep_original_var.get():
            cmd.append("-k")
        if self.force_var.get():
            cmd.append("-F")
            
        return cmd
        
    def run_conversion(self):
        if self.is_running:
            return
            
        # Validate input directory
        if not os.path.isdir(self.input_dir_var.get()):
            messagebox.showerror("Error", "Input directory does not exist!")
            return
            
        self.is_running = True
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("Running conversion...")
        
        # Clear previous output
        self.clear_output()
        
        # Build command
        cmd = self.build_command()
        self.append_output(f"Running: {' '.join(cmd)}\n")
        self.append_output("-" * 80 + "\n")
        
        # Run in separate thread
        thread = threading.Thread(target=self.run_conversion_thread, args=(cmd,))
        thread.daemon = True
        thread.start()
        
    def run_conversion_thread(self, cmd):
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read output line by line
            for line in self.process.stdout:
                if self.process.poll() is not None and not line:
                    break
                self.root.after(0, self.append_output, line)
                
            self.process.wait()
            return_code = self.process.returncode
            
            self.root.after(0, self.conversion_finished, return_code)
            
        except Exception as e:
            self.root.after(0, self.append_output, f"\nError: {str(e)}\n")
            self.root.after(0, self.conversion_finished, -1)
            
    def conversion_finished(self, return_code):
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if return_code == 0:
            self.append_output("\n" + "=" * 80 + "\n")
            self.append_output("✓ Conversion completed successfully!\n")
            self.status_var.set("Conversion completed successfully")
        else:
            self.append_output("\n" + "=" * 80 + "\n")
            self.append_output(f"✗ Conversion failed with exit code {return_code}\n")
            self.status_var.set(f"Conversion failed (exit code {return_code})")
            
    def stop_conversion(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.append_output("\n\nConversion stopped by user.\n")
            self.status_var.set("Conversion stopped")
            self.is_running = False
            self.run_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
