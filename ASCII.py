import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pyfiglet
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageTk
import numpy as np
import cv2
import threading
import time

class EnhancedASCIIGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced ASCII Art Generator")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.setup_image_processing_vars()
        self.setup_video_vars()
        self.configure_styles()
        self.create_widgets()
        
        # Add window resize binding
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_image_processing_vars(self):
        self.CHAR_SET = "@%#*+=-:. "
        self.ASPECT_RATIO = 0.5
        self.edge_detection = False
        self.dithering = False

        # Tkinter variables with improved default values
        self.char_set_var = tk.StringVar(value=self.CHAR_SET)
        self.img_width_var = tk.IntVar(value=1)  # Default width set to 1
        self.img_height_var = tk.IntVar(value=1)  # Default height set to 1
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.sharpness_var = tk.DoubleVar(value=1.0)

        # Text conversion variables
        self.text_input_var = tk.StringVar()
        self.font_var = tk.StringVar(value="standard")
        self.text_width_var = tk.IntVar(value=80)

    def setup_video_vars(self):
        self.video_playing = False
        self.video_thread = None
        self.fps_var = tk.IntVar(value=30)
        self.video_delay = 1/30

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#1e1e1e', foreground='white')
        style.configure('TEntry', fieldbackground='#313233', foreground='white')
        style.configure('TCombobox', fieldbackground='#313233', foreground='white')
        style.configure('TButton', background='#007AFF', foreground='white')
        style.map('TButton', background=[('active', '#0063CC')])

    def create_widgets(self):
        self.create_title_bar()
        self.create_notebook()
        self.create_image_tab()
        self.create_text_tab()
        self.create_video_tab()

    def create_title_bar(self):
        title_bar = tk.Frame(self.root, bg='#313233', height=40)
        title_bar.pack(fill=tk.X)

    def create_notebook(self):
        self.tab_control = ttk.Notebook(self.root)
        self.text_tab = ttk.Frame(self.tab_control)
        self.image_tab = ttk.Frame(self.tab_control)
        self.video_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.text_tab, text='Text to ASCII')
        self.tab_control.add(self.image_tab, text='Image to ASCII')
        self.tab_control.add(self.video_tab, text='Video to ASCII')
        self.tab_control.pack(expand=1, fill="both")

    def create_image_tab(self):
        control_frame = tk.Frame(self.image_tab, bg='#1e1e1e')
        control_frame.pack(fill=tk.X, pady=10)
        
        # Image controls
        img_top_frame = tk.Frame(control_frame, bg='#1e1e1e')
        img_top_frame.pack(fill=tk.X)
        ttk.Button(img_top_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        self.img_path = ttk.Entry(img_top_frame, width=60)
        self.img_path.pack(side=tk.LEFT, padx=5)
        self.preview_label = tk.Label(img_top_frame, bg='#313233', width=40, height=10)
        self.preview_label.pack(side=tk.RIGHT, padx=10)

        # Slider controls
        slider_frame = tk.Frame(control_frame, bg='#1e1e1e')
        slider_frame.pack(fill=tk.X, pady=10)
        
        self.create_slider(slider_frame, "Width:", self.img_width_var, 50, 300)
        self.create_slider(slider_frame, "Height:", self.img_height_var, 30, 150)
        self.create_slider(slider_frame, "Contrast:", self.contrast_var, 0.5, 2.0, resolution=0.1)
        self.create_slider(slider_frame, "Brightness:", self.brightness_var, 0.5, 2.0, resolution=0.1)
        self.create_slider(slider_frame, "Sharpness:", self.sharpness_var, 0.5, 2.0, resolution=0.1)

        # Checkboxes
        checkbox_frame = tk.Frame(control_frame, bg='#1e1e1e')
        checkbox_frame.pack(fill=tk.X, pady=5)
        self.edge_var = tk.BooleanVar()
        ttk.Checkbutton(checkbox_frame, text="Edge Detection", variable=self.edge_var).pack(side=tk.LEFT, padx=5)
        self.dither_var = tk.BooleanVar()
        ttk.Checkbutton(checkbox_frame, text="Dithering", variable=self.dither_var).pack(side=tk.LEFT, padx=5)

        # Output controls
        output_frame = tk.Frame(self.image_tab, bg='#1e1e1e')
        output_frame.pack(fill=tk.X, pady=10)
        ttk.Combobox(output_frame, textvariable=self.char_set_var, values=[
            "@%#*+=-:. ", " .:-=+*#%@", "█▓▒░ ", "01", "🀰🀱🀲🀳🀴🀵🀶🀷"
        ]).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="Generate ASCII", command=self.generate_ascii_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="Save", command=self.save_ascii_image).pack(side=tk.LEFT, padx=5)
        
        # Monospace output
        self.image_output = scrolledtext.ScrolledText(
            self.image_tab, 
            bg='#313233', 
            fg='white', 
            wrap=tk.NONE,
            font=('Courier New', 10)
        )
        self.image_output.pack(fill=tk.BOTH, expand=True)

    def create_video_tab(self):
        control_frame = tk.Frame(self.video_tab, bg='#1e1e1e')
        control_frame.pack(fill=tk.X, pady=10)
        
        # Video controls
        video_controls = tk.Frame(control_frame, bg='#1e1e1e')
        video_controls.pack(fill=tk.X, padx=5)
        
        ttk.Button(video_controls, text="Load Video", command=self.load_video).pack(side=tk.LEFT, padx=5)
        self.video_path = ttk.Entry(video_controls, width=60)
        self.video_path.pack(side=tk.LEFT, padx=5)
        
        # Video playback controls
        playback_frame = tk.Frame(control_frame, bg='#1e1e1e')
        playback_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(playback_frame, text="Play", command=self.play_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(playback_frame, text="Stop", command=self.stop_video).pack(side=tk.LEFT, padx=5)
        
        # FPS control
        ttk.Label(playback_frame, text="FPS:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(playback_frame, textvariable=self.fps_var, width=5).pack(side=tk.LEFT)
        
        # Video output
        self.video_output = scrolledtext.ScrolledText(
            self.video_tab,
            bg='#313233',
            fg='white',
            wrap=tk.NONE,
            font=('Courier New', 10)
        )
        self.video_output.pack(fill=tk.BOTH, expand=True)

    def create_text_tab(self):
        input_frame = tk.Frame(self.text_tab, bg='#1e1e1e')
        input_frame.pack(pady=20, fill=tk.X)
        
        ttk.Label(input_frame, text="Enter Text:").pack(side=tk.LEFT, padx=10)
        ttk.Entry(input_frame, textvariable=self.text_input_var, width=40).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(input_frame, text="Font:").pack(side=tk.LEFT, padx=10)
        self.font_selector = ttk.Combobox(input_frame, textvariable=self.font_var, width=15)
        self.font_selector['values'] = pyfiglet.FigletFont.getFonts()
        self.font_selector.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(input_frame, text="Width:").pack(side=tk.LEFT, padx=10)
        ttk.Entry(input_frame, textvariable=self.text_width_var, width=5).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(input_frame, text="Generate", command=self.generate_ascii_text).pack(side=tk.LEFT, padx=10)
        
        # Monospace output
        self.text_output = scrolledtext.ScrolledText(
            self.text_tab, 
            bg='#313233', 
            fg='white', 
            wrap=tk.WORD,
            font=('Courier New', 10)
        )
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_slider(self, parent, label, var, from_, to_, resolution=1):
        frame = tk.Frame(parent, bg='#1e1e1e')
        frame.pack(side=tk.LEFT, padx=10)
        tk.Label(frame, text=label, bg='#1e1e1e', fg='white').pack()
        
        # Create and pack the entry widget for direct value input
        entry = ttk.Entry(frame, textvariable=var, width=5)
        entry.pack()
        
        slider = ttk.Scale(
            frame,
            from_=from_,
            to=to_,
            variable=var,
            orient='horizontal',
            length=150
        )
        slider.pack()
        
        # Bind the slider to update both the variable and entry
        def on_slider_change(event):
            value = float(slider.get())
            rounded_value = round(value/resolution)*resolution
            var.set(rounded_value)
            
        slider.bind('<B1-Motion>', on_slider_change)
        slider.bind('<Button-1>', on_slider_change)
    
        # Bind the entry to update both the variable and slider
        def on_entry_change(*args):
            try:
                value = float(var.get())
                slider.set(value)
            except ValueError:
                pass
                
            var.trace('w', on_entry_change)
    
            
            value_label = tk.Label(frame, textvariable=var, bg='#1e1e1e', fg='white')
            value_label.pack()

    def load_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.img_path.delete(0, tk.END)
            self.img_path.insert(0, path)
            self.show_image_preview(path)

    def load_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if path:
            self.video_path.delete(0, tk.END)
            self.video_path.insert(0, path)
            self.stop_video()

    def play_video(self):
        if not self.video_playing and self.video_path.get():
            self.video_playing = True
            self.video_thread = threading.Thread(target=self.process_video)
            self.video_thread.daemon = True
            self.video_thread.start()

    def stop_video(self):
        self.video_playing = False
        if self.video_thread:
            self.video_thread.join(timeout=1.0)

    def process_video(self):
        cap = cv2.VideoCapture(self.video_path.get())
        if not cap.isOpened():
            messagebox.showerror("Error", "Failed to open video file")
            return

        try:
            while self.video_playing:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                processed_frame = self.preprocess_image(image)
                ascii_frame = self.image_to_ascii(processed_frame)
                
                self.root.after(0, self.update_video_output, ascii_frame)
                time.sleep(1/self.fps_var.get())

        finally:
            cap.release()

    def update_video_output(self, ascii_frame):
        self.video_output.delete(1.0, tk.END)
        self.video_output.insert(tk.END, ascii_frame)

    def show_image_preview(self, path):
        try:
            image = Image.open(path)
            image.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(image)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{str(e)}")

    def generate_ascii_text(self):
        try:
            text = self.text_input_var.get()
            font = self.font_var.get()
            width = self.text_width_var.get()
            
            if not text:
                messagebox.showerror("Error", "Please enter some text!")
                return
                
            ascii_art = pyfiglet.Figlet(font=font, width=width).renderText(text)
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.INSERT, ascii_art)
        except Exception as e:
            messagebox.showerror("Error", f"Text conversion failed:\n{str(e)}")

    def generate_ascii_image(self):
        try:
            image = Image.open(self.img_path.get())
            image = self.preprocess_image(image)
            ascii_art = self.image_to_ascii(image)
            self.image_output.delete(1.0, tk.END)
            self.image_output.insert(tk.INSERT, ascii_art)
        except Exception as e:
             messagebox.showerror("Error", f"Failed to generate ASCII art:\n{str(e)}")


    def preprocess_image(self, image):
        image = image.convert("L")
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self.contrast_var.get())
        
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.brightness_var.get())
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(self.sharpness_var.get())
    
        if self.edge_var.get():
            image = image.filter(ImageFilter.FIND_EDGES)
    
        if self.dither_var.get():
            image = image.convert("1")
    
        target_width = max(1, int(self.img_width_var.get()))
        target_height = max(1, int(self.img_height_var.get() * self.ASPECT_RATIO))
        image = image.resize((target_width, target_height), Image.LANCZOS)
    
        return image
    



    def image_to_ascii(self, image):
        pixels = np.array(image)
        chars = np.array(list(self.char_set_var.get()))
        normalized = (pixels / 255 * (len(chars) - 1)).astype(int)
        ascii_matrix = chars[normalized]
        return "\n".join("".join(row) for row in ascii_matrix)

    def save_ascii_image(self):
        content = self.image_output.get(1.0, tk.END)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Success", "ASCII art saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def on_window_resize(self, event):
        if hasattr(self, 'video_output'):
            new_width = event.width // 8  # Increased from 10 to 8 for larger width
            new_height = event.height // 15  # Increased from 20 to 15 for larger height
            
            self.img_width_var.set(new_width)
            self.img_height_var.set(new_height)
            
        self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedASCIIGenerator(root)
    root.mainloop()
