# -*- coding: utf-8 -*-
"""
File: single gravel image processing page
Version: SANDI v1.0.0-beta
Created on Tue Aug 20 16:49:45 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: layout of the single gravel image processing page
"""

###############################################################################
# Import packages
###############################################################################

import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors
import cv2
import numpy as np
import matplotlib.ticker as ticker
import time
import math
import threading
import os
import sys

###############################################################################
# Import local packages
###############################################################################

from sandi.attributes.PCAM import PCam3_characteristics
from sandi.attributes.IMG import IMG
from sandi.functions.ImportImages import open_stones_file, reset_all
from sandi.functions.ImageEnhancement import (rgb_to_grey, denoise, histogram_stretching,
                                              image_reconstruction, lighten_shadows_with_gamma)
from sandi.functions.ParticleExtraction import extract_stones, extract_stones_on_green, filter_stones_on_size
from sandi.functions.VignetteGeneration import add_scale_bar, generate_vignette
from sandi.functions.StatisticsComputation import stones_sample_statistics, compute_stones_statistics
from sandi.functions.ExportToCSV import save_sample_csv, save_gravels_csv

###############################################################################
# Creation of the page layout
###############################################################################

class SingleStoneProcessing:
    
    ###########################################################################
    # Initialize layout and variables
    ###########################################################################
    
    def __init__(self, root, on_go_home):
        self.root = root
        self.on_go_home = on_go_home
        
        reset_all()
        self.images_on_canvas = []
        self.image_scale = 1.0
        self.setup_main_interface()
        self.initial_image_x = 0
        self.initial_image_y = 0
        self.removed_particles = []
        
        self.denoising_controls_visible = False
        self.filter_strength_label.grid_remove()
        self.filter_strength_value_label.grid_remove()
        self.filter_strength_slider.grid_remove()
        self.denoise_button.grid_remove()
        
        self.histogram_controls_visible = False
        self.min_value_label.grid_remove()
        self.max_value_label.grid_remove()
        self.max_value_entry.grid_remove()
        self.min_value_entry.grid_remove()
        self.histogram_stretching_button.grid_remove()
        
        self.reconstruction_controls_visible = False
        self.SubDiff_label.grid_remove()
        self.SubDiff_value.grid_remove()
        self.SubDiff_slider.grid_remove()
        self.reconstruction_button.grid_remove()
        
        self.gamma_label.grid_remove()
        self.gamma_value.grid_remove()
        self.gamma_slider.grid_remove()
        self.gamma_button.grid_remove()
        self.shadow_controls_visible = False
        
        self.initialize_expanded_window()
        self.plot_histogram(which='initialise')

        self.tooltip_label = tk.Label(self.image_canvas, text="", background="yellow", relief="solid", padx=5, pady=5)
        self.tooltip_label.place_forget() 
        self.dragging = False
        self.last_tooltip_update = 0
        self.tooltip_update_delay = 0.05 
        
        self.start_point = None
        self.end_point = None 
        self.distance_lines = []
        self.start_circles = []
        self.end_circles = []  
        self.distance_label = None 
        
        self.image_canvas.modify_mode = False
        self.temp_contours = []
        
    ###########################################################################
    # Create main layout structure
    ###########################################################################
        
    def setup_main_interface(self):
        self.pcam_characteristics = PCam3_characteristics()
        
        self.root.grid_columnconfigure(0, minsize=277)
        self.root.grid_columnconfigure(1, minsize=900)
        self.root.grid_columnconfigure(2, minsize=277)
        
        self.button_color = "#d3d3d3"
        self.hover_color = "white"

        #######################################################################
        # Left frame
        #######################################################################
        
        self.left_frame = tk.Frame(self.root, bg="#2c3e50", padx=5, pady=5)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_propagate(False)

        #######################################################################
        ### Import file button
        #######################################################################
        
        self.file_button = tk.Button(self.left_frame, text="Select JPG image", command=self.open_file_button_clicked,
                                     bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                     borderwidth=1, relief="flat", width=80)
        self.file_button.grid(row=0, column=0, columnspan=2, pady=(6, 3), padx=(5,0), sticky="nw")
        
        self.file_button.bind("<Enter>", self.on_hover_buttons)
        self.file_button.bind("<Leave>", self.on_leave_buttons)

        #######################################################################
        ### Reset button
        #######################################################################
                
        self.reset_button = tk.Button(self.left_frame,
                                       text="Reset",
                                       command=self.reset_button_clicked,
                                       bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                       borderwidth=1, relief="flat", width=75)
        self.reset_button.grid(row=1, column=0, columnspan=2, sticky="nw", pady=(5, 10), padx=(6,0))
        
        self.reset_button.bind("<Enter>", self.on_hover_buttons)
        self.reset_button.bind("<Leave>", self.on_leave_buttons)

        #######################################################################
        ### Background processing frame
        #######################################################################
        
        self.background_canvas = tk.Canvas(self.left_frame, bg="#2c3e50", bd=0, highlightthickness=0)
        self.background_canvas.grid(row=4, column=0, padx=(5,0), pady=(0, 5), sticky="ns")

        self.background_processing_frame = tk.Frame(self.background_canvas, bg="#2c3e50", bd=0, relief="groove", highlightthickness=1, highlightbackground="white")
        self.background_processing_frame.grid(row=4, column=0, padx=(5,5), pady=(0, 5), sticky="ns")
        self.background_canvas.create_window((0, 0), window=self.background_processing_frame, anchor="nw", width=261)

        self.background_processing_frame.update_idletasks()  
        self.background_canvas.config(scrollregion=self.background_canvas.bbox("all"))

        self.left_frame.grid_rowconfigure(4, weight=3)
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        self.title_option_1 = tk.Label(self.background_processing_frame,
                                         text="Option 1:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12, "bold"))
        self.title_option_1.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 0), sticky="sw")
        
        self.subtitle_option_1 = tk.Label(self.background_processing_frame,
                                         text="extraction on white background",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 10, "bold"))
        self.subtitle_option_1.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nw")

        self.background_processing_frame_title = tk.Label(self.background_processing_frame,
                                         text="Image pre-processing:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12))
        self.background_processing_frame_title.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        self.background_processing_frame.bind("<Configure>", self.update_scroll_region)
        self.background_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        #######################################################################
        ### Adjust denoising section
        #######################################################################
        
        def update_filter_strength_label(value):
            self.filter_strength_value_label.config(text=str(int(float(value))))
    
        self.denoise_filter_strength = tk.DoubleVar(value=15)
        
            #######################################################################
            ##### drop-down button
            #######################################################################
        
        self.test_denoising_button = tk.Button(self.background_processing_frame,
                                               text="› Adjust denoising level",
                                               command=self.toggle_denoising_controls,
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=25)
        self.test_denoising_button.grid(row=3, column=0, columnspan=2, sticky="w", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Filter strength label
            #######################################################################
        
        self.filter_strength_label = tk.Label(self.background_processing_frame,
                                              text="Filter strength:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.filter_strength_label.grid(row=4, column=0, sticky="w", padx=(10,5), pady=(5, 0))
        
        self.filter_strength_value_label = tk.Label(self.background_processing_frame,
                                                    text=str(int(self.denoise_filter_strength.get())),
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.filter_strength_value_label.grid(row=4, column=0, sticky="w", padx=(220,0), pady=(5, 0))
        
            #######################################################################
            ##### Denoising slider
            #######################################################################
        
        style = ttk.Style()
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=24,
                        sliderrelief="flat",
                        troughrelief="flat",
                        sliderthickness=12,
                        relief="flat",
                        borderwidth=0)
        style.map("TScale",
                  background=[("active", "#388E3C")],
                  sliderrelief=[("active", "flat")])
        
        self.filter_strength_slider = ttk.Scale(self.background_processing_frame,
                                                from_=0, to=100,
                                                orient="horizontal",
                                                variable=self.denoise_filter_strength,
                                                style="TScale",
                                                command=update_filter_strength_label)
        self.filter_strength_slider.grid(row=5, column=0, columnspan=1, sticky="ew", padx=(10,10), pady=(0, 10))

            #######################################################################
            ##### Apply Denoising button
            #######################################################################
        
        style.configure('TButton',
                        background='#2c3e50',
                        foreground='white',
                        font=('Segoe UI', 10),
                        padding=4,
                        borderwidth=0.5,
                        relief='solid',
                        width=32)
        
        style.map('TButton',
                  background=[('active', '#388E3C')],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        
        self.denoise_button = ttk.Button(self.background_processing_frame,
                                 text="Apply denoising",
                                 command=self.apply_denoising,
                                 style='TButton')  
        self.denoise_button.grid(row=6, column=0, columnspan=1, sticky="nw", pady=(0, 15), padx=(10, 10))
        
        #######################################################################
        ### Adjust histogram stretching section
        #######################################################################
        
        def update_min_value_label(value):
            min_val = int(float(value))
            self.min_value_label.config(text=f"Min: {min_val}")

        def update_max_value_label(value):
            max_val = int(float(value))
            self.max_value_label.config(text=f"Max: {max_val}")
        
            #######################################################################
            ##### Drop-down button
            #######################################################################
            
        self.test_histogram_button = tk.Button(self.background_processing_frame,
                                               text="› Adjust histogram stretching",
                                               command=self.toggle_histogram_controls,
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=25)
        self.test_histogram_button.grid(row=7, column=0, columnspan=2, sticky="w", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Min/Max 
            #######################################################################
        
        self.min_value = tk.DoubleVar(value=0)
        self.max_value = tk.DoubleVar(value=255)
        
        self.min_value_label = tk.Label(self.background_processing_frame,
                                      text="Min:",
                                      bg="#2c3e50",
                                      fg="white",
                                      font=("Segoe UI", 11))
        self.min_value_label.grid(row=8, column=0, sticky="w", padx=(10, 5), pady=(6,0))
        
        self.min_value_entry = tk.Entry(self.background_processing_frame,
                                      textvariable=self.min_value,
                                      bg="#243342",
                                      fg="white",
                                      width=6,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.min_value_entry.grid(row=8, column=0, sticky="w", padx=(195, 0), pady=(5,0))
        
        self.min_value_entry.bind("<Enter>", lambda e: self.on_hover(self.min_value_entry))
        self.min_value_entry.bind("<Leave>", lambda e: self.on_leave(self.min_value_entry))

        self.max_value_label = tk.Label(self.background_processing_frame,
                                        text="Max:",
                                        bg="#2c3e50",
                                        fg="white",
                                        font=("Segoe UI", 11))
        self.max_value_label.grid(row=9, column=0, sticky="w", padx=(10, 5), pady=(0,6))
        
        self.max_value_entry = tk.Entry(self.background_processing_frame,
                                        textvariable=self.max_value,
                                      bg="#243342",
                                      fg="white",
                                      width=6,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.max_value_entry.grid(row=9, column=0, sticky="w", padx=(195, 0), pady=(0,5))
        
        self.max_value_entry.bind("<Enter>", lambda e: self.on_hover(self.max_value_entry))
        self.max_value_entry.bind("<Leave>", lambda e: self.on_leave(self.max_value_entry))
        
            #######################################################################
            ##### Apply histogram stretching button
            #######################################################################
            
        self.histogram_stretching_button = ttk.Button(self.background_processing_frame,
                                 text="Apply histogram stretching",
                                 command=self.apply_histogram_stretching,
                                 style='TButton')  # Apply the custom style
        self.histogram_stretching_button.grid(row=10, column=0, columnspan=1, sticky="nw", pady=(0, 15), padx=(10, 10))
        
        #######################################################################
        ### Adjust reconstruction section
        #######################################################################
    
        self.SubDiff = tk.DoubleVar(value=50)
        
            #######################################################################
            ##### drop-down button
            #######################################################################
        
        self.test_image_reconstuction_button = tk.Button(self.background_processing_frame,
                                               text="› Adjust image reconstruction",
                                               command=self.toggle_reconstruction_controls,
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=25)
        self.test_image_reconstuction_button.grid(row=11, column=0, columnspan=2, sticky="w", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Filter strength label
            #######################################################################
        
        self.SubDiff_label = tk.Label(self.background_processing_frame,
                                              text="Difference:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.SubDiff_label.grid(row=12, column=0, sticky="w", padx=(10,5), pady=(5, 0))
        
        self.SubDiff_value = tk.Label(self.background_processing_frame,
                                                    text=str(int(self.SubDiff.get())),
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.SubDiff_value.grid(row=12, column=0, sticky="e", padx=(190,15),  pady=(5, 0))
        
            #######################################################################
            ##### Reconstruction slider
            #######################################################################
        
        style = ttk.Style()
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=24,
                        sliderrelief="flat",
                        troughrelief="flat",
                        sliderthickness=12,
                        relief="flat",
                        borderwidth=0)
        style.map("TScale",
                  background=[("active", "#388E3C")],
                  sliderrelief=[("active", "flat")])
        
        self.SubDiff_slider = ttk.Scale(self.background_processing_frame,
                                                from_=0, to=255,
                                                orient="horizontal",
                                                variable=self.SubDiff,
                                                style="TScale",
                                                command=self.update_SubDiff)
        self.SubDiff_slider.grid(row=13, column=0, columnspan=1, sticky="ew", padx=(10,10), pady=(0, 10))

            #######################################################################
            ##### Apply reconstruction button
            #######################################################################
        
        self.reconstruction_button = ttk.Button(self.background_processing_frame,
                                 text="Apply image reconstruction",
                                 command=self.apply_image_reconstruction,
                                 style='TButton')  # Apply the custom style
        self.reconstruction_button.grid(row=14, column=0, columnspan=1, sticky="nw", pady=(0, 15), padx=(10, 10))
        
        #######################################################################
        ### Adjust gamma section
        #######################################################################
    
        self.gamma = tk.DoubleVar(value=0.90)
        
            #######################################################################
            ##### drop-down button
            #######################################################################
        
        self.adjust_gamma_button = tk.Button(self.background_processing_frame,
                                               text="› Adjust shadows",
                                               command=self.toggle_shadow_controls,
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=25)
        self.adjust_gamma_button.grid(row=15, column=0, columnspan=2, sticky="w", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Adjust gamma label
            #######################################################################
        
        self.gamma_label = tk.Label(self.background_processing_frame,
                                              text="Gamma value:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.gamma_label.grid(row=16, column=0, sticky="w", padx=(10,5), pady=(5, 0))
        
        gamma_value = self.gamma.get()
        formatted_gamma = "{:.2f}".format(gamma_value)
        
        self.gamma_value = tk.Label(self.background_processing_frame,
                                                    text=formatted_gamma,
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.gamma_value.grid(row=16, column=0, sticky="w", padx=(210,15), pady=(5, 0))
        
            #######################################################################
            ##### Gamma slider
            #######################################################################
        
        style = ttk.Style()
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=24,
                        sliderrelief="flat",
                        troughrelief="flat",
                        sliderthickness=12,
                        relief="flat",
                        borderwidth=0)
        style.map("TScale",
                  background=[("active", "#388E3C")],
                  sliderrelief=[("active", "flat")])
        
        self.gamma_slider = ttk.Scale(self.background_processing_frame,
                                                from_=0.1, to=3.0,
                                                orient="horizontal",
                                                variable=self.gamma,
                                                style="TScale",
                                                command=self.update_gamma)
        self.gamma_slider.grid(row=17, column=0, columnspan=1, sticky="ew", padx=(10,14), pady=(0, 10))

            #######################################################################
            ##### Apply gamma button
            #######################################################################
        
        self.gamma_button = ttk.Button(self.background_processing_frame,
                                 text="Apply shadow correction",
                                 command=self.apply_gamma_correction,
                                 style='TButton')
        self.gamma_button.grid(row=18, column=0, columnspan=1, sticky="nw", pady=(0, 15), padx=(10, 10))
        
        #######################################################################
        # Extract stones button #1
        #######################################################################
        
        style.configure('Extraction.TButton',
                        background='#2c3e50',
                        foreground='white',
                        font=('Segoe UI', 12),
                        padding=6,
                        relief='solid'
                        )
        
        style.map('Extraction.TButton',
                  background=[('active', '#FFBC42')],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        
        self.extract_particles_button_1 = ttk.Button(self.background_processing_frame,
                                 text="Extract stones",
                                 command=self.apply_extract_particles_on_white,
                                 style='Extraction.TButton',width=25) 
        self.extract_particles_button_1.grid(row=19, column=0, columnspan=1, sticky="w", pady=(5, 10), padx=(8,5))
        
        #######################################################################
        ##### Histogram figure
        #######################################################################
        
        self.figure = Figure(figsize=(0.2, 1.5), dpi=120)
        self.ax = self.figure.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.left_frame)
        self.canvas.get_tk_widget().grid(row=20, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 0))
        
        #######################################################################
        ##### Expand button
        #######################################################################
        
        self.expand_button = tk.Button(self.left_frame, text="🔍 Expand plot", command=self.show_expanded_window, bg="#3A506B", fg="white", font=("Segoe UI", 10),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w")
        self.expand_button.grid(row=21, column=0, columnspan=2, pady=10)
        
        #######################################################################
        # Middle frame
        #######################################################################
        
        self.middle_frame = tk.Frame(self.root, bg="#243342")
        self.middle_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.middle_frame.grid_rowconfigure(0, weight=0)
        self.middle_frame.grid_rowconfigure(1, weight=0)
        self.middle_frame.grid_rowconfigure(2, weight=2)
        
        #######################################################################
        ### Image canvas
        #######################################################################
        
        # Dropdown for selecting image type
        self.image_select = ttk.Combobox(self.middle_frame, values=["Original Image", "Denoised Image", "Stretched Image", "Reconstructed Image", "Shadow Corrected Image", "Binary Image", "Extracted Particles Image", "Extracted Particles Filtered on Intensity"], state="readonly")
        self.image_select.set("Select image")
        self.image_select.grid(row=0, column=0, padx=1, pady=(2,0), sticky="ew")
        self.image_select.bind("<<ComboboxSelected>>", self.update_image_display)
        
        # Image canvas
        self.image_canvas = tk.Canvas(self.middle_frame, bg="#243342", width=900, height=600)
        self.image_canvas.grid(row=1, column=0, padx=1, pady=(0,7), sticky="ew")

        # Console frame
        self.console_frame = tk.Frame(self.middle_frame, bg="#243342", bd=1, relief="flat")
        self.console_frame.grid(row=2, column=0, padx=0, pady=(0, 5), sticky="nsew")
        
        self.console_text = tk.Text(self.console_frame, bg="#243342", fg="white", wrap=tk.WORD, height=9)
        self.console_text.grid(row=0, column=0, sticky="nsew")
        self.console_text.config(state=tk.DISABLED)

        self.scrollbar = ttk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.console_text.config(yscrollcommand=self.scrollbar.set)

        self.console_text.tag_configure('info', foreground='white', font=("Segoe UI", 10))
        self.console_text.tag_configure('error', foreground='red', font=("Segoe UI", 10))
        self.console_text.tag_configure('success', foreground='lime', font=("Segoe UI", 10))
        self.console_text.tag_configure('new', foreground='#EEB902', font=("Segoe UI", 10))
        self.console_text.tag_configure('debug', foreground='orange', font=("Segoe UI", 10))
        
        self.style = ttk.Style()
        self.style.configure('Vertical.TScrollbar', 
                             gripcount=0,
                             background='white',
                             troughcolor='#243342',
                             buttoncolor='#243342',
                             borderwidth=0,
                             relief='flat')
        self.style.map('Vertical.TScrollbar', 
                       background=[('pressed', '#EEB902'), ('active', '#EEB902')],
                       relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(1, weight=0)
        self.console_frame.grid_rowconfigure(0, weight=1)
        
        self.console_frame.update_idletasks()
        self.console_frame.config(height=self.console_frame.winfo_reqheight())
        
        #######################################################################
        # Right frame
        #######################################################################
        
        self.right_frame = tk.Frame(self.root, bg="#2c3e50", padx=5, pady=0)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        
        #######################################################################
        ### Particles extraction frame option 2
        #######################################################################

        self.right_frame.grid_rowconfigure(0, weight=0) 
        self.right_frame.grid_rowconfigure(1, weight=0) 
        self.right_frame.grid_rowconfigure(2, weight=0)     

        
        self.option2_canvas = tk.Canvas(self.right_frame, bg="#2c3e50", bd=0, highlightthickness=0)
        self.option2_canvas.grid(row=0, column=0, padx=(0,0), pady=(10, 5), sticky="nw")

        self.option2_frame = tk.Frame(self.option2_canvas, bg="#2c3e50", bd=0, relief="groove", highlightthickness=1, highlightbackground="white")
        self.option2_frame.grid(row=0, column=0, padx=(5,5), pady=(5, 5), sticky="nw")
        self.option2_canvas.create_window((0, 0), window=self.option2_frame, anchor="nw", width=275)
        
        #######################################################################
        # Extract particles button #2
        #######################################################################
        
        self.title_option_2 = tk.Label(self.option2_frame,
                                         text="Option 2:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12, "bold"))
        self.title_option_2.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 0), sticky="sw")
        
        self.subtitle_option_2 = tk.Label(self.option2_frame,
                                         text="extraction on green background",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 10, "bold"))
        self.subtitle_option_2.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nw")
        
        style.configure('Extraction.TButton',
                        background='#2c3e50',
                        foreground='white',
                        font=('Segoe UI', 12),
                        padding=6,
                        relief='solid'
                        )

        style.map('Extraction.TButton',
                  background=[('active', '#FFBC42')],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        
        self.extract_particles_button_2 = ttk.Button(self.option2_frame,
                                 text="Extract stones",
                                 command=self.apply_extract_particles_on_green,
                                 style='Extraction.TButton',width=27)  
        self.extract_particles_button_2.grid(row=2, column=0, columnspan=1, sticky="w", pady=(5, 10), padx=(6,6))
               
        #######################################################################
        # Filtering on size
        #######################################################################
        
        self.filtering_and_export_frame = tk.Frame(self.right_frame, bg="#2c3e50")
        self.filtering_and_export_frame.grid(row=0, column=0, padx=5, pady=(140, 0), sticky="nw")
        
        self.filtering_title = tk.Label(self.filtering_and_export_frame,
                                         text="Stones filtration:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12, "bold"))
        self.filtering_title.grid(row=0, column=0, columnspan=2, padx=0, pady=(0, 0), sticky="w")
        
        self.MinSize = tk.DoubleVar(value=0.05)
        
        self.MinSize_label = tk.Label(self.filtering_and_export_frame,
                                       text="Minimum stone length (cm):",
                                       bg="#2c3e50",
                                       fg="white",
                                       font=("Segoe UI", 11),
                                       wraplength=200)
        self.MinSize_label.grid(row=1, column=0, sticky="w", padx=0, pady=(0, 0))
        
        self.MinSize_entry = tk.Entry(self.filtering_and_export_frame,
                                      textvariable=self.MinSize,
                                      bg="#243342",
                                      fg="white",
                                      width=6,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.MinSize_entry.grid(row=1, column=0, sticky="w", padx=(215, 15), pady=0)

        self.filter_size_button = ttk.Button(self.filtering_and_export_frame,
                                             text="Apply size filter",
                                             command=self.apply_size_filter,
                                             style='Extraction.TButton', width=28)
        self.filter_size_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5), padx=(0, 15))
        
        #######################################################################
        # Statistics computation 
        #######################################################################
        
        self.statistics_computation_title = tk.Label(self.filtering_and_export_frame,
                                                     text="Statistics computation:",
                                                     bg="#2c3e50",
                                                     fg="white",
                                                     wraplength=230,
                                                     justify="left",
                                                     font=("Segoe UI", 12, "bold"))
        self.statistics_computation_title.grid(row=3, column=0, columnspan=2, padx=0, pady=(15, 5), sticky="w")
        
        self.compute_statistics_button = ttk.Button(self.filtering_and_export_frame,
                                                     text="Compute stones statistics",
                                                     command=self.apply_stones_statistics_computation,
                                                     style='Extraction.TButton', width=28)
        self.compute_statistics_button.grid(row=4, column=0, columnspan=1, sticky="ew", pady=(0, 5), padx=(0, 15))
        
        #######################################################################
        # Save CSV & vignettes buttons
        #######################################################################
        
        self.save_csv_title = tk.Label(self.filtering_and_export_frame,
                                        text="Export outputs:",
                                        bg="#2c3e50",
                                        fg="white",
                                        wraplength=230,
                                        justify="left",
                                        font=("Segoe UI", 12, "bold"))
        self.save_csv_title.grid(row=5, column=0, columnspan=2, padx=0, pady=(15, 5), sticky="w")
        
        self.save_csv_button = ttk.Button(self.filtering_and_export_frame,
                                           text="Save statistics as csv",
                                           command=self.save_csv_button_clicked,
                                           style='Extraction.TButton', width=28)
        self.save_csv_button.grid(row=6, column=0, columnspan=1, sticky="ew", pady=(0, 15), padx=(0, 15))
        
        self.save_vignettes = ttk.Button(self.filtering_and_export_frame,
                                          text="Save gravel vignettes",
                                          command=self.save_vignettes_button_clicked,
                                          style='Extraction.TButton', width=28)
        self.save_vignettes.grid(row=7, column=0, columnspan=1, sticky="ew", pady=(0, 15), padx=(0, 15))
        
        #######################################################################
        ##### Canvas for gravel contours
        #######################################################################
               
        self.particle_canvas = tk.Canvas(self.right_frame, width=230, height=230, bd=0, bg='#2c3e50', relief='flat', highlightthickness=0)
        self.particle_canvas.grid(row=8, column=0, sticky="nw", padx=(20,10), pady=(0, 0))
        
        #######################################################################
        # Back to Homepage button
        #######################################################################
        
        self.back_button = tk.Button(self.right_frame, text="Back to homepage", command=self.go_home,
                                     bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                     borderwidth=1, relief="flat", width=29)
        self.back_button.grid(row=9, column=0, columnspan=1, sticky="nw", pady=(25, 10), padx=(5, 10))
        
        self.back_button.bind("<Enter>", self.on_hover_buttons)
        self.back_button.bind("<Leave>", self.on_leave_buttons)
        
    ###########################################################################
    ########################### Log message function ##########################
    ###########################################################################
        
    def log_message(self, message_type, message):
        """
        Logs a message to the console.
        """
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, message + "\n", message_type)
        self.console_text.config(state=tk.DISABLED)
        self.console_text.yview(tk.END)
        
    ###########################################################################
    ######################### Image import functions ##########################
    ###########################################################################
        
    def open_file_button_clicked(self):
        """
        Open the file explorer to allow the user to select an image to be imported. Before importing the image, it resets all variables, canvas and figures.
    
        Functions called:
            open_stones_file (from ImportImages file)    
            reset_all (from ImportImages file)
            plot_histogram (local)
            show_stones_technical_frame_popup (local)
        """
        reset_all()
        self.plot_histogram(which='initialise')
        self.image_canvas.delete("all")
        self.particle_canvas.delete("all")
        self.tooltip_label.place_forget() 
        open_stones_file(self, self.pcam_characteristics.image_height.get())
        if IMG.tk_resized_image:
            self.show_stones_technical_frame_popup(IMG.filename)
                
    def show_stones_technical_frame_popup(self, filename):
        """
        Creates a temporary popup window where the user can draw a line corresponding to 1 cm in real life. The image is only imported once this popup is validated.
        """
        popup = tk.Toplevel(self.root)
        popup.title("Image scale definition")
        popup.configure(bg="#34495e")
        popup.geometry("950x730")
    
        popup_frame_title = tk.Label(
            popup,
            text="Select the start and end point representing 1 cm on the scale of the image:",
            bg="#34495e",
            fg="white",
            wraplength=900,
            justify="left",
            font=("Segoe UI", 12, "bold")
        )
        popup_frame_title.grid(row=0, column=0, columnspan=1, padx=(20, 0), pady=(20, 3), sticky="nw")
    
        canvas = tk.Canvas(popup, bg="white", width=900, height=600, highlightthickness=0)
        canvas.grid(row=2, column=0, columnspan=2, padx=20, pady=(10, 20))
    
        img = Image.open(filename)
        self.original_width, self.original_height = img.size  # Store original dimensions
        RESIZE_WIDTH = 900
        RESIZE_HEIGHT = 600
        self.img_tk = ImageTk.PhotoImage(img.resize((RESIZE_WIDTH, RESIZE_HEIGHT)))
        canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)
    
        self.start_point = None
        self.end_point = None
        self.pixel_label = None
    
        # Tooltip for zoomed-in view
        tooltip = tk.Toplevel(popup)  
        tooltip.geometry("150x150") 
        tooltip.overrideredirect(True)  
        tooltip.withdraw() 
        tooltip_frame = tk.Frame(tooltip, bg="white", borderwidth=1, relief="solid")
        tooltip_frame.pack(padx=2, pady=2)
        tooltip_label = tk.Label(tooltip_frame)
        tooltip_label.pack()
    
        # Display coordinates label
        self.coordinates_label = tk.Label(popup, text="", bg="#34495e", fg="white", font=("Segoe UI", 12))
        self.coordinates_label.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 20))
    
        def on_click(event):
            """
            Function to allow the user to draw a line between two points to measure 1 cm.
            """
            if self.start_point is None:
                self.start_point = (event.x, event.y)
                canvas.create_text(event.x, event.y, text="+", font=("Arial", 14), fill="white")
            elif self.end_point is None:
                self.end_point = (event.x, event.y)
                canvas.create_text(event.x, event.y, text="+", font=("Arial", 14), fill="white")
                canvas.create_line(self.start_point[0], self.start_point[1], event.x, event.y, fill="white", width=2)
                self.calculate_pixel_size(popup, self.original_width, self.original_height)
            else:
                canvas.delete("all") 
                canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)  
                self.start_point = (event.x, event.y)
                self.end_point = None
                canvas.create_text(event.x, event.y, text="+", font=("Arial", 14), fill="white")
                
        canvas.bind("<Button-1>", on_click)
        
        def on_mouse_move(event):
            """
            Function to help the user locate the cursor on the image.
            """
            canvas.delete("crosshair")
            canvas.create_line(event.x, 0, event.x, 600, fill="yellow", dash=(2, 2), tags="crosshair")
            canvas.create_line(0, event.y, 900, event.y, fill="yellow", dash=(2, 2), tags="crosshair")
            threading.Thread(target=self.process_zoom_area, args=(event.x, event.y, img, 900, 600, tooltip_label, tooltip)).start()

        canvas.bind("<Motion>", on_mouse_move)
    
        button_frame = tk.Frame(popup, bg="#34495e")
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
    
        ok_button = tk.Button(
            button_frame,
            text="OK",
            command=lambda: self.import_image(filename, popup),
            width=12,
            font=("Segoe UI", 11),
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            activeforeground="white"
        )
        ok_button.grid(row=0, column=0, padx=20)
    
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=popup.destroy,
            width=12,
            font=("Segoe UI", 11),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white"
        )
        cancel_button.grid(row=0, column=1, padx=20)
    
        def on_mouse_leave(event):
            """
            Function to remove the tooltip once the cursor is out of the image.
            """
            tooltip.withdraw()
    
        def on_mouse_enter(event):
            """
            Function to create the tooltip once the cursor is in the image.
            """
            if self.start_point or self.end_point:  
                tooltip.deiconify() 
    
        canvas.bind("<Leave>", on_mouse_leave)
        canvas.bind("<Enter>", on_mouse_enter)
        
    def process_zoom_area(self, x, y, img, resized_width, resized_height, tooltip_label, tooltip):
        """
        Function to create a zoomed-in image tooltip representing the 14x14 pixel area where the cursor is.
        """
        zoom_area_size = 14
        x0 = max(x - zoom_area_size // 2, 0)
        y0 = max(y - zoom_area_size // 2, 0)
        x1 = min(x + zoom_area_size // 2, resized_width)
        y1 = min(y + zoom_area_size // 2, resized_height)
        
        cropped_img = img.crop((
            x0 * (self.original_width / resized_width), 
            y0 * (self.original_height / resized_height), 
            x1 * (self.original_width / resized_width), 
            y1 * (self.original_height / resized_height)
        ))
        
        cropped_img = cropped_img.convert("RGBA")
        zoomed_img = cropped_img.resize((150, 150), Image.NEAREST)
        center_x = 150 // 2
        center_y = 150 // 2
        
        # Draw a cross at the center of the zoomed image
        for i in range(-5, 6):  
            if 0 <= center_x + i < 150 and 0 <= center_y < 150:  
                zoomed_img.putpixel((center_x + i, center_y), (255, 255, 0, 255))  
            if 0 <= center_x < 150 and 0 <= center_y + i < 150:  
                zoomed_img.putpixel((center_x, center_y + i), (255, 255, 0, 255))
        
        # Use the main thread to update with the new image
        self.root.after(0, self.update_tooltip, zoomed_img, x, y, tooltip_label, tooltip)
    
    def update_tooltip(self, zoomed_img, x, y, tooltip_label, tooltip):
        """
        Function to update the tooltip as the cursor moves over the image.
        """
        zoomed_img_tk = ImageTk.PhotoImage(zoomed_img)
        tooltip_label.config(image=zoomed_img_tk)
        tooltip_label.image = zoomed_img_tk 
        tooltip.geometry(f"+{x + 15}+{y + 15}")
        tooltip.deiconify()
    
    def calculate_pixel_size(self, popup, original_width, original_height):
        """
        Function to calculate the pixel size.
        """
        if self.pixel_label:
            self.pixel_label.destroy()
        if self.start_point and self.end_point:
            canvas_width = 900  
            canvas_height = 600
            
            # Calculate scaling factors based on the original image dimensions
            scale_x = original_width / canvas_width
            scale_y = original_height / canvas_height
            
            # Calculate pixel coordinates in the original image
            start_x = int(self.start_point[0] * scale_x)
            start_y = int(self.start_point[1] * scale_y)
            end_x = int(self.end_point[0] * scale_x)
            end_y = int(self.end_point[1] * scale_y)
    
            # Calculate distance in pixels using original coordinates
            pixel_distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
            
            if pixel_distance > 0:
                real_world_distance_cm = 1
                pixel_size = real_world_distance_cm / pixel_distance              
                IMG.pixel_size = pixel_size
                self.pixel_label = tk.Label(
                    popup, 
                    text=f'Calculated pixel size = {pixel_distance:.3f} pix and {pixel_size:.3f} cm', 
                    bg="#34495e", 
                    fg="white", 
                    font=("Segoe UI", 12)
                )
                self.pixel_label.grid(row=2, column=0, columnspan=1, padx=(20, 0), pady=(0, 10), sticky="nw")
                
    def import_image(self, filename, popup):
        """
        Function to import the image once the pixel size is calculated.
        """
        try:            
            if IMG.tk_resized_image:
                self.image_list = [IMG.tk_resized_image]  
                self.current_image_index = 0
                self.display_image(self.current_image_index)
                self.log_message('new', "New processing started.")
                self.log_message('success', "Image successfully imported.")
                self.log_message('info', f"Current image name is: {IMG.image_name}")
                self.log_message('info', f"Current image date is: {IMG.date_time}")
                self.log_message('info', f"Calculated pixel size is: {IMG.pixel_size:.4f} cm")
                self.log_message('info', f"Image was shot using {IMG.camera} equipped with {IMG.lens}, at aperture of f/{IMG.aperture}, focal length of {IMG.focal_length} mm, exposure time of {IMG.exposure} s and ISO {IMG.iso}")
                self.image_canvas.bind("<Button-1>", self.start_measurement) 
                self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
                self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
                self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
            
                if IMG.selected_image is not None:
                    self.plot_histogram(which='original_histogram')
                else:
                    self.plot_histogram(which='initialise') 
                popup.destroy() 
        except ValueError:
                pass
                        
    def reset_button_clicked(self):
        """
        Function to reset all variables.
        """
        reset_all()
        self.image_canvas.delete("all")
        self.plot_histogram(which='initialise')
        if IMG.selected_image is None:
            self.log_message('success', "All image variables have been successfully reset")
            self.log_message('info', f"Current image name is: {IMG.image_name}")
            self.log_message('info', f"Current image date is: {IMG.date_time}")
            self.log_message('info', f"Calculated pixel size is: {IMG.pixel_size:.4f} cm")
        else: 
            self.log_message('error', "Reset didn't function")
            self.log_message('info', f"Current image name is: {IMG.image_name}")
            self.log_message('info', f"Current image date is: {IMG.date_time}")
            self.log_message('info', f"Calculated pixel size is: {IMG.pixel_size:.4f} cm")
            
    def go_home(self):
        """
        Reset all values and back to homepage.
    
        Functions called:  
            reset_all (from ImportImages file)
            destroy (local)
            on_go_home (local)
        """
        self.destroy()
        self.on_go_home()
        reset_all()

    def destroy(self):
        """
        Destroys current page.
        """
        for widget in self.root.winfo_children():
            widget.destroy()
            
        for i in range(self.root.grid_size()[0]):  
            self.root.grid_columnconfigure(i, weight=0, uniform='')
    
        for i in range(self.root.grid_size()[1]):  
            self.root.grid_rowconfigure(i, weight=0, uniform='')
            
    ###########################################################################
    ############################ Denoising functions ##########################
    ###########################################################################
        
    def update_filter_strength(self, *args):
        """
        Updates denoising filter strength label.
        """
        self.filter_strength_value_label.config(text=str(int(self.denoise_filter_strength.get())))

    def apply_denoising(self):
        """
        Applies a denoising filter to the currently selected image.
    
        Functions called:
            rgb_to_grey (from ImageEnhancement file)
            denoise (from ImageEnhancement file)
            plot histogram (local)
        """
        filter_strength = round(self.denoise_filter_strength.get(), 0)
        if IMG.selected_image is None:
            self.log_message('error', f"An error occurred during the conversion to greyscale. Selected image is {IMG.selected_image}")
        rgb_to_grey(IMG.selected_image)
        if IMG.img_grey is None:
            self.log_message('error', f"An error occurred during the conversion to greyscale. Grey image is {IMG.img_grey}")
        denoise(IMG.img_grey, filter_strength)
        if IMG.img_modified is not None:
            self.log_message('success', f"\nDenoising with a filter strength of {str(int(self.denoise_filter_strength.get()))} has been performed successfully.")
        else:
            self.log_message('error', f"An error occurred during the denoising process. Denoised image is {IMG.img_modified}")
        if IMG.tk_denoised_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_denoised_image, tags="denoised img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind("<Button-1>", self.start_measurement) 
            self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
            self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
            self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
        self.plot_histogram(which='modified_histogram')
        
    ###########################################################################
    ###################### Histogram stretching drop-down #####################
    ###########################################################################
    
    def apply_histogram_stretching(self):
        """
        Applies histogram stretching.
        
        Functions called:
            histogram_stretching (from ImageEnhancement file)
            plot histogram (local)
        """
        image = IMG.img_modified
        minimum = self.min_value.get()
        maximum = self.max_value.get()
        if IMG.img_modified is not None:
            histogram_stretching(image, minimum, maximum)
            self.log_message('success', f"Histogram clipping between {str(int(self.min_value.get()))} and {str(int(self.max_value.get()))}, and normalized has been performed successfully.")
        else:
            self.log_message('error', f"An error occurred during the histogram stretching process. Stretched image is {IMG.img_modified}")
        if IMG.tk_stretched_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_stretched_image, tags="stretched img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind("<Button-1>", self.start_measurement) 
            self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
            self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
            self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
        self.plot_histogram(which='modified_histogram')
        
    ###########################################################################
    ######################### Reconstruction drop-down ########################
    ###########################################################################
    
    def update_SubDiff(self, *args):
        """
        Updates the SubDiff label.
        """
        self.SubDiff_value.config(text=str(int(self.SubDiff.get())))
    
    def apply_image_reconstruction(self):
        """
        Applies image reconstruction.
        
        Functions called:
            image_reconstruction (from ImageEnhancement file)
            plot histogram (local)
        """
        image = IMG.img_modified
        subdiff = round(self.SubDiff.get(), 0)
        if IMG.img_modified is not None:
            image_reconstruction(image, subdiff)
            self.log_message('success', f"Image reconstruction with a value of {str(int(self.SubDiff.get()))} has been performed successfully.")
        else:
            self.log_message('error', f"An error occurred during the image reconstruction. Reconstructed image is {IMG.img_reconstructed}")
        if IMG.tk_reconstructed_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_reconstructed_image, tags="reconstructed img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind("<Button-1>", self.start_measurement) 
            self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
            self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
            self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
        self.plot_histogram(which='modified_histogram')
        
    ###########################################################################
    ####################### Shadow correction drop-down #######################
    ###########################################################################
    
    def update_gamma(self, *args):
        """
        Updates the gamma label.
        """
        gamma = self.gamma.get()
        self.gamma_value.config(text="{:.2f}".format(gamma))
    
    def apply_gamma_correction(self):
        """
        Applies gamma correction.
        
        Functions called:
            lighten_shadows_with_gamma (from ImageEnhancement file)
            plot histogram (local)
        """
        image = IMG.img_modified
        gamma = round(self.gamma.get(), 2)
        if IMG.img_modified is not None:
            lighten_shadows_with_gamma(image, gamma)
            self.log_message('success', f"Shadow correction with a value of {gamma} has been performed successfully.")
        else:
            self.log_message('error', "An error occurred during the shadow correction.")
        if IMG.tk_gamma_corrected_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_gamma_corrected_image, tags="corrected shadow img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind("<Button-1>", self.start_measurement) 
            self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
            self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
            self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
        self.plot_histogram(which='modified_histogram')
        
    ###########################################################################
    ############################ Extraction functions #########################
    ###########################################################################
        
    def apply_extract_particles_on_white(self):
        """
        Extracts gravels and updates the canvas with contours, centroids and binds it with actions (measurement, tooltip). White background option.
        
        Functions called:
            extract_stones (from ParticleExtraction file)
            draw_centroids_on_canvas (local)
        """
        if IMG.selected_image is None:
            self.log_message('error', f"Selected image is {IMG.selected_image}")
        extract_stones(self, IMG.image_name)
        if IMG.stats is None:
            self.log_message('error', f"An error occurred during the particle extraction. Stats is {IMG.stats}")
        else:
            pass

        if IMG.tk_binary_image and IMG.tk_extracted_particles_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_binary_image, tags="binary img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_extracted_particles_image, tags="extracted particles img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.draw_centroids_on_canvas()
            self.image_canvas.bind('<Motion>', lambda event: self.show_particle_tooltip(event))
            self.image_canvas.bind("<Button-3>", self.on_right_mouse_down)  
            self.image_canvas.bind("<B3-Motion>", self.on_mouse_drag)  
            self.image_canvas.bind("<ButtonRelease-3>", self.on_mouse_up) 
    
            self.image_canvas.bind("<Button-1>", self.start_measurement) 
            self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
            self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
            self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
            
    def apply_extract_particles_on_green(self):
        """
        Extracts gravels and updates the canvas with contours, centroids and binds it with actions (measurement, tooltip). Green background option.
        
        Functions called:
            extract_stones (from ParticleExtraction file)
            draw_centroids_on_canvas (local)
        """
        if IMG.selected_image is None:
            self.log_message('error', f"Selected image is {IMG.selected_image}")
        extract_stones_on_green(self, IMG.image_name)
        if IMG.stats is None:
            self.log_message('error', f"An error occurred during the particle extraction. Stats is {IMG.stats}")
        else:
            pass

        if IMG.tk_binary_image and IMG.tk_extracted_particles_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_binary_image, tags="binary img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_extracted_particles_image, tags="extracted particles img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.draw_centroids_on_canvas()
            self.image_canvas.bind('<Motion>', lambda event: self.show_particle_tooltip(event))
            self.image_canvas.bind("<Button-3>", self.on_right_mouse_down)  
            self.image_canvas.bind("<B3-Motion>", self.on_mouse_drag)  
            self.image_canvas.bind("<ButtonRelease-3>", self.on_mouse_up) 
    
            self.image_canvas.bind("<Button-1>", self.start_measurement) 
            self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
            self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
            self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
        
    ###########################################################################
    ######################## Filter intensity drop-down #######################
    ###########################################################################
    
    def apply_size_filter(self):
        """
        Filters stones based on their size (in pixels).
        
        Functions called:
            filter_stones_on_size (from ParticleExtraction file)
            draw_centroids_on_canvas (local)
        """
        MinSize = self.MinSize.get()
        if IMG.stats is not None:
            filter_stones_on_size(self, IMG.stats, MinSize)
            self.log_message('success', f"Particles smaller than {str(self.MinSize.get())} cm were filtered out.")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind('<Motion>', lambda event: self.show_particle_tooltip(event))
            self.draw_centroids_on_canvas()
            if any(hasattr(prop, 'convexity') and prop.convexity for prop in IMG.stats):
                self.plot_histogram(which="axis_length_histogram")
                stones_sample_statistics(IMG.stats, self)
        else:
            self.log_message('error', "An error occurred during the particle filtration.")
            
    ###########################################################################
    ####################### Image statistics computation ######################
    ###########################################################################
        
    def apply_stones_statistics_computation(self):
        """
        Computes gravels and image statistics.
        
        Functions called:
            compute_stones_statistics (from StatisticsComputation file)
            draw_centroids_on_canvas (local)
            plot_histogram (local)
        """
        if IMG.stats is not None:
            compute_stones_statistics(self, IMG.stats, IMG.pixel_size)
            self.image_canvas.bind('<Motion>', lambda event: self.show_particle_tooltip(event))
            self.draw_centroids_on_canvas()
            self.plot_histogram(which='axis_length_histogram')
        else:
            self.log_message('error', "There is no statistics available")
        
    ###########################################################################
    ############################# Toggle functions ############################
    ###########################################################################
    
    def toggle_denoising_controls(self):
        """
        Shows or hides denoising buttons.
        """
        if self.denoising_controls_visible:
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.denoising_controls_visible = False
        else:
            self.filter_strength_label.grid()
            self.filter_strength_value_label.grid()
            self.filter_strength_slider.grid()
            self.denoise_button.grid()
            self.denoising_controls_visible = True
            
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_controls_visible = False
            self.histogram_stretching_button.grid_remove()
            
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.reconstruction_controls_visible = False
            
            self.gamma_label.grid_remove()
            self.gamma_value.grid_remove()
            self.gamma_slider.grid_remove()
            self.gamma_button.grid_remove()
            self.shadow_controls_visible = False
            
    def toggle_histogram_controls(self):
        """
        Shows or hides histogram stretching buttons.
        """
        if self.histogram_controls_visible:
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_stretching_button.grid_remove()
            self.histogram_controls_visible = False
        else:
            self.min_value_label.grid()
            self.max_value_label.grid()
            self.max_value_entry.grid()
            self.min_value_entry.grid() 
            self.histogram_stretching_button.grid()
            self.histogram_controls_visible = True
            
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.denoising_controls_visible = False
            
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.reconstruction_controls_visible = False
            
            self.gamma_label.grid_remove()
            self.gamma_value.grid_remove()
            self.gamma_slider.grid_remove()
            self.gamma_button.grid_remove()
            self.shadow_controls_visible = False
            
    def toggle_reconstruction_controls(self):
        """
        Shows or hides image reconstruction buttons.
        """
        if self.reconstruction_controls_visible:
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.reconstruction_controls_visible = False
        else:
            self.SubDiff_label.grid()
            self.SubDiff_value.grid()
            self.SubDiff_slider.grid()
            self.reconstruction_button.grid()
            self.reconstruction_controls_visible = True
            
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.denoising_controls_visible = False
            
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_stretching_button.grid_remove()
            self.histogram_controls_visible = False 
            
            self.gamma_label.grid_remove()
            self.gamma_value.grid_remove()
            self.gamma_slider.grid_remove()
            self.gamma_button.grid_remove()
            self.shadow_controls_visible = False

    def toggle_shadow_controls(self):
        """
        Shows or hides shadow correction buttons.
        """
        if self.shadow_controls_visible:
            self.gamma_label.grid_remove()
            self.gamma_value.grid_remove()
            self.gamma_slider.grid_remove()
            self.gamma_button.grid_remove()
            self.shadow_controls_visible = False
        else:
            self.gamma_label.grid()
            self.gamma_value.grid()
            self.gamma_slider.grid()
            self.gamma_button.grid()
            self.shadow_controls_visible = True
            
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.denoising_controls_visible = False
            
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_stretching_button.grid_remove()
            self.histogram_controls_visible = False

            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.reconstruction_controls_visible = False              
            
    def toggle_min_size_controls(self):
        """
        Shows or hides filtering buttons.
        """
        if self.min_size_controls_visible:
            self.MinSize_label.grid_remove()
            self.MinSize_entry.grid_remove()
            self.filter_size_button.grid_remove()
            self.min_size_controls_visible = False
        else:
            self.MinSize_label.grid()
            self.MinSize_entry.grid()
            self.filter_size_button.grid()
            self.min_size_controls_visible = True
    
    ###########################################################################
    ########################### Plot image histogram ##########################
    ###########################################################################
    
    def plot_histogram(self, which):
        """
        Computes and shows image histogram or PSD.
        """
        # Initializes figure
        self.figure.patch.set_facecolor('#2c3e50')
        self.ax.set_facecolor('none')
        self.expanded_figure.patch.set_facecolor('#2c3e50')
        self.expanded_ax.set_facecolor('none')
        self.ax.clear()
        self.expanded_ax.clear()
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        for spine in self.expanded_ax.spines.values():
            spine.set_visible(False)  
        if hasattr(self, 'ax2') and self.ax2 is not None:
            self.ax2.cla()  
            self.ax2.set_xticks([])
            self.ax2.set_yticks([])
            self.ax2.set_xlabel('')
            self.ax2.set_ylabel('')
            self.ax.legend('')
            self.ax.grid('')
            self.ax.set_xlim('')
            self.ax.set_ylim('')
            for spine in self.ax2.spines.values():
                spine.set_visible(False)
        if hasattr(self, 'expanded_ax2') and self.expanded_ax2 is not None:
            self.expanded_ax2.cla()  
            self.expanded_ax2.set_xticks([])
            self.expanded_ax2.set_yticks([])
            self.expanded_ax2.set_xlabel('')
            self.expanded_ax2.set_ylabel('')
            self.expanded_ax2.legend('')
            self.expanded_ax2.grid('')
            self.expanded_ax2.set_xlim('')
            self.expanded_ax2.set_ylim('')
            for spine in self.expanded_ax2.spines.values():
                spine.set_visible(False) 
        self.ax.set_xscale('linear')  
        self.expanded_ax.set_xscale('linear')
    
        if which == 'original_histogram':
            
            hist = cv2.calcHist([IMG.selected_image], [0], None, [256], [0, 256])
            bars = self.ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            expanded_bars = self.expanded_ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            
            self.ax.set_xlim([0, 255])
            self.expanded_ax.set_xlim([0, 255])
    
            self.ax.set_xlabel('Pixel intensity', color='white', fontsize=6, labelpad=2)
            self.ax.set_ylabel('Frequency', color='white', fontsize=6, labelpad=2)
            self.ax.grid(axis='both', which='both', linewidth=0.1)
    
            self.expanded_ax.set_xlabel('Pixel intensity', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.set_ylabel('Frequency', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.grid(axis='both', which='both', linewidth=0.1)
            
            self.ax.tick_params(axis='both', labelsize=6, length=2, colors='white')
            self.expanded_ax.tick_params(axis='both', which='both', labelsize=6, length=2, colors='white')
            
            for spine in self.ax.spines.values():
                spine.set_visible(True)
            for spine in self.expanded_ax.spines.values():
                spine.set_visible(True)  
            
            self.ax.tick_params(axis='both', labelsize=6, colors='white', length=2)
            self.ax.spines['top'].set_color('white')
            self.ax.spines['right'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.spines['bottom'].set_color('white')
    
            self.expanded_ax.tick_params(axis='both', labelsize=8, colors='white', length=2)
            self.expanded_ax.spines['top'].set_color('white')
            self.expanded_ax.spines['right'].set_color('white')
            self.expanded_ax.spines['left'].set_color('white')
            self.expanded_ax.spines['bottom'].set_color('white')
    
            self.figure.tight_layout(pad=1.0)
    
            mplcursors.cursor(bars, hover=True).connect("add", lambda sel: (sel.annotation.set_text(
                f'Intensity: {sel.index}\nFrequency: {sel.target[1]:.0f}'
            ),
            setattr(sel.annotation, 'arrowstyle', 'fancy'),
            setattr(sel.annotation, 'linewidth', 0.3),
            sel.annotation.set_fontsize(5),
            sel.annotation.set_backgroundcolor('black'),
            sel.annotation.set_color('lime')
            ))
    
        if which == 'modified_histogram':
            
            hist = cv2.calcHist([IMG.img_modified], [0], None, [256], [0, 256])
            bars = self.ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            expanded_bars = self.expanded_ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            
            self.ax.set_xlim([0, 255])
            self.ax.set_ylim([0, np.max(hist) * 1.1])
            self.expanded_ax.set_xlim([0, 255])
            self.expanded_ax.set_ylim([0, np.max(hist) * 1.1])
            
            self.ax.tick_params(axis='both', labelsize=6, length=2, colors='white')
            self.expanded_ax.tick_params(axis='both', which='both', labelsize=6, length=2, colors='white')
    
            self.ax.set_xlabel('Pixel intensity', color='white', fontsize=6, labelpad=2)
            self.ax.set_ylabel('Frequency', color='white', fontsize=6, labelpad=2)
            self.ax.grid(axis='both', which='both', linewidth=0.1)
    
            self.expanded_ax.set_xlabel('Pixel intensity', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.set_ylabel('Frequency', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.grid(axis='both', which='both', linewidth=0.1)
            
            for spine in self.ax.spines.values():
                spine.set_visible(True)
            for spine in self.expanded_ax.spines.values():
                spine.set_visible(True) 

            self.ax.tick_params(axis='both', labelsize=6, colors='white', length=2)
            self.ax.spines['top'].set_color('white')
            self.ax.spines['right'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.spines['bottom'].set_color('white')
    
            self.expanded_ax.tick_params(axis='both', labelsize=8, colors='white', length=2)
            self.expanded_ax.spines['top'].set_color('white')
            self.expanded_ax.spines['right'].set_color('white')
            self.expanded_ax.spines['left'].set_color('white')
            self.expanded_ax.spines['bottom'].set_color('white')
            
            self.figure.tight_layout(pad=1.0)
    
            mplcursors.cursor(bars, hover=True).connect("add", lambda sel: (sel.annotation.set_text(
                f'Intensity: {sel.index}\nFrequency: {sel.target[1]:.0f}'
            ),
            setattr(sel.annotation, 'arrowstyle', 'fancy'),
            setattr(sel.annotation, 'linewidth', 0.3),
            sel.annotation.set_fontsize(5),
            sel.annotation.set_backgroundcolor('black'),
            sel.annotation.set_color('lime')
            ))
            mplcursors.cursor(expanded_bars, hover=True).connect("add", lambda sel: (sel.annotation.set_text(
                f'Intensity: {sel.index}\nFrequency: {sel.target[1]:.0f}'
            ),
            setattr(sel.annotation, 'arrowstyle', 'fancy'),
            setattr(sel.annotation, 'linewidth', 0.3),
            sel.annotation.set_fontsize(5),
            sel.annotation.set_backgroundcolor('black'),
            sel.annotation.set_color('lime')
            ))
            
        if which == 'axis_length_histogram':
            
            major_axis_lengths = [prop.major_axis_length_cm for prop in IMG.stats]
            minor_axis_lengths = [prop.minor_axis_length_cm for prop in IMG.stats]
            if not major_axis_lengths and not minor_axis_lengths:
                self.log_message('error', "No data to plot.")
                return 
        
            bin_width = 1 
            bins = int((20 - 0) / bin_width) 
            bin_edges = np.arange(0, 21, bin_width)  
            bar_width = (1 / 2) * (bin_edges[1] - bin_edges[0])

            major_hist, _ = np.histogram(major_axis_lengths, bins=bin_edges)
            minor_hist, _ = np.histogram(minor_axis_lengths, bins=bin_edges)

            indices = np.arange(bins) 
        
            self.ax.bar(indices, major_hist, width=bar_width, color='lime', 
                         label='Major axis', edgecolor='white', linewidth=0.3, align='edge')
            self.ax.bar(indices + bar_width, minor_hist, width=bar_width, color='#FFBC42', 
                         label='Minor axis', edgecolor='white', linewidth=0.3, align='edge')
        
            self.expanded_ax.bar(indices, major_hist, width=bar_width, color='lime', 
                                 label='Major axis', edgecolor='white', linewidth=0.3, align='edge')
            self.expanded_ax.bar(indices + bar_width, minor_hist, width=bar_width, color='#FFBC42', 
                                 label='Minor axis', edgecolor='white', linewidth=0.3, align='edge')
        
            self.ax.set_xlim(-bar_width, bins)
            self.expanded_ax.set_xlim(-bar_width, bins)
        
            self.ax.set_xlabel('Axis length (cm)', color='white', fontsize=6, labelpad=2)
            self.ax.set_ylabel('Frequency (count)', color='white', fontsize=6, labelpad=2)
            
            self.ax.minorticks_on()
            self.expanded_ax.minorticks_on()
            self.ax.xaxis.set_major_locator(ticker.MultipleLocator(5))   
            self.ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))  
            self.ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True)) 
            self.ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())  
            self.ax.grid(axis='both', which='both', linewidth=0.1) 
            self.ax.grid(axis='both', which='minor', linestyle='--', linewidth=0.05) 
            self.expanded_ax.minorticks_on()
            self.expanded_ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
            self.expanded_ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
            self.expanded_ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True)) 
            self.expanded_ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())  
            self.expanded_ax.grid(axis='both', which='both', linewidth=0.1)
            self.expanded_ax.grid(axis='both', which='minor', linestyle='--', linewidth=0.05)
            
            self.expanded_ax.set_xlabel('Axis length (cm)', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.set_ylabel('Frequency (count)', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.grid(axis='both', which='both', linewidth=0.1)

            self.ax.legend(loc='upper right', fontsize=6, labelcolor='white', frameon=False)
            self.expanded_ax.legend(loc='upper right', fontsize=8, labelcolor='white', frameon=False)
            self.ax.tick_params(axis='both', labelsize=6, length=2, colors='white')
            self.expanded_ax.tick_params(axis='both', labelsize=8, length=2, colors='white')
        
            for spine in self.ax.spines.values():
                spine.set_color('white')
                spine.set_visible(True)
            for spine in self.expanded_ax.spines.values():
                spine.set_color('white')
                spine.set_visible(True)
        
            self.figure.tight_layout(pad=1.0)
            
        elif which == "initialise":
            self.ax.clear()
            self.expanded_ax.clear()
            self.ax.text(0.5, 0.5, 'No image selected', color='#FFBC42',
                          fontsize=8, ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_xlabel('', color='white')  
            self.ax.set_ylabel('', color='white')
            self.ax.spines['top'].set_color('#2c3e50')  
            self.ax.spines['right'].set_color('#2c3e50') 
            self.ax.spines['left'].set_color('#2c3e50')  
            self.ax.spines['bottom'].set_color('#2c3e50') 
            self.ax.tick_params(axis='both', colors='#2c3e50') 
            
            self.expanded_ax.text(0.5, 0.5, 'No image selected', color='#FFBC42',
                          fontsize=8, ha='center', va='center')
            self.expanded_ax.set_xticks([])
            self.expanded_ax.set_yticks([])
            self.expanded_ax.set_xlabel('', color='white')  
            self.expanded_ax.set_ylabel('', color='white')
            self.expanded_ax.spines['top'].set_color('#2c3e50')  
            self.expanded_ax.spines['right'].set_color('#2c3e50') 
            self.expanded_ax.spines['left'].set_color('#2c3e50')  
            self.expanded_ax.spines['bottom'].set_color('#2c3e50') 
            self.expanded_ax.tick_params(axis='both', colors='#2c3e50') 
            
            self.figure.tight_layout(pad=1.0)
        
        self.canvas.draw()
        self.expanded_canvas.draw()
        
    ###########################################################################
    ##### ################ Calling save outputs functions #####################
    ###########################################################################
            
    def save_csv_button_clicked(self):
        """
        Exports CSV files when button clicked.
        
        Functions called:
            save_gravels_csv (from ExportToCSV file)
            save_image_csv (from ExportToCSV file)
        """
        save_gravels_csv(IMG.stats, IMG.image_paths, self)
        save_sample_csv(IMG.stats, self)
            
    def save_vignettes_button_clicked(self):
        """
        Exports individual vignettes when button clicked.
        
        Functions called:
            generate_vignette (from VignetteGeneration file)
        """
        generate_vignette(self, "gravel", IMG.stats)
        
    ###########################################################################
    ######################### Dynamic layout functions ########################
    ###########################################################################
    
    def on_hover_buttons(self, event):
        """
        Layout when mouse is above a button.
        """
        event.widget.config(bg=self.hover_color)
        
    def on_leave_buttons(self, event):
        """
        Layout when mouse leaves a button.
        """
        event.widget.config(bg=self.button_color)
        
    def on_hover(self, widget):
        """
        Layout when mouse is above a button.
        """
        widget.config(bg="#2c3e50", fg="white",font=("Segoe UI", 11), borderwidth=1, highlightcolor='lime', highlightthickness=1)
        
    def on_leave(self, widget):
        """
        Layout when mouse leaves a button.
        """
        widget.config(bg="#243342", fg="white",font=("Segoe UI", 11), borderwidth=1, highlightcolor='lime', highlightthickness=0)
    
    ###########################################################################
    ######################### Dynamic canvas functions ########################
    ###########################################################################
    
    def display_image(self, index):
        """
        Displays an image on the canvas.
        """
        self.image_canvas.delete("all")
        if 0 <= index < len(self.image_list):
            IMG.tk_image = self.image_list[index]
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_image, tags="img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
    def update_image_display(self, event):
        """
        Updates the image displayed on the canvas based on the user choice.
        """
        selected_image = self.image_select.get()
        self.image_canvas.delete("all")
        if selected_image == "Denoised Image" and IMG.tk_denoised_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_denoised_image, tags="img")
        elif selected_image == "Original Image" and IMG.tk_resized_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_resized_image, tags="img")
        elif selected_image =="Stretched Image" and IMG.tk_stretched_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_stretched_image, tags="img")
        elif selected_image =="Reconstructed Image" and IMG.tk_reconstructed_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_reconstructed_image, tags="img")
        elif selected_image =="Shadow Corrected Image" and IMG.tk_gamma_corrected_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_gamma_corrected_image, tags="img")
        elif selected_image =="Binary Image" and IMG.tk_binary_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_binary_image, tags="img")
        elif selected_image == "Extracted Particles Image" and IMG.tk_extracted_particles_image:
            self.image_canvas.create_image(0,0,anchor=tk.NW, image=IMG.tk_extracted_particles_image, tags = "extracted particles img")
        elif selected_image =="Extracted Particles Filtered on Intensity" and IMG.tk_extracted_intensity_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_extracted_intensity_image, tags="img")

        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
    def update_scroll_region(self, event=None):
        """
        Scrolls through the frame.
        """
        self.background_processing_frame.update_idletasks()  
        bbox = self.background_canvas.bbox("all")
        canvas_height = self.background_canvas.winfo_height()
        canvas_width = self.background_canvas.winfo_width()
        
        if bbox:
            content_height = bbox[3] - bbox[1]
            
            if content_height > canvas_height:
                self.background_canvas.config(scrollregion=self.background_canvas.bbox("all"))
                self.background_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            else:
                self.background_canvas.config(scrollregion=(0, 0, 0, 0))  
                self.background_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if self.background_canvas.cget("scrollregion") != (0, 0, 0, 0): 
            self.background_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def show_particle_tooltip(self, event):
        """
        Shows a yellow popup when the mouse goes over detected contours (within a radius of 10) and updates the particle canvas with the corresponding contours.
        """
        x, y = event.x, event.y
        tooltip_text = ""
        
        proximity_radius = 10
        matched_particle = None
        
        for i, prop in enumerate(IMG.stats):
            centroid_x, centroid_y = prop.scaled_centroid 
    
            if (centroid_x - proximity_radius <= x <= centroid_x + proximity_radius and
                centroid_y - proximity_radius <= y <= centroid_y + proximity_radius):
    
                if hasattr(prop, 'major_axis_length_cm'):
                    tooltip_text = f"Gravel: {i}\nArea: {prop.area_cm2:.1f} cm²\nEquivalent diameter: {prop.equivalent_diameter_cm:.1f} cm\nMajor axis length: {prop.major_axis_length_cm:.1f} cm\nMinor axis length: {prop.minor_axis_length_cm:.1f} cm\nPerimeter: {prop.perimeter_cm:.1f} cm\nSolidity: {prop.solidity:.2f}\nAspect ratio: {prop.aspect_ratio:.2f}\nForm Factor: {prop.form_factor:.2f}\nSphericity: {prop.sphericity:.2f}\nRoundess: {prop.roundness:.2f}\nExtent: {prop.extent:.2f}\nType: {prop.type}"
        
                else:
                    tooltip_text = f"Gravel: {i}" 

                canvas_x = self.image_canvas.winfo_pointerx() - self.image_canvas.winfo_rootx()
                canvas_y = self.image_canvas.winfo_pointery() - self.image_canvas.winfo_rooty()
                
                canvas_width = self.image_canvas.winfo_width()
                canvas_height = self.image_canvas.winfo_height()
                
                tooltip_width = self.tooltip_label.winfo_reqwidth()
                tooltip_height = self.tooltip_label.winfo_reqheight()
                
                margin = 10
                
                tooltip_x = canvas_x + margin
                tooltip_y = canvas_y + margin
                
                if tooltip_x + tooltip_width > canvas_width:  
                    tooltip_x = canvas_x - tooltip_width - margin  
                    if tooltip_x < 0: 
                        tooltip_x = margin
                
                if tooltip_y + tooltip_height > canvas_height: 
                    tooltip_y = canvas_y - tooltip_height - margin  
                    if tooltip_y < 0:  
                        tooltip_y = margin

                self.tooltip_label.place_forget()
                self.tooltip_label.config(text=tooltip_text)
                self.image_canvas.update_idletasks() 
    
                matched_particle = (prop.scaled_centroid, i, prop.contour)
                break  
                
        if matched_particle is not None:
            centroid, index, contours = matched_particle

            self.particle_canvas.delete("all")

            canvas_width = self.particle_canvas.winfo_width()
            canvas_height = self.particle_canvas.winfo_height()
            self.img = Image.new('RGB', (canvas_width, canvas_height), '#2c3e50')  
            self.img_tk = ImageTk.PhotoImage(self.img)
            self.particle_canvas.create_image(0, 0, anchor="nw", image=self.img_tk)  
    
            if contours is not None:
                all_points = np.concatenate([np.array(contour).reshape(-1, 2) for contour in contours])
                
                try:
                    min_x, min_y = np.min(all_points, axis=0)
                    max_x, max_y = np.max(all_points, axis=0)
                except ValueError as e:
                    self.log_message('error', f"Error while calculating bounding box: {e}")
                    return
    
                bbox_width = max_x - min_x
                bbox_height = max_y - min_y
    
                # Ensure bounding box dimensions are valid
                if bbox_width <= 0 or bbox_height <= 0:
                    self.log_message('error', "Particle too small to be displayed.")
                    return
    
                # Step 2: Calculate the center of the bounding box
                bbox_center_x = min_x + bbox_width / 2
                bbox_center_y = min_y + bbox_height / 2
    
                # Step 3: Determine the canvas center
                canvas_center_x = canvas_width / 2
                canvas_center_y = canvas_height / 2
    
                # Step 4: Calculate the scale factor while preserving the aspect ratio
                scale_margin = 0.9  
                scale_factor = min(canvas_width / bbox_width, canvas_height / bbox_height) * scale_margin
                if scale_factor <= 0:
                    self.log_message('error', "Invalid scaling factor.")
                    return
    
                # Step 5: Translate to center the particle on the canvas
                translate_x = canvas_center_x - (bbox_center_x * scale_factor)
                translate_y = canvas_center_y - (bbox_center_y * scale_factor)
    
                # Separate outer contour from inner contours
                outer_contour = contours[0] 
                inner_contours = contours[1:]  
    
                # Step 6: Scale and translate the outer contour
                scaled_outer_contour = [
                    (point[0] * scale_factor + translate_x, point[1] * scale_factor + translate_y)
                    for point in np.array(outer_contour).reshape(-1, 2)
                ]
    
                # Draw the outer contour 
                if len(scaled_outer_contour) > 2:
                    self.particle_canvas.create_polygon(
                        scaled_outer_contour, fill='#3A506B', outline='lime', width=2
                    )
    
                # Step 7: Scale and translate the inner contours
                for inner_contour in inner_contours:
                    scaled_inner_contour = [
                        (point[0] * scale_factor + translate_x, point[1] * scale_factor + translate_y)
                        for point in np.array(inner_contour).reshape(-1, 2)
                    ]
    
                    # Draw the inner contours 
                    self.particle_canvas.create_polygon(
                        scaled_inner_contour, fill='#2c3e50', outline='lime', width=2
                    )

                # Step 8: Draw the adaptive scale bar
                scale_bar_pixel_length = canvas_width / 3  
                scale_bar_real_length_um = scale_bar_pixel_length * IMG.pixel_size / scale_factor
                scale_bar_x1, scale_bar_y1 = 20, canvas_height - 20 
                scale_bar_x2 = scale_bar_x1 + scale_bar_pixel_length 
    
                self.particle_canvas.create_line(
                    scale_bar_x1, scale_bar_y1, scale_bar_x2, scale_bar_y1, fill="white", width=3
                )
    
                self.particle_canvas.create_text(
                    (scale_bar_x1 + scale_bar_x2) / 2, scale_bar_y1 - 10, text=f"{scale_bar_real_length_um:.1f} µm", fill="white"
                )
            
            else:
                self.log_message('error', "No contours available for the particle.")
        else:
            pass
           
        if tooltip_text != "":
            self.tooltip_label.config(text=tooltip_text)
            self.tooltip_label.place(x=tooltip_x, y=tooltip_y)
        else:
            self.tooltip_label.place_forget()
        
    def draw_centroids_on_canvas(self):
        """
        Shows the centroids of all stones on the image canvas.
        """
        if not IMG.stats:
            self.log_message('error', "No stone to draw.")
            return
        self.image_canvas.delete("centroid", "contour")
        for i, prop in enumerate(IMG.stats):
            centroid_x, centroid_y = prop.scaled_centroid  
            self.image_canvas.create_oval(
                centroid_x - 1, centroid_y - 1, centroid_x + 1, centroid_y + 1,
                outline="red", fill="red", tags=("centroid", f"particle_{i}")
            )
            if hasattr(prop, 'scaled_contour') and prop.scaled_contour:
                for cnt in prop.scaled_contour:
                    if cnt is not None:
                        cnt = np.array(cnt, dtype=np.int32).tolist()
                        self.image_canvas.create_polygon(cnt, outline='lime', fill='', width=1, tags=("contour", f"particle_{i}"))
    
    def on_right_mouse_down(self, event):
        """
        Starts selection rectangle creation on right-click.
        """
        if not self.dragging:
            self.start_x, self.start_y = event.x, event.y
            self.rect_id = self.image_canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y, outline="blue", width=2
            )
            self.dragging = True

    def on_mouse_drag(self, event):
        """
        Drags selection rectangle with the mouse.
        """
        if self.dragging and self.rect_id:
            self.image_canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        """
        Finalizes rectangle creation or show context menu on right-click.
        """
        if self.dragging:
            self.dragging = False  
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            selected_particles = []
            
            # Collect selected particles inside the rectangle
            for i, prop in enumerate(IMG.stats):
                centroid_x, centroid_y = prop.scaled_centroid
                if x_min <= centroid_x <= x_max and y_min <= centroid_y <= y_max:
                    selected_particles.append((i, prop))
            
            self.show_context_menu(event, selected_particles, x_min, x_max, y_min, y_max)
            self.image_canvas.delete(self.rect_id)
            self.rect_id = None 
        else:
            self.log_message('info', "No gravel selected.")
        
    def show_context_menu(self, event, selected_particles, x_min, x_max, y_min, y_max):
        """
        Shows context menu.
        """
        x, y = self.image_canvas.canvasx(event.x), self.image_canvas.canvasy(event.y)
        matched_particle = None
        proximity_radius = 10
    
        # Check if a particle is matched (existing logic)
        if not selected_particles:
            for i, prop in enumerate(IMG.stats):
                centroid_x, centroid_y = prop.scaled_centroid
                if (centroid_x - proximity_radius <= x <= centroid_x + proximity_radius and
                        centroid_y - proximity_radius <= y <= centroid_y + proximity_radius):
                    matched_particle = (i, prop)
                    break
    
        # Create and populate the context menu
        self.context_menu = tk.Menu(self.image_canvas, tearoff=0)
    
        if len(selected_particles) >= 2:
            self.context_menu.add_command(
                label="Remove selected gravels",
                command=lambda: self.remove_particles([p[0] for p in selected_particles])
            )
        elif matched_particle or len(selected_particles) == 1:
            self.context_menu.add_command(
                label="Remove selected gravel",
                command=lambda: self.remove_particle(matched_particle[0] if matched_particle else selected_particles[0][0])
            )
        self.context_menu.add_command(
            label="Restore deleted gravel(s)",
            command=lambda: self.restore_particle()
        )

        self.context_menu.post(event.x_root, event.y_root)
    
    def remove_particle(self, index):
        """
        Removes a selected gravel and updates the contours and centroids on the image canvas.
        
        Functions called:
            draw_centroids_on_canvas (local)
        """
        removed_particle = IMG.stats[index]
        self.removed_particles.append((index, removed_particle))
        del IMG.stats[index]
        self.log_message('info', f"Successfully removed particle {index + 1}.")
        self.image_canvas.delete("centroid")
        self.draw_centroids_on_canvas()
        if any(hasattr(prop, 'convexity') and prop.convexity for prop in IMG.stats):
            self.plot_histogram(which="axis_length_histogram")
            stones_sample_statistics(IMG.stats, self)
    
    def remove_particles(self, particle_indices):
        """        
        Removes selected gravels and updates the contours and centroids on the image canvas.
                
        Functions called:
            draw_centroids_on_canvas (local)
        """
        for index in sorted(particle_indices, reverse=True):
            removed_particle = IMG.stats[index]
            self.removed_particles.append((index, removed_particle))  # Store the particle data
            del IMG.stats[index]
        self.log_message('info', f"Removed {len(particle_indices)} particle(s).")
        self.image_canvas.delete("centroid")
        self.draw_centroids_on_canvas()
        if any(hasattr(prop, 'convexity') and prop.convexity for prop in IMG.stats):
            self.plot_histogram(which="axis_length_histogram")
            stones_sample_statistics(IMG.stats, self)
            
    def restore_particle(self):
        """
        Restores the last deleted gravel(s) and updates the contours and centroids on the image canvas.
        
        Functions called:
            draw_centroids_on_canvas (local)
        """
        if self.removed_particles:
            self.removed_particles.sort(key=lambda x: x[0])
            for index, particle_data in self.removed_particles:
                IMG.stats.insert(index, particle_data)  
            
            self.log_message('info', f"Restored {len(self.removed_particles)} particle(s).")
            self.image_canvas.delete("centroid")
            self.draw_centroids_on_canvas()
            if any(hasattr(prop, 'convexity') and prop.convexity for prop in IMG.stats):
                self.plot_histogram(which="axis_length_histogram")
                stones_sample_statistics(IMG.stats, self)
            self.removed_particles.clear()
        else:
            self.log_message('warning', "No particle to undo.")

    def start_measurement(self, event):
        """
        Starts measurement.
        
        Functions called:
            clear_previous_measurements (local)
        """
        if self.start_point is None:
            self.start_point = (event.x, event.y)
            start_circle = self.image_canvas.create_oval(
                event.x - 3, event.y - 3, event.x + 3, event.y + 3,
                fill="#AF50AF", outline="#AF50AF"
            )
            self.start_circles.append(start_circle)
        else:
            self.clear_previous_measurements(event)
            self.start_point = (event.x, event.y)
            start_circle = self.image_canvas.create_oval(
                event.x - 3, event.y - 3, event.x + 3, event.y + 3,
                fill="#AF50AF", outline="#AF50AF"
            )
            self.start_circles.append(start_circle)

    def update_measurement(self, event):
        """
        Updates measurement line.
        """
        if self.start_point:
            self.end_point = (event.x, event.y)

            for line in self.distance_lines:
                self.image_canvas.delete(line)
            self.distance_lines.clear()

            if self.distance_label:
                self.image_canvas.delete(self.distance_label)
                self.distance_label = None

            for circle in self.end_circles:
                self.image_canvas.delete(circle)
            self.end_circles.clear()  
            distance_line = self.image_canvas.create_line(
                self.start_point[0], self.start_point[1],
                self.end_point[0], self.end_point[1],
                fill="#AF50AF", width=1, dash=(2, 2)  
            )
            self.distance_lines.append(distance_line)

            end_circle = self.image_canvas.create_oval(
                self.end_point[0] - 3, self.end_point[1] - 3,
                self.end_point[0] + 3, self.end_point[1] + 3,
                fill="#AF50AF", outline="#AF50AF"
            )
            self.end_circles.append(end_circle)

    def end_measurement(self, event):
        """
        Ends measurement.
        """
        if self.start_point is not None and self.end_point is not None:
            if IMG.img_modified is not None:
                img_width = IMG.img_modified.shape[1]  
                img_height = IMG.img_modified.shape[0]
            else:
                img_width = IMG.selected_image.shape[1]  
                img_height = IMG.selected_image.shape[0]
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
    
            scale_x = img_width / canvas_width
            scale_y = img_height / canvas_height
    
            start_x = int(self.start_point[0] * scale_x)
            start_y = int(self.start_point[1] * scale_y)
            end_x = int(self.end_point[0] * scale_x)
            end_y = int(self.end_point[1] * scale_y)
    
            distance_pixels = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
    
            distance_line = self.image_canvas.create_line(
                self.start_point[0], self.start_point[1],
                self.end_point[0], self.end_point[1],
                fill="#AF50AF", width=2
            )
            self.distance_lines.append(distance_line)
    
            end_circle = self.image_canvas.create_oval(
                self.end_point[0] - 3, self.end_point[1] - 3,
                self.end_point[0] + 3, self.end_point[1] + 3,
                fill="#AF50AF", outline="#AF50AF"
            )
            self.end_circles.append(end_circle)
    
            distance_cm = distance_pixels * IMG.pixel_size
            
            if self.distance_label:
                self.image_canvas.delete(self.distance_label)
            self.distance_label = self.image_canvas.create_text(
                self.end_point[0] + 10, self.end_point[1] + 10,
                text=f"{distance_pixels:.1f} px / {distance_cm:.2f} cm",
                fill="#AF50AF", anchor="nw"
            )
    
            self.end_point = None

    def clear_previous_measurements(self, event):
        """
        Clear previous measurements.
        """
        for line in self.distance_lines:
            self.image_canvas.delete(line)
        self.distance_lines.clear()

        for circle in self.start_circles:
            self.image_canvas.delete(circle)
        self.start_circles.clear()

        for end_circle in self.end_circles:
            self.image_canvas.delete(end_circle)
        self.end_circles.clear()

        if self.distance_label:
            self.image_canvas.delete(self.distance_label)
            self.distance_label = None

        self.start_point = None
        self.end_point = None
        
    ###########################################################################
    ############################ Plotting functions ###########################
    ###########################################################################
    
    def initialize_expanded_window(self):
        """
        Creates a new window to expand the histogram or PSD, initially hidden.
        """
        self.expanded_window = tk.Toplevel(self.root)
        self.expanded_window.title("Expanded plot")
        self.expanded_window.configure(bg="#2c3e50")
        self.expanded_window.geometry("900x600") 
        self.expanded_window.withdraw()  
        
        self.expanded_figure = Figure(figsize=(6, 4), dpi=300)
        self.expanded_ax = self.expanded_figure.add_subplot(111)
    
        self.expanded_canvas = FigureCanvasTkAgg(self.expanded_figure, master=self.expanded_window)
        self.expanded_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.expanded_figure.tight_layout(pad=4) 

        self.expanded_window.protocol("WM_DELETE_WINDOW", self.hide_expanded_window)
    
    def show_expanded_window(self):
        """
        Shows the window with the expanded histogram or PSD.
        """
        if not hasattr(self, 'expanded_window') or not self.expanded_window.winfo_exists():
            self.initialize_expanded_window()
        self.expanded_window.deiconify()
    
    def hide_expanded_window(self):
        """
        Hides the expanded window when the close button is pressed.
        """
        if hasattr(self, 'expanded_window') and self.expanded_window.winfo_exists():
            self.expanded_window.withdraw()

