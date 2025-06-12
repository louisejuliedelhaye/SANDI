# -*- coding: utf-8 -*-
"""
File: homepage
Version: SANDI v1.0.0-beta
Created on Tue Aug 20 16:47:08 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: layout of the homepage
"""

###############################################################################
# Import packages
###############################################################################

import tkinter as tk
from tkinter import ttk
import os
import sys
from PIL import Image, ImageTk

###############################################################################
# Access everything in the directory
###############################################################################

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'functions'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'images'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'attributes'))

###############################################################################
# Creation of the page layout
###############################################################################

class Homepage():
    
    def __init__(self, root, on_single_image_processing, on_single_stone_processing, on_batch_processing):
        
        self.root = root
        self.on_single_image_processing = on_single_image_processing
        self.on_batch_processing = on_batch_processing
        self.on_single_stone_processing = on_single_stone_processing

        self.homepage_frame = tk.Frame(self.root, bg="#2c3e50")
        self.homepage_frame.pack(fill=tk.BOTH, expand=True)
        
        self.bg_photo = None 
        self.set_background_image("images/homepage_background.png")
        self.homepage_frame.bind("<Configure>", self.on_resize)

        self.create_widgets()
    
    def on_resize(self, event):
        """
        Adapt background image to window size.
        """
        self.set_background_image("images/homepage_background.png")
    
    def set_background_image(self, image_path):
        """
        Displays the background image.
        """
        if getattr(sys, 'frozen', False):  
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")   

        full_image_path = os.path.join(base_path, image_path)

        if self.homepage_frame.winfo_width() > 1 and self.homepage_frame.winfo_height() > 1:
            self.original_bg_image = Image.open(full_image_path)
            resized_image = self.original_bg_image.resize(
                (self.homepage_frame.winfo_width(), self.homepage_frame.winfo_height()), 
                Image.LANCZOS
            )
    
            self.bg_photo = ImageTk.PhotoImage(resized_image)
    
            if hasattr(self, 'background_label'):
                self.background_label.configure(image=self.bg_photo)
                self.background_label.image = self.bg_photo
            else:
                self.background_label = tk.Label(self.homepage_frame, image=self.bg_photo)
                self.background_label.place(relwidth=1, relheight=1)
                self.background_label.lower()
                
    def style_buttons(self):
        """
        Defines the style of the buttons.
        """
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton',
                        background='#2c3e50',  
                        foreground='white',
                        font=('Segoe UI', 14),
                        padding=10)
        style.map('TButton',
                  background=[('active', '#45A049'), ('pressed', '#388E3C')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
    
    def create_widgets(self):

        self.homepage_frame.grid_rowconfigure(0, weight=0)
        self.homepage_frame.grid_rowconfigure(1, weight=0)
        self.homepage_frame.grid_rowconfigure(2, weight=0)
        self.homepage_frame.grid_rowconfigure(3, weight=0)  
        self.homepage_frame.grid_columnconfigure(0, weight=1)  
        self.homepage_frame.grid_columnconfigure(1, weight=0)  

        # Title
        title = tk.Label(self.homepage_frame, text="SANDI",
                               bg="#2c3e50", fg="#FFBC42", font=("Segoe UI", 94, "bold"), wraplength=500)
        title.grid(row=0, column=0, padx=95, pady=(60, 0), sticky="nw")
    
        # Subtitle
        subtitle = tk.Label(self.homepage_frame, text="Sediment ANalysis & Delineation through Images",
                                bg="#2c3e50", fg="#FFBC42", font=("Segoe UI", 20), wraplength=455)
        subtitle.grid(row=1, column=0, padx=95, pady=(0, 10), sticky="nw")
    
        # Frame with buttons
        button_frame = tk.Frame(self.homepage_frame, bg="#2c3e50")  
        button_frame.grid(row=3, column=0, padx=80, pady=0, sticky="nw")  
    
        # Space
        space = tk.Label(button_frame, text=" ",
                                         bg="#2c3e50", fg="white", font=("Segoe UI", 18, "bold"))
        space.grid(row=0, column=0, columnspan=2, pady=(10, 10), sticky="nw")  
        
        # Suspended particles
        suspended_particles_text = tk.Label(button_frame, text="Suspended particles:",
                                     bg="#2c3e50", fg="lightgrey", font=("Segoe UI", 12, "bold"), wraplength=440)
        suspended_particles_text.grid(row=1, column=0, padx=5, pady=(0, 0), sticky="sw")
    
        # Single image processing button
        self.single_image_processing_button = ttk.Button(button_frame, text="Single image processing",
                                                            command=self.on_single_image_processing, width=40)
        self.single_image_processing_button.grid(row=2, pady=(0, 5), sticky="n")
    
        # Batch processing button
        self.batch_processing_button = ttk.Button(button_frame, text="Batch processing",
                                                      command=self.on_batch_processing, width=40)
        self.batch_processing_button.grid(row=3, pady=(5, 5), sticky="n")
        
        # Gravels
        gravels_text = tk.Label(button_frame, text="Gravels:",
                                     bg="#2c3e50", fg="lightgrey", font=("Segoe UI", 12, "bold"), wraplength=440)
        gravels_text.grid(row=4, column=0, padx=5, pady=(20, 0), sticky="sw")
        
        # Stone processing button
        self.stone_processing_button = ttk.Button(button_frame, text="Gravels analysis",
                                                      command=self.on_single_stone_processing, width=40)
        self.stone_processing_button.grid(row=5, pady=(0, 5), sticky="n")
        
        # Spaces
        space = tk.Label(self.homepage_frame, text=" ",
                                     bg="#2c3e50", fg="white", font=("Segoe UI", 20), wraplength=440)
        space.grid(row=5, column=0, padx=80, pady=(0, 20), sticky="sw")
        
        space = tk.Label(self.homepage_frame, text=" ",
                                     bg="#2c3e50", fg="white", font=("Segoe UI", 20), wraplength=440)
        space.grid(row=5, column=0, padx=80, pady=(0, 20), sticky="sw")
    
        # Copyrights
        copyrights = tk.Label(self.homepage_frame, text="SANDI v1.0.0-alpha 2025\nRoyal Belgian Institute of Natural Sciences | Louise Delhaye\nArtwork by Sophie Delhaye",
                                     bg="#2c3e50", fg="#0f1620", font=("Segoe UI", 8), wraplength=440)
        copyrights.grid(row=6, column=0, padx=140, pady=(20, 10), sticky="sw")
    
        self.style_buttons()

    def destroy(self):
        """
        Destroys the homepage.
        """
        self.homepage_frame.destroy()
