#!/usr/bin/env python3

"""
GUI wrapper for convert.sh - Audio Converter
Provides a modern graphical interface for converting audio in video files.
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
        self.root.title("🎬 Audio Converter - Video Audio Transcoder")
        self.root.geometry("950x800")
        self.root.minsize(800, 650)
        
        # Set icon if available
        try:
            icon_path = Path(__file__).parent / "icon.png"
            if icon_path.exists():
                icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon)
        except:
            pass
        
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
        
        # Apply modern theme and create UI
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        """Configure ttk styles for a modern look"""
        style = ttk.Style()
        
        # Try to use a modern theme
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # Configure button styles
        style.configure('Action.TButton', 
                       font=('Helvetica', 10, 'bold'),
                       padding=10)
        
        style.configure('Run.TButton',
                       font=('Helvetica', 11, 'bold'),
                       padding=15,
                       relief='raised')
        
        style.configure('Stop.TButton',
                       font=('Helvetica', 10),
                       padding=10)
        
        # Configure label styles
        style.configure('Title.TLabel',
                       font=('Helvetica', 14, 'bold'),
                       foreground='#1a237e')
        
        style.configure('Subtitle.TLabel',
                       font=('Helvetica', 10),
                       foreground='#666666')
        
        style.configure('Header.TLabel',
                       font=('Helvetica', 11, 'bold'),
                       foreground='#2c3e50',
                       padding=5)
        
        style.configure('Field.TLabel',
                       font=('Helvetica', 10))
        
        # Configure frame styles
        style.configure('Card.TFrame',
                       relief='groove',
                       borderwidth=2)
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # ===== TITLE SECTION =====
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(title_frame, 
                 text="Video Audio Converter", 
                 style='Title.TLabel').pack(anchor=tk.W)
        ttk.Label(title_frame, 
                 text="Transcode audio tracks in video files while preserving video quality", 
                 style='Subtitle.TLabel').pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        row += 2
        
        # ===== FILE SELECTION SECTION =====
        ttk.Label(main_frame, text="Source & Destination", 
                 style='Header.TLabel').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 12))
        row += 1
        
        # Input Directory
        ttk.Label(main_frame, text="Input Directory:", 
                 style='Field.TLabel').grid(row=row, column=0, sticky=tk.W, pady=10, padx=(15, 0))
        # Default to ~/Videos if it exists, else cwd
        default_videos = os.path.expanduser('~/Videos')
        if os.path.isdir(default_videos):
            default_input = default_videos
        else:
            default_input = os.getcwd()
        self.input_dir_var = tk.StringVar(value=default_input)
        input_entry = ttk.Entry(main_frame, textvariable=self.input_dir_var, 
                               font=('Helvetica', 10), width=50)
        input_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=10)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_input).grid(row=row, column=2, padx=(0, 10))
        row += 1
        
        # Output Directory
        ttk.Label(main_frame, text="Output Directory:", 
                 style='Field.TLabel').grid(row=row, column=0, sticky=tk.W, pady=10, padx=(15, 0))
        # Default output to ~/Videos if it exists, else empty
        if os.path.isdir(default_videos):
            default_output = default_videos
        else:
            default_output = ""
        self.output_dir_var = tk.StringVar(value=default_output)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_dir_var, 
                                font=('Helvetica', 10), width=50)
        output_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=10)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_output).grid(row=row, column=2, padx=(0, 10))
        row += 1

        ttk.Label(main_frame, text="Tip: Leave output directory empty to use input directory", 
                 font=("Helvetica", 9, "italic"), 
                 foreground="#757575").grid(row=row, column=1, sticky=tk.W, padx=10, pady=(0, 15))
        row += 1
        
        # ===== CONVERSION SETTINGS =====
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        ttk.Label(main_frame, text="Conversion Settings", 
                 style='Header.TLabel').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 12))
        row += 1
        
        # Settings in a grid
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=15)
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
        # Audio Codec
        ttk.Label(settings_frame, text="Audio Codec:", 
                 style='Field.TLabel').grid(row=0, column=0, sticky=tk.W, pady=10, padx=(0, 10))
        codec_frame = ttk.Frame(settings_frame)
        codec_frame.grid(row=0, column=1, sticky=tk.W, pady=10)
        self.audio_codec_var = tk.StringVar(value="lpcm")
        codec_combo = ttk.Combobox(codec_frame, textvariable=self.audio_codec_var, 
                                   values=["lpcm", "pcm_s16le", "ac3", "aac", "mp3", "opus"],
                                   width=18, state='readonly', font=('Helvetica', 10))
        codec_combo.pack(side=tk.LEFT)
        ttk.Label(codec_frame, text="(LPCM = PCM 16-bit LE)", 
                 font=("Helvetica", 8), foreground="#757575").pack(side=tk.LEFT, padx=10)
        
        # Parallel Jobs
        ttk.Label(settings_frame, text="Parallel Jobs:", 
                 style='Field.TLabel').grid(row=0, column=2, sticky=tk.W, pady=10, padx=(30, 10))
        jobs_frame = ttk.Frame(settings_frame)
        jobs_frame.grid(row=0, column=3, sticky=tk.W, pady=10)
        self.jobs_var = tk.StringVar(value="1")
        jobs_spinbox = ttk.Spinbox(jobs_frame, from_=1, to=16, textvariable=self.jobs_var, 
                                   width=10, font=('Helvetica', 10))
        jobs_spinbox.pack(side=tk.LEFT)
        ttk.Label(jobs_frame, text="(1-16 concurrent)", 
                 font=("Helvetica", 8), foreground="#757575").pack(side=tk.LEFT, padx=10)
        
        # Output Format
        ttk.Label(settings_frame, text="Output Format:", 
                 style='Field.TLabel').grid(row=1, column=0, sticky=tk.W, pady=10, padx=(0, 10))
        self.format_var = tk.StringVar(value="mov")
        format_combo = ttk.Combobox(settings_frame, textvariable=self.format_var, 
                                    values=["mov", "mp4", "mkv", "avi"],
                                    width=18, state='readonly', font=('Helvetica', 10))
        format_combo.grid(row=1, column=1, sticky=tk.W, pady=10)
        
        row += 1
        
        # ===== OPTIONS =====
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        ttk.Label(main_frame, text="Options", 
                 style='Header.TLabel').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        options_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="15")
        options_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=15)
        
        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, 
                       text="Dry Run (preview actions without executing)", 
                       variable=self.dry_run_var,
                       style='TCheckbutton').grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.keep_original_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, 
                       text="Keep Original Files (don't delete after conversion)", 
                       variable=self.keep_original_var).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.force_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, 
                       text="Force (transcode regardless of detected audio codec)", 
                       variable=self.force_var).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        row += 1
        
        # ===== CONTROL BUTTONS =====
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        row += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=15)
        
        self.run_button = ttk.Button(button_frame, text="Start Conversion", 
                                     command=self.run_conversion, 
                                     style='Run.TButton', width=22)
        self.run_button.pack(side=tk.LEFT, padx=8)

        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                      command=self.stop_conversion, 
                                      state=tk.DISABLED, 
                                      style='Stop.TButton', width=15)
        self.stop_button.pack(side=tk.LEFT, padx=8)
        
        ttk.Button(button_frame, text="Clear Output", 
                  command=self.clear_output, 
                  style='Action.TButton', width=15).pack(side=tk.LEFT, padx=8)
        
        row += 1
        
        # ===== OUTPUT DISPLAY =====
        ttk.Label(main_frame, text="Conversion Log", 
                 style='Header.TLabel').grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10, 10))
        row += 1
        
        # Create output text with custom colors
        output_frame = ttk.Frame(main_frame, relief='sunken', borderwidth=2)
        output_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=15)
        main_frame.rowconfigure(row, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            height=12, 
            width=100, 
            wrap=tk.WORD, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground="#264f78"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.output_text.tag_config("success", foreground="#4EC9B0")
        self.output_text.tag_config("error", foreground="#f48771")
        self.output_text.tag_config("info", foreground="#569cd6")
        self.output_text.tag_config("warning", foreground="#dcdcaa")
        
        row += 1
        
        # ===== STATUS BAR =====
        status_frame = ttk.Frame(main_frame, relief='groove', borderwidth=2)
        status_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(status_frame, text="Status:", 
                 font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT, padx=(10, 5))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                font=('Helvetica', 9), foreground="#2e7d32")
        status_label.pack(side=tk.LEFT, padx=5, pady=8)
        
    def browse_input(self):
        directory = filedialog.askdirectory(
            initialdir=self.input_dir_var.get(),
            title="Select Input Directory"
        )
        if directory:
            self.input_dir_var.set(directory)
            
    def browse_output(self):
        directory = filedialog.askdirectory(
            initialdir=self.output_dir_var.get() or self.input_dir_var.get(),
            title="Select Output Directory"
        )
        if directory:
            self.output_dir_var.set(directory)
            
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
        
    def append_output(self, text, tag=None):
        self.output_text.insert(tk.END, text, tag)
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
        self.append_output(f"Executing: {' '.join(cmd)}\n", "info")
        self.append_output("=" * 100 + "\n")
        
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
                # Color code certain lines
                tag = None
                if "✓" in line or "Converted:" in line or "success" in line.lower():
                    tag = "success"
                elif "✗" in line or "Error" in line or "failed" in line.lower():
                    tag = "error"
                elif "Found:" in line or "Detected" in line:
                    tag = "info"
                    
                self.root.after(0, self.append_output, line, tag)
                
            self.process.wait()
            return_code = self.process.returncode
            
            self.root.after(0, self.conversion_finished, return_code)
            
        except Exception as e:
            self.root.after(0, self.append_output, f"\nError: {str(e)}\n", "error")
            self.root.after(0, self.conversion_finished, -1)
            
    def conversion_finished(self, return_code):
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if return_code == 0:
            self.append_output("\n" + "=" * 100 + "\n")
            self.append_output("Conversion completed successfully!\n", "success")
            self.status_var.set("Conversion completed successfully")
            messagebox.showinfo("Success", "All files converted successfully!")
        else:
            self.append_output("\n" + "=" * 100 + "\n")
            self.append_output(f"Conversion failed with exit code {return_code}\n", "error")
            self.status_var.set(f"Conversion failed (exit code {return_code})")
            messagebox.showerror("Error", f"Conversion failed with exit code {return_code}")
            
    def stop_conversion(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.append_output("\n\nConversion stopped by user.\n", "warning")
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
