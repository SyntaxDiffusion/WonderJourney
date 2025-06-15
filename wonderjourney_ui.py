import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import threading
import json
import yaml

class WonderJourneyUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WonderJourney - 3D Scene Generator")
        
        # Make window resizable and set minimum size
        self.root.minsize(1000, 700)
        self.root.geometry("1200x800")
        
        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.openai_api_key = tk.StringVar()
        self.scene_description = tk.StringVar(value="Library interior with shelves packed with ancient books")
        self.process = None
        
        self.load_settings()
        self.create_widgets()
        
    def create_widgets(self):
        # Create main container with scrollbar
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Main frame inside scrollable area
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎨 WonderJourney 3D Scene Generator", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0,20))
        
        # GPU Status
        gpu_frame = ttk.LabelFrame(main_frame, text="GPU Status", padding=10)
        gpu_frame.pack(fill="x", pady=5)
        
        self.gpu_status = tk.StringVar(value="Checking GPU...")
        gpu_label = ttk.Label(gpu_frame, textvariable=self.gpu_status)
        gpu_label.pack()
        self.check_gpu_status()
        
        # API Key
        api_frame = ttk.LabelFrame(main_frame, text="OpenAI API Key (Required)", padding=10)
        api_frame.pack(fill="x", pady=5)
        
        ttk.Label(api_frame, text="Enter your OpenAI API key:").pack(anchor="w")
        api_entry = ttk.Entry(api_frame, textvariable=self.openai_api_key, show="*", width=60)
        api_entry.pack(fill="x", pady=2)
        
        # Image Upload
        image_frame = ttk.LabelFrame(main_frame, text="Input Image", padding=10)
        image_frame.pack(fill="x", pady=5)
        
        self.image_path = tk.StringVar()
        ttk.Label(image_frame, text="Select your input image:").pack(anchor="w")
        
        image_select_frame = ttk.Frame(image_frame)
        image_select_frame.pack(fill="x", pady=2)
        
        ttk.Entry(image_select_frame, textvariable=self.image_path, width=50).pack(side="left", fill="x", expand=True)
        ttk.Button(image_select_frame, text="Browse", command=self.browse_image).pack(side="right", padx=(5,0))
        
        # Scene Configuration
        scene_frame = ttk.LabelFrame(main_frame, text="Scene Configuration", padding=10)
        scene_frame.pack(fill="x", pady=5)
        
        ttk.Label(scene_frame, text="Content Prompt (what's in the scene):").pack(anchor="w")
        self.content_prompt = tk.StringVar(value="Alpine village, street, chalet, church")
        ttk.Entry(scene_frame, textvariable=self.content_prompt, width=60).pack(fill="x", pady=2)
        
        ttk.Label(scene_frame, text="Style Prompt:").pack(anchor="w", pady=(10,0))
        self.style_prompt = tk.StringVar(value="DSLR 35mm landscape")
        ttk.Entry(scene_frame, textvariable=self.style_prompt, width=60).pack(fill="x", pady=2)
        
        ttk.Label(scene_frame, text="Background Description:").pack(anchor="w", pady=(10,0))
        self.background_prompt = tk.StringVar(value="A small village with a church and a clock tower surrounded by mountains")
        ttk.Entry(scene_frame, textvariable=self.background_prompt, width=60).pack(fill="x", pady=2)
        
        ttk.Label(scene_frame, text="Negative Prompt (what to avoid):").pack(anchor="w", pady=(10,0))
        self.negative_prompt = tk.StringVar(value="")
        ttk.Entry(scene_frame, textvariable=self.negative_prompt, width=60).pack(fill="x", pady=2)
        
        # Advanced Settings
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Settings", padding=10)
        advanced_frame.pack(fill="x", pady=5)
        
        # Create notebook for organized settings
        notebook = ttk.Notebook(advanced_frame)
        notebook.pack(fill="both", expand=True)
        
        # Basic Settings Tab
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Basic Settings")
        
        # Create grid for basic settings
        basic_grid = ttk.Frame(basic_tab)
        basic_grid.pack(fill="x", padx=10, pady=10)
        
        # Row 1: Frames, Scenes, Keyframes
        ttk.Label(basic_grid, text="Frames:").grid(row=0, column=0, sticky="w", padx=(0,5))
        self.frames = tk.StringVar(value="10")
        ttk.Entry(basic_grid, textvariable=self.frames, width=8).grid(row=0, column=1, sticky="w", padx=(0,15))
        
        ttk.Label(basic_grid, text="Scenes:").grid(row=0, column=2, sticky="w", padx=(0,5))
        self.num_scenes = tk.StringVar(value="1")
        ttk.Entry(basic_grid, textvariable=self.num_scenes, width=8).grid(row=0, column=3, sticky="w", padx=(0,15))
        
        ttk.Label(basic_grid, text="Keyframes:").grid(row=0, column=4, sticky="w", padx=(0,5))
        self.num_keyframes = tk.StringVar(value="2")
        ttk.Entry(basic_grid, textvariable=self.num_keyframes, width=8).grid(row=0, column=5, sticky="w")
        
        # Row 2: Resolution settings
        ttk.Label(basic_grid, text="Generation Resolution:").grid(row=1, column=0, sticky="w", padx=(0,5), pady=(10,0))
        self.gen_resolution = tk.StringVar(value="512")
        resolution_combo = ttk.Combobox(basic_grid, textvariable=self.gen_resolution, width=10,
                                       values=["256", "512", "768", "1024"])
        resolution_combo.grid(row=1, column=1, sticky="w", padx=(0,15), pady=(10,0))
        
        ttk.Label(basic_grid, text="Interpolation Resolution:").grid(row=1, column=2, sticky="w", padx=(0,5), pady=(10,0))
        self.interp_resolution = tk.StringVar(value="512")
        interp_combo = ttk.Combobox(basic_grid, textvariable=self.interp_resolution, width=10,
                                   values=["256", "512", "768", "1024"])
        interp_combo.grid(row=1, column=3, sticky="w", padx=(0,15), pady=(10,0))
        
        ttk.Label(basic_grid, text="FPS:").grid(row=1, column=4, sticky="w", padx=(0,5), pady=(10,0))
        self.save_fps = tk.StringVar(value="10")
        ttk.Entry(basic_grid, textvariable=self.save_fps, width=8).grid(row=1, column=5, sticky="w", pady=(10,0))
        
        # Row 3: Aspect Ratio settings
        ttk.Label(basic_grid, text="Aspect Ratio:").grid(row=2, column=0, sticky="w", padx=(0,5), pady=(10,0))
        self.aspect_ratio = tk.StringVar(value="1:1 (Square)")
        aspect_combo = ttk.Combobox(basic_grid, textvariable=self.aspect_ratio, width=15,
                                   values=["1:1 (Square)", "16:9 (Landscape)", "9:16 (Portrait)", "4:3 (Standard)", "3:4 (Portrait)", "Custom"])
        aspect_combo.grid(row=2, column=1, columnspan=2, sticky="w", padx=(0,15), pady=(10,0))
        
        ttk.Label(basic_grid, text="Base Size:").grid(row=2, column=3, sticky="w", padx=(0,5), pady=(10,0))
        self.base_size = tk.StringVar(value="512")
        size_combo = ttk.Combobox(basic_grid, textvariable=self.base_size, width=10,
                                 values=["256", "384", "512", "640", "768"])
        size_combo.grid(row=2, column=4, sticky="w", padx=(0,15), pady=(10,0))
        
        # Custom Width and Height Controls
        ttk.Label(basic_grid, text="Custom Width:").grid(row=3, column=0, sticky="w", padx=(0,5), pady=(10,0))
        self.custom_width = tk.StringVar(value="512")
        width_entry = ttk.Entry(basic_grid, textvariable=self.custom_width, width=12)
        width_entry.grid(row=3, column=1, sticky="w", padx=(0,15), pady=(10,0))
        
        ttk.Label(basic_grid, text="Custom Height:").grid(row=3, column=2, sticky="w", padx=(0,5), pady=(10,0))
        self.custom_height = tk.StringVar(value="512")
        height_entry = ttk.Entry(basic_grid, textvariable=self.custom_height, width=12)
        height_entry.grid(row=3, column=3, sticky="w", padx=(0,15), pady=(10,0))
        
        # Button to apply custom dimensions
        apply_custom_btn = ttk.Button(basic_grid, text="Apply Custom", command=self.apply_custom_dimensions)
        apply_custom_btn.grid(row=3, column=4, sticky="w", padx=(0,15), pady=(10,0))
        
        # Bind aspect ratio changes to update custom dimensions
        aspect_combo.bind('<<ComboboxSelected>>', self.on_aspect_ratio_change)
        
        # Checkboxes for boolean options
        checkbox_frame = ttk.Frame(basic_tab)
        checkbox_frame.pack(fill="x", padx=10, pady=10)
        
        self.use_gpt = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkbox_frame, text="Use GPT for scene enhancement", variable=self.use_gpt).pack(anchor="w", pady=2)
        
        self.finetune_decoder = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkbox_frame, text="Fine-tune decoder", variable=self.finetune_decoder).pack(anchor="w", pady=2)
        
        self.finetune_depth = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkbox_frame, text="Fine-tune depth model", variable=self.finetune_depth).pack(anchor="w", pady=2)
        
        self.enable_regenerate = tk.BooleanVar(value=True)
        ttk.Checkbutton(checkbox_frame, text="Enable regeneration on quality issues", variable=self.enable_regenerate).pack(anchor="w", pady=2)
        
        # Keyframes Tab
        keyframe_tab = ttk.Frame(notebook)
        notebook.add(keyframe_tab, text="Keyframes")
        
        keyframe_scroll_frame = ttk.Frame(keyframe_tab)
        keyframe_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(keyframe_scroll_frame, text="Configure each keyframe with its own image and description:").pack(anchor="w", pady=(0,10))
        
        self.keyframes = []  # List of dictionaries with 'image_path' and 'description'
        self.keyframe_frame = ttk.Frame(keyframe_scroll_frame)
        self.keyframe_frame.pack(fill="both", expand=True)
        
        # Add button to add more keyframes
        add_keyframe_btn = ttk.Button(keyframe_scroll_frame, text="+ Add Keyframe",
                                     command=self.add_keyframe)
        add_keyframe_btn.pack(pady=5)
        
        # Initialize with 2 keyframes
        for i in range(2):
            self.add_keyframe()
        
        # Camera Settings Tab
        camera_tab = ttk.Frame(notebook)
        notebook.add(camera_tab, text="Camera Settings")
        
        camera_scroll_frame = ttk.Frame(camera_tab)
        camera_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Camera controls grid
        camera_grid = ttk.Frame(camera_scroll_frame)
        camera_grid.pack(fill="x", pady=10)
        
        # Row 1: Rotation settings
        ttk.Label(camera_grid, text="Rotation Range:").grid(row=0, column=0, sticky="w", padx=(0,5))
        self.rotation_range = tk.StringVar(value="0.45")
        ttk.Entry(camera_grid, textvariable=self.rotation_range, width=10).grid(row=0, column=1, sticky="w", padx=(0,15))
        
        ttk.Label(camera_grid, text="Camera Speed Multiplier:").grid(row=0, column=2, sticky="w", padx=(0,5))
        self.camera_speed_multiplier = tk.StringVar(value="0.2")
        ttk.Entry(camera_grid, textvariable=self.camera_speed_multiplier, width=10).grid(row=0, column=3, sticky="w", padx=(0,15))
        
        # Row 2: Rotation path
        ttk.Label(camera_grid, text="Rotation Path:").grid(row=1, column=0, sticky="w", padx=(0,5), pady=(10,0))
        self.rotation_path = tk.StringVar(value="0, 0, 0, 1, 1, 0, 0, 0")
        rotation_entry = ttk.Entry(camera_grid, textvariable=self.rotation_path, width=40)
        rotation_entry.grid(row=1, column=1, columnspan=3, sticky="w", padx=(0,15), pady=(10,0))
        
        # Help text for rotation path
        help_text = ttk.Label(camera_scroll_frame,
                             text="Rotation Path: Comma-separated values (0=forward, 1=rotation). Length should match scenes × keyframes.",
                             font=("Arial", 8), foreground="gray")
        help_text.pack(anchor="w", pady=(5,0))
        
        # Preset buttons
        preset_frame = ttk.LabelFrame(camera_scroll_frame, text="Camera Presets", padding=10)
        preset_frame.pack(fill="x", pady=10)
        
        preset_buttons = ttk.Frame(preset_frame)
        preset_buttons.pack(fill="x")
        
        ttk.Button(preset_buttons, text="Smooth Forward",
                  command=lambda: self.set_camera_preset("forward")).pack(side="left", padx=(0,5))
        ttk.Button(preset_buttons, text="Cinematic Pan",
                  command=lambda: self.set_camera_preset("pan")).pack(side="left", padx=(0,5))
        ttk.Button(preset_buttons, text="Dynamic Movement",
                  command=lambda: self.set_camera_preset("dynamic")).pack(side="left", padx=(0,5))
        ttk.Button(preset_buttons, text="Static Shots",
                  command=lambda: self.set_camera_preset("static")).pack(side="left")
        
        # Config Management
        config_frame = ttk.LabelFrame(main_frame, text="Configuration Management", padding=10)
        config_frame.pack(fill="x", pady=5)
        
        config_buttons = ttk.Frame(config_frame)
        config_buttons.pack(fill="x")
        
        ttk.Button(config_buttons, text="Save Config", command=self.save_config).pack(side="left", padx=(0,5))
        ttk.Button(config_buttons, text="Load Config", command=self.load_config).pack(side="left", padx=(0,5))
        ttk.Button(config_buttons, text="Reset to Defaults", command=self.reset_config).pack(side="left")
        
        # Generate button
        generate_frame = ttk.Frame(main_frame)
        generate_frame.pack(fill="x", pady=20)
        
        self.generate_btn = ttk.Button(generate_frame, text="🚀 Generate 3D Scene", 
                                     command=self.start_generation)
        self.generate_btn.pack(side="left", padx=(0,10))
        
        self.stop_btn = ttk.Button(generate_frame, text="⏹ Stop", 
                                 command=self.stop_generation, state="disabled")
        self.stop_btn.pack(side="left")
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready to generate!")
        ttk.Label(generate_frame, textvariable=self.progress_var).pack(side="left", padx=(20,0))
        
        # Output
        output_frame = ttk.LabelFrame(main_frame, text="Generation Output", padding=10)
        output_frame.pack(fill="both", expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=12)
        self.output_text.pack(fill="both", expand=True)
        
    def check_gpu_status(self):
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                self.gpu_status.set(f"✓ GPU Ready: {gpu_name}")
            else:
                self.gpu_status.set("⚠ No GPU - Will be very slow!")
        except:
            self.gpu_status.set("✗ GPU Check Failed")
            
    def set_camera_preset(self, preset_type):
        """Set camera presets for different movement styles"""
        if preset_type == "forward":
            self.rotation_path.set("0, 0, 0, 0, 0, 0, 0, 0")
            self.rotation_range.set("0.0")
            self.camera_speed_multiplier.set("0.5")
        elif preset_type == "pan":
            self.rotation_path.set("0, 1, 1, 1, 1, 0, 0, 0")
            self.rotation_range.set("0.3")
            self.camera_speed_multiplier.set("0.2")
        elif preset_type == "dynamic":
            self.rotation_path.set("0, 1, 0, 1, 0, 1, 0, 1")
            self.rotation_range.set("0.6")
            self.camera_speed_multiplier.set("0.4")
        elif preset_type == "static":
            self.rotation_path.set("0, 0, 0, 0, 0, 0, 0, 0")
            self.rotation_range.set("0.0")
            self.camera_speed_multiplier.set("0.0")

    def get_dimensions_from_aspect_ratio(self):
        """Calculate width and height based on aspect ratio and base size"""
        base = int(self.base_size.get())
        ratio = self.aspect_ratio.get()
        
        if "1:1" in ratio:
            return base, base
        elif "16:9" in ratio:
            if "Portrait" in ratio:  # 9:16
                return int(base * 9/16), base
            else:  # 16:9
                return base, int(base * 9/16)
        elif "4:3" in ratio:
            if "Portrait" in ratio:  # 3:4
                return int(base * 3/4), base
            else:  # 4:3
                return base, int(base * 3/4)
        elif "Custom" in ratio:
            # Use custom width and height values
            try:
                width = int(self.custom_width.get())
                height = int(self.custom_height.get())
                return width, height
            except ValueError:
                return base, base  # Fallback to square if invalid custom values
        else:
            return base, base  # Default to square

    def apply_custom_dimensions(self):
        """Apply custom width and height dimensions"""
        try:
            width = int(self.custom_width.get())
            height = int(self.custom_height.get())
            
            # Validate dimensions (must be positive and reasonable)
            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Width and height must be positive numbers")
                return
            
            if width > 2048 or height > 2048:
                messagebox.showwarning("Warning", "Large dimensions may cause memory issues")
            
            # Set aspect ratio to Custom
            self.aspect_ratio.set("Custom")
            
            # Update the display to show current custom dimensions
            messagebox.showinfo("Success", f"Custom dimensions applied: {width}x{height}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer values for width and height")

    def on_aspect_ratio_change(self, event=None):
        """Handle aspect ratio changes and update custom dimensions accordingly"""
        ratio = self.aspect_ratio.get()
        
        if "Custom" not in ratio:
            # For preset ratios, update custom dimensions to match
            width, height = self.get_dimensions_from_aspect_ratio()
            self.custom_width.set(str(width))
            self.custom_height.set(str(height))

    def add_keyframe(self):
        """Add a new keyframe with image and description"""
        keyframe_num = len(self.keyframes) + 1
        
        # Main frame for this keyframe
        main_frame = ttk.LabelFrame(self.keyframe_frame, text=f"Keyframe {keyframe_num}", padding=10)
        main_frame.pack(fill="x", pady=5)
        
        # Image selection
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill="x", pady=2)
        
        ttk.Label(image_frame, text="Image:").pack(side="left", padx=(0,5))
        
        image_var = tk.StringVar()
        image_entry = ttk.Entry(image_frame, textvariable=image_var, width=40)
        image_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        
        browse_btn = ttk.Button(image_frame, text="Browse",
                               command=lambda: self.browse_keyframe_image(image_var))
        browse_btn.pack(side="left", padx=(0,5))
        
        # Remove button
        remove_btn = ttk.Button(image_frame, text="Remove",
                               command=lambda: self.remove_keyframe(main_frame, keyframe_data))
        remove_btn.pack(side="right")
        
        # Description
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="x", pady=(5,0))
        
        ttk.Label(desc_frame, text="Description:").pack(anchor="w")
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(desc_frame, textvariable=desc_var, width=80)
        desc_entry.pack(fill="x", pady=2)
        
        # Store keyframe data
        keyframe_data = {
            'frame': main_frame,
            'image_path': image_var,
            'description': desc_var
        }
        
        self.keyframes.append(keyframe_data)
        self.update_keyframe_labels()
    
    def remove_keyframe(self, frame, keyframe_data):
        """Remove a keyframe"""
        if len(self.keyframes) > 1:  # Keep at least one
            frame.destroy()
            self.keyframes.remove(keyframe_data)
            self.update_keyframe_labels()
    
    def update_keyframe_labels(self):
        """Update keyframe labels after removal"""
        for i, keyframe in enumerate(self.keyframes):
            keyframe['frame'].config(text=f"Keyframe {i+1}")
    
    def browse_keyframe_image(self, image_var):
        """Browse for keyframe image"""
        filename = filedialog.askopenfilename(
            title="Select Keyframe Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
        )
        if filename:
            image_var.set(filename)

    def browse_image(self):
        filename = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
        )
        if filename:
            self.image_path.set(filename)
    
    def save_config(self):
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            config = self.get_current_config()
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            messagebox.showinfo("Success", f"Configuration saved to {filename}")
    
    def load_config(self):
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                self.load_config_values(config)
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {e}")
    
    def reset_config(self):
        # Reset to default values
        self.content_prompt.set("Alpine village, street, chalet, church")
        self.style_prompt.set("DSLR 35mm landscape")
        self.background_prompt.set("A small village with a church and a clock tower surrounded by mountains")
        self.negative_prompt.set("")
        self.frames.set("10")
        self.num_scenes.set("1")
        self.num_keyframes.set("2")
        self.gen_resolution.set("512")
        self.interp_resolution.set("512")
        self.save_fps.set("10")
        self.aspect_ratio.set("1:1 (Square)")
        self.base_size.set("512")
        self.custom_width.set("512")
        self.custom_height.set("512")
        self.rotation_range.set("0.45")
        self.rotation_path.set("0, 0, 0, 1, 1, 0, 0, 0")
        self.camera_speed_multiplier.set("0.2")
        self.use_gpt.set(True)
        self.finetune_decoder.set(True)
        self.finetune_depth.set(True)
        self.enable_regenerate.set(True)
        self.image_path.set("")
        
        # Clear keyframes
        for keyframe in self.keyframes:
            keyframe['image_path'].set("")
            keyframe['description'].set("")
    
    def get_current_config(self):
        # Always use 512x512 for now
        width, height = 512, 512
        
        # Parse rotation path from string to list
        try:
            rotation_path = [int(x.strip()) for x in self.rotation_path.get().split(',')]
        except:
            rotation_path = [0, 0, 0, 1, 1, 0, 0, 0]  # Default fallback
        
        # Ensure rotation path has enough values for all scenes and keyframes
        num_scenes = int(self.num_scenes.get())
        num_keyframes = int(self.num_keyframes.get())
        required_length = num_scenes * num_keyframes
        
        # If rotation path is too short, extend it by repeating the pattern
        if len(rotation_path) < required_length:
            # Repeat the pattern to reach required length
            while len(rotation_path) < required_length:
                rotation_path.extend(rotation_path[:min(8, required_length - len(rotation_path))])
        
        return {
            'runs_dir': 'outputs/wonderjourney',
            'example_name': 'ui_generated',
            'seed': -1,
            'frames': int(self.frames.get()),
            'finetune_decoder_gen': self.finetune_decoder.get(),
            'finetune_decoder_interp': True,  # Always True for higher quality as requested
            'finetune_depth_model': self.finetune_depth.get(),
            'num_scenes': int(self.num_scenes.get()),
            'num_keyframes': int(self.num_keyframes.get()),
            'use_gpt': self.use_gpt.get(),
            'kf2_upsample_coef': 4,
            'skip_interp': False,
            'skip_gen': False,
            'enable_regenerate': self.enable_regenerate.get(),
            'debug': False,
            'inpainting_resolution_gen': int(self.gen_resolution.get()),
            'inpainting_resolution_interp': int(self.interp_resolution.get()),
            'rotation_range': float(self.rotation_range.get()),
            'rotation_path': rotation_path,
            'camera_speed_multiplier_rotation': float(self.camera_speed_multiplier.get()),
            'save_fps': int(self.save_fps.get()),
            'image_width': width,
            'image_height': height
        }
    
    def load_config_values(self, config):
        # Load values from config into UI
        if 'frames' in config:
            self.frames.set(str(config['frames']))
        if 'num_scenes' in config:
            self.num_scenes.set(str(config['num_scenes']))
        if 'num_keyframes' in config:
            self.num_keyframes.set(str(config['num_keyframes']))
        if 'use_gpt' in config:
            self.use_gpt.set(config['use_gpt'])
        if 'finetune_decoder_gen' in config:
            self.finetune_decoder.set(config['finetune_decoder_gen'])
        if 'finetune_depth_model' in config:
            self.finetune_depth.set(config['finetune_depth_model'])

    def start_generation(self):
        if not self.openai_api_key.get():
            messagebox.showerror("Error", "Please enter your OpenAI API key")
            return
        
        if not self.image_path.get():
            messagebox.showerror("Error", "Please select an input image")
            return
            
        os.environ['OPENAI_API_KEY'] = self.openai_api_key.get()
        self.save_settings()
        
        # Create config with current UI values
        config = self.get_current_config()
        
        # Add our UI-generated example to the main examples.yaml temporarily
        examples_path = "examples/examples.yaml"
        
        # Read existing examples
        try:
            with open(examples_path, 'r', encoding='utf-8') as f:
                existing_examples = yaml.safe_load(f) or []
        except:
            existing_examples = []
        
        # Create our UI example
        ui_example = {
            'name': 'ui_generated',
            'image_filepath': self.image_path.get(),
            'style_prompt': self.style_prompt.get(),
            'content_prompt': self.content_prompt.get(),
            'negative_prompt': self.negative_prompt.get(),
            'background': self.background_prompt.get()
        }
        
        # Add keyframes if they exist
        keyframes_data = []
        for i, keyframe in enumerate(self.keyframes):
            image_path = keyframe['image_path'].get().strip()
            description = keyframe['description'].get().strip()
            if image_path and description:
                keyframes_data.append({
                    'image_filepath': image_path,
                    'description': description
                })
        
        if keyframes_data:
            ui_example['keyframes'] = keyframes_data
        
        # Remove any existing ui_generated entry and add our new one
        existing_examples = [ex for ex in existing_examples if ex.get('name') != 'ui_generated']
        existing_examples.append(ui_example)
        
        # Save updated examples
        with open(examples_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_examples, f, allow_unicode=True)
        
        with open("temp_config.yaml", 'w') as f:
            yaml.dump(config, f)
        
        # Use virtual environment Python if available
        venv_python = os.path.join("venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_cmd = venv_python
        else:
            python_cmd = "python"
        
        cmd = [python_cmd, "run.py", "--example_config", "temp_config.yaml"]
        
        self.generate_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_var.set("Starting generation...")
        self.output_text.delete("1.0", tk.END)
        
        thread = threading.Thread(target=self.run_generation, args=(cmd,))
        thread.daemon = True
        thread.start()
        
    def run_generation(self, cmd):
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                          stderr=subprocess.STDOUT, text=True)
            
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.root.after(0, self.update_output, line.strip())
                    
            self.process.wait()
            
            if self.process.returncode == 0:
                self.root.after(0, self.generation_complete)
            else:
                self.root.after(0, self.generation_error)
                
        except Exception as e:
            self.root.after(0, self.update_output, f"Error: {e}")
            
    def update_output(self, text):
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        
        if "100%" in text:
            self.progress_var.set("Complete!")
        elif "%" in text:
            self.progress_var.set(f"Processing... {text}")
            
    def generation_complete(self):
        self.generate_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_var.set("Success!")
        self.cleanup_temp_files()
        messagebox.showinfo("Success", "3D scene generated! Check outputs folder.")
        
    def generation_error(self):
        self.generate_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_var.set("Failed")
        self.cleanup_temp_files()
        
    def cleanup_temp_files(self):
        """Clean up temporary configuration files and restore examples.yaml"""
        # Remove temp config file
        if os.path.exists("temp_config.yaml"):
            try:
                os.remove("temp_config.yaml")
            except:
                pass
        
        # Remove ui_generated entry from examples.yaml
        examples_path = "examples/examples.yaml"
        try:
            with open(examples_path, 'r', encoding='utf-8') as f:
                examples = yaml.safe_load(f) or []
            
            # Remove ui_generated entry
            examples = [ex for ex in examples if ex.get('name') != 'ui_generated']
            
            # Save cleaned examples
            with open(examples_path, 'w', encoding='utf-8') as f:
                yaml.dump(examples, f, allow_unicode=True)
        except:
            pass  # Ignore cleanup errors
        
    def stop_generation(self):
        if self.process:
            self.process.terminate()
            self.generate_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            
    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", 'r') as f:
                    settings = json.load(f)
                    self.openai_api_key.set(settings.get('api_key', ''))
        except:
            pass
            
    def save_settings(self):
        try:
            with open("settings.json", 'w') as f:
                json.dump({'api_key': self.openai_api_key.get()}, f)
        except:
            pass

def main():
    if not os.path.exists("run.py"):
        messagebox.showerror("Error", "Run this from WonderJourney directory")
        return
        
    root = tk.Tk()
    app = WonderJourneyUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()