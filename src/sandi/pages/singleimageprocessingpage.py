# -*- coding: utf-8 -*-
"""
File: single SPM image processing page
Version: SANDI v1.0.0-beta
Created on Tue Aug 20 16:49:45 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: layout of the single SPM image processing page
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
import os
import sys

###############################################################################
# Import local packages
###############################################################################

from sandi.attributes.PCAM import PCam3_characteristics
from sandi.attributes.IMG import IMG
from sandi.functions.ImportImages import open_file, reset_all
from sandi.functions.ImageEnhancement import (rgb_to_grey, denoise, histogram_stretching,
                                              correct_background_illumination, image_reconstruction,
                                              image_resampling)
from sandi.functions.ParticleExtraction import (extract_particles, filter_particles_on_intensity,
                                                filter_particles_on_size, filter_particles_on_aspect_ratio)
from sandi.functions.VignetteGeneration import generate_vignette
from sandi.functions.StatisticsComputation import compute_image_statistics
from sandi.functions.ExportToCSV import (save_image_csv, save_particles_csv,
                                         save_single_image_PSD_figure, save_single_image_spiderchart_figure)

###############################################################################
# Creation of the page layout
###############################################################################

class SingleImageProcessing:
    
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
        self.last_button_clicked = None
        self.removed_particles = []
        self.dragging = False
        
        self.denoising_controls_visible = False
        self.filter_strength_label.grid_remove()
        self.filter_strength_value_label.grid_remove()
        self.filter_strength_slider.grid_remove()
        self.denoise_button.grid_remove()
        self.return_denoising_arrow_button.grid_remove()
        
        self.histogram_controls_visible = False
        self.min_value_label.grid_remove()
        self.max_value_label.grid_remove()
        self.max_value_entry.grid_remove()
        self.min_value_entry.grid_remove()
        self.histogram_stretching_button.grid_remove()
        self.return_histogram_arrow_button.grid_remove()
        
        self.background_illumination_controls_visible = False
        self.background_window_size_label.grid_remove()
        self.background_window_size_value_label.grid_remove()
        self.background_window_size_slider.grid_remove()
        self.background_illumination_button.grid_remove()
        self.return_illumination_arrow_button.grid_remove()
        
        self.reconstruction_controls_visible = False
        self.SubDiff_label.grid_remove()
        self.SubDiff_value.grid_remove()
        self.SubDiff_slider.grid_remove()
        self.reconstruction_button.grid_remove()
        self.return_reconstruction_arrow_button.grid_remove()
        
        self.resampling_controls_visible = False
        self.pixelsize_label.grid_remove()
        self.pixelsize_value.grid_remove()
        self.resampling_label.grid_remove()
        self.resampling_value.grid_remove()
        self.resampling_slider.grid_remove()
        self.resampling_button.grid_remove()
        self.return_arrow_button.grid_remove()
        
        self.max_intensity_controls_visible = False
        self.MaxInt_label.grid_remove()
        self.MaxInt_value.grid_remove()
        self.MaxInt_slider.grid_remove()
        self.filter_intensity_button.grid_remove()
        
        self.min_size_controls_visible = False
        self.MinSize_label.grid_remove()
        self.MinSize_entry.grid_remove()
        self.filter_size_button.grid_remove()
        
        self.min_aspect_ratio_controls_visible = False
        self.MinAspectRatio_label.grid_remove()
        self.MinAspectRatio_value.grid_remove()
        self.MinAspectRatio_slider.grid_remove()
        self.filter_aspectratio_button.grid_remove()
        
        self.initialize_expanded_window()
        self.plot_histogram(which='initialise')

        self.tooltip_label = tk.Label(self.image_canvas, text="", background="yellow", relief="solid", padx=5, pady=5)
        self.tooltip_label.place_forget() 
        
        self.start_point = None
        self.end_point = None 
        self.distance_lines = []
        self.start_circles = []
        self.end_circles = []  
        self.distance_label = None 
        
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
        
        self.left_frame = tk.Frame(self.root, bg="#2c3e50", padx=5, pady=10)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_propagate(False) 

        #######################################################################
        ### Import file button
        #######################################################################
        
        self.file_button = tk.Button(self.left_frame, text="Select image", command=self.open_file_button_clicked,
                                     bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                     borderwidth=1, relief="flat", width=80)
        self.file_button.grid(row=0, column=0, columnspan=2, pady=(6, 3), padx=(8,0), sticky="nw")
        
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
        self.reset_button.grid(row=1, column=0, columnspan=2, sticky="nw", pady=(3, 10), padx=(8,0))
        
        self.reset_button.bind("<Enter>", self.on_hover_buttons)
        self.reset_button.bind("<Leave>", self.on_leave_buttons)

        #######################################################################
        ### Background processing frame
        #######################################################################
        
        # Create background canvas
        self.background_canvas = tk.Canvas(self.left_frame, bg="#2c3e50", bd=0, highlightthickness=0)
        self.background_canvas.grid(row=4, column=0, padx=(5,0), pady=(0, 0), sticky="ns")

        # Create a frame inside the canvas
        self.background_processing_frame = tk.Frame(self.background_canvas, bg="#2c3e50", bd=0, relief="groove")
        self.background_canvas.create_window((0, 0), window=self.background_processing_frame, anchor="nw")

        # Configure row and column weights for dynamic resizing
        self.left_frame.grid_rowconfigure(4, weight=3)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Title of the background processing section
        self.background_processing_frame_title = tk.Label(self.background_processing_frame,
                                         text="Image enhancement:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12))
        self.background_processing_frame_title.grid(row=0, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        #######################################################################
        ### Adjust denoising section
        #######################################################################
        
        def update_filter_strength_label(value):
            self.filter_strength_value_label.config(text=str(int(float(value))))
    
        self.denoise_filter_strength = tk.DoubleVar(value=10)
        
            #######################################################################
            ##### drop-down button
            #######################################################################
        
        self.test_denoising_button = tk.Button(self.background_processing_frame,
                                               text="› Adjust denoising level",
                                               command=self.toggle_denoising_controls,
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=28)
        self.test_denoising_button.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(5, 0), pady=(0, 5))
        
            #######################################################################
            ##### Filter strength label
            #######################################################################
        
        self.filter_strength_label = tk.Label(self.background_processing_frame,
                                              text="Filter strength:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.filter_strength_label.grid(row=2, column=0, sticky="w", padx=10, pady=(5, 0))
        
        # Label to display the current filter strength value
        self.filter_strength_value_label = tk.Label(self.background_processing_frame,
                                                    text=str(int(self.denoise_filter_strength.get())),
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.filter_strength_value_label.grid(row=2, column=0, sticky="e", padx=10, pady=(5, 0))
        
            #######################################################################
            ##### Denoising slider
            #######################################################################
        
        style = ttk.Style()
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=25,
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
        self.filter_strength_slider.grid(row=3, column=0, columnspan=1, sticky="ew", padx=10, pady=(0, 10))

            #######################################################################
            ##### Apply Denoising button
            #######################################################################
        
        style.configure('TButton',
                        background='#2c3e50',
                        foreground='white',
                        font=('Segoe UI', 10),
                        padding=6,
                        borderwidth=0.5,
                        relief='solid')
        
        # Style when button pressed
        style.map('TButton',
                  background=[('active', '#388E3C')],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        
        self.denoise_button = ttk.Button(self.background_processing_frame,
                                 text="Apply denoising",
                                 command=self.apply_denoising,
                                 style='TButton', width=25) 
        self.denoise_button.grid(row=4, column=0, columnspan=1, sticky="w", pady=(0, 10), padx=(10, 0))
        
        # Button to undo operation
        self.return_denoising_arrow_button = tk.Button(self.background_processing_frame,
                                      text="↻", relief='flat', bg=self.button_color,
                                     command=self.reset_denoising_clicked, width=4, height=1, font=("Segoe UI", 11, "bold"))

        self.return_denoising_arrow_button.grid(row=4, column=0, sticky="w", pady=(0, 10), padx=(210, 0))
        
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
                                               padx=10, pady=5, anchor="w", width=28)
        self.test_histogram_button.grid(row=5, column=0, columnspan=2, sticky="ew", padx=(5, 0), pady=(0, 5))
        
            #######################################################################
            ##### Min/Max 
            #######################################################################
        
        # Initialize values
        self.min_value = tk.DoubleVar(value=0)
        self.max_value = tk.DoubleVar(value=255)
        
        self.min_value_label = tk.Label(self.background_processing_frame,
                                      text="Min:",
                                      bg="#2c3e50",
                                      fg="white",
                                      font=("Segoe UI", 11))
        self.min_value_label.grid(row=6, column=0, sticky="w", padx=(5, 5), pady=(6,0))
        
        self.min_value_entry = tk.Entry(self.background_processing_frame,
                                      textvariable=self.min_value,
                                      bg="#243342",
                                      fg="white",
                                      width=5,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.min_value_entry.grid(row=6, column=0, sticky="e", padx=(0, 12), pady=(5,0))
        
        self.min_value_entry.bind("<Enter>", lambda e: self.on_hover(self.min_value_entry))
        self.min_value_entry.bind("<Leave>", lambda e: self.on_leave(self.min_value_entry))

        self.max_value_label = tk.Label(self.background_processing_frame,
                                        text="Max:",
                                        bg="#2c3e50",
                                        fg="white",
                                        font=("Segoe UI", 11))
        self.max_value_label.grid(row=7, column=0, sticky="w", padx=(5, 5), pady=(0,6))
        
        self.max_value_entry = tk.Entry(self.background_processing_frame,
                                        textvariable=self.max_value,
                                      bg="#243342",
                                      fg="white",
                                      width=5,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.max_value_entry.grid(row=7, column=0, sticky="e", padx=(0, 12), pady=(0,5))
        
        self.max_value_entry.bind("<Enter>", lambda e: self.on_hover(self.max_value_entry))
        self.max_value_entry.bind("<Leave>", lambda e: self.on_leave(self.max_value_entry))
        
            #######################################################################
            ##### Apply histogram stretching button
            #######################################################################
            
        self.histogram_stretching_button = ttk.Button(self.background_processing_frame,
                                 text="Apply histogram stretching",
                                 command=self.apply_histogram_stretching,
                                 style='TButton', width=25) 
        self.histogram_stretching_button.grid(row=8, column=0, columnspan=1, sticky="w", pady=(0, 10), padx=(10, 0))
        
        # Button to undo operation
        self.return_histogram_arrow_button = tk.Button(self.background_processing_frame,
                                      text="↻", relief='flat', bg=self.button_color,
                                     command=self.reset_histogram_clicked, width=4, height=1, font=("Segoe UI", 11, "bold"))

        self.return_histogram_arrow_button.grid(row=8, column=0, sticky="w", pady=(0, 10), padx=(210, 0))
        
        #######################################################################
        ### Adjust background illumination section
        #######################################################################
    
        self.background_window_size = tk.DoubleVar(value=1.00)
        
            #######################################################################
            ##### Drop-down button
            #######################################################################
        
        self.test_background_window_size_button = tk.Button(self.background_processing_frame,
                                               text="› Adjust background illumination",
                                               command=self.toggle_background_illumination_controls,
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=25)
        self.test_background_window_size_button.grid(row=9, column=0, columnspan=2, sticky="ew", padx=(5, 0), pady=(0, 5))
        
            #######################################################################
            ##### Window size label
            #######################################################################
        
        self.background_window_size_label = tk.Label(self.background_processing_frame,
                                              text="Window size (mm):",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.background_window_size_label.grid(row=10, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.background_window_size_value_label = tk.Label(self.background_processing_frame,
                                                    text=f"{self.background_window_size.get():.2f}",
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.background_window_size_value_label.grid(row=10, column=0, sticky="e", padx=10, pady=(5, 0))
        
            #######################################################################
            ##### Window size slider
            #######################################################################

        style = ttk.Style()
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=25,
                        sliderrelief="flat",
                        troughrelief="flat",
                        sliderthickness=12,
                        relief="flat",
                        borderwidth=0)
        style.map("TScale",
                  background=[("active", "#388E3C")],
                  sliderrelief=[("active", "flat")])
        
        self.background_window_size_slider = ttk.Scale(self.background_processing_frame,
                                                from_=0, to=5,
                                                orient="horizontal",
                                                variable=self.background_window_size,
                                                style="TScale",
                                                command=self.update_window_size_label)
        self.background_window_size_slider.grid(row=11, column=0, columnspan=1, sticky="ew", padx=10, pady=(0, 10))

            #######################################################################
            ##### Apply background illumination button
            #######################################################################
        
        style.configure('TButton',
                        background='#2c3e50',
                        foreground='white',
                        font=('Segoe UI', 10),
                        padding=3,
                        borderwidth=0.5,
                        relief='solid')
        
        style.map('TButton',
                  background=[('active', '#388E3C')],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        
        self.background_illumination_button = ttk.Button(self.background_processing_frame,
                                 text="Correct illumination",
                                 command=self.apply_background_illumination_correction,
                                 style='TButton', width=25)  
        self.background_illumination_button.grid(row=12, column=0, columnspan=1, sticky="w", pady=(0, 10), padx=(10, 0))
        
        # Button to undo operation
        self.return_illumination_arrow_button = tk.Button(self.background_processing_frame,
                                      text="↻", relief='flat', bg=self.button_color,
                                     command=self.reset_illumination_clicked, width=4, height=1, font=("Segoe UI", 11, "bold"))

        self.return_illumination_arrow_button.grid(row=12, column=0, sticky="w", pady=(0, 10), padx=(210, 0))
        
        #######################################################################
        ### Adjust reconstruction section
        #######################################################################
    
        self.SubDiff = tk.DoubleVar(value=50)
        
            #######################################################################
            ##### Drop-down button
            #######################################################################
        
        self.test_image_reconstuction_button = tk.Button(self.background_processing_frame,
                                               text="› Adjust image reconstruction",
                                               command=self.toggle_reconstruction_controls,
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=28)
        self.test_image_reconstuction_button.grid(row=13, column=0, columnspan=2, sticky="ew", padx=(5, 0), pady=(0, 5))
        
            #######################################################################
            ##### Filter strength label
            #######################################################################
        
        self.SubDiff_label = tk.Label(self.background_processing_frame,
                                              text="Difference:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.SubDiff_label.grid(row=14, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.SubDiff_value = tk.Label(self.background_processing_frame,
                                                    text=str(int(self.SubDiff.get())),
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.SubDiff_value.grid(row=14, column=0, sticky="e", padx=10, pady=(5, 0))
        
            #######################################################################
            ##### Reconstruction slider
            #######################################################################
        
        style = ttk.Style()
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=25,
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
        self.SubDiff_slider.grid(row=15, column=0, columnspan=1, sticky="ew", padx=10, pady=(0, 10))

            #######################################################################
            ##### Apply reconstruction button
            #######################################################################
        
        self.reconstruction_button = ttk.Button(self.background_processing_frame,
                                 text="Apply image reconstruction",
                                 command=self.apply_image_reconstruction,
                                 style='TButton', width=25) 
        self.reconstruction_button.grid(row=16, column=0, columnspan=1, sticky="w", pady=(0, 10), padx=(10, 0))
        
        # Button to undo operation
        self.return_reconstruction_arrow_button = tk.Button(self.background_processing_frame,
                                      text="↻", relief='flat', bg=self.button_color,
                                     command=self.reset_reconstruction_clicked, width=4, height=1, font=("Segoe UI", 11, "bold"))

        self.return_reconstruction_arrow_button.grid(row=16, column=0, sticky="w", pady=(0, 10), padx=(210, 0))
        
        #######################################################################
        ### Adjust pixel size for resampling
        #######################################################################
    
        self.new_resolution = tk.DoubleVar(value=1.00)
        
            #######################################################################
            ##### Drop-down button
            #######################################################################
        
        self.dropdown_resampling_button = tk.Button(self.background_processing_frame,
                                               text="› Resample image",
                                               command=self.toggle_resampling_controls, 
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=28)
        self.dropdown_resampling_button.grid(row=17, column=0, columnspan=2, sticky="ew", padx=(5, 0), pady=(0, 3))
        
            #######################################################################
            ##### Original pixel size label
            #######################################################################
        
        self.pixelsize_label = tk.Label(self.background_processing_frame,
                                              text="Original pixel size (µm):",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.pixelsize_label.grid(row=18, column=0, sticky="w", padx=10, pady=(3, 0))
        
        formatted_pixel_size = "{:.2f}".format(IMG.pixel_size)
        
        self.pixelsize_value = tk.Label(self.background_processing_frame,
                                                    text=formatted_pixel_size,
                                                    bg="#2c3e50",
                                                    fg="white",
                                                    font=("Segoe UI", 11, "bold"))
        self.pixelsize_value.grid(row=18, column=0, sticky="e", padx=10, pady=(3, 0))
        
            #######################################################################
            ##### Resampling value label
            #######################################################################
        
        self.resampling_label = tk.Label(self.background_processing_frame,
                                              text="Resampling pixel size (µm):",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.resampling_label.grid(row=19, column=0, sticky="w", padx=10, pady=(0, 0))
        
        resolution_value = self.new_resolution.get()
        formatted_resolution = "{:.2f}".format(resolution_value)
        
        self.resampling_value = tk.Label(self.background_processing_frame,
                                                    text=formatted_resolution,
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.resampling_value.grid(row=19, column=0, sticky="e", padx=10, pady=(0, 0))
        
            #######################################################################
            ##### Resampling slider
            #######################################################################
        
        self.resampling_slider = ttk.Scale(self.background_processing_frame,
                                                from_=0.50, to=5.00,
                                                orient="horizontal",
                                                variable=self.new_resolution,
                                                style="TScale",
                                                command=self.update_new_resolution)         
        self.resampling_slider.grid(row=20, column=0, columnspan=1, sticky="ew", padx=10, pady=(0, 5))
        
            #######################################################################
            ##### Apply resampling button
            #######################################################################
        
        self.resampling_button = ttk.Button(self.background_processing_frame,
                                 text="Apply image resampling",
                                 command=self.apply_resampling,
                                 style='TButton', width=25)  
        self.resampling_button.grid(row=21, column=0, columnspan=1, sticky="w", pady=(0, 10), padx=(10, 0))
               
        # Button to undo operation
        self.return_arrow_button = tk.Button(self.background_processing_frame,
                                      text="↻", relief='flat', bg=self.button_color,
                                     command=self.reset_resampling_clicked, width=4, height=1, font=("Segoe UI", 11, "bold"))

        self.return_arrow_button.grid(row=21, column=0, sticky="w", pady=(0, 10), padx=(210, 0))

        #######################################################################
        # Extract particles button
        #######################################################################
        
        style.configure('TButton',
                        background='#2c3e50',
                        foreground='white',
                        font=('Segoe UI', 10),
                        padding=6,
                        borderwidth=0.5,
                        relief='solid')
        
        # Title for the background processing section
        self.extraction_frame_title = tk.Label(self.left_frame,
                                         text="Particles extraction:",
                                         bg="#2c3e50",
                                         fg="white",
                                         justify="left",
                                         font=("Segoe UI", 12))
        self.extraction_frame_title.grid(row=22, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")
        
        self.extract_particles_button = ttk.Button(self.left_frame,
                                 text="Extract particles",
                                 command=self.apply_extract_particles,
                                 style='TButton',
                                 width=28)  
        self.extract_particles_button.grid(row=23, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=(10, 0))
        
        #######################################################################
        ##### Histogram Plot
        #######################################################################
        
        # Create figure
        self.figure = Figure(figsize=(0.2, 1.5), dpi=120)
        self.ax = self.figure.add_subplot(111)
        
        # Create canvas for the figure
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.left_frame)
        self.canvas.get_tk_widget().grid(row=24, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 0))
        
        # Expand button
        self.expand_button = tk.Button(self.left_frame, text="🔍 Expand plot", command=self.show_expanded_window, bg="#3A506B", fg="white", font=("Segoe UI", 10),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w")
        self.test_background_window_size_button.grid(row=9, column=0, columnspan=1, sticky="ew", padx=(5, 0), pady=(0, 5))
        self.expand_button.grid(row=25, column=0, columnspan=2, pady=10)
        
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
        self.image_select = ttk.Combobox(self.middle_frame, values=["Original Image", "Denoised Image", "Stretched Image", "Corrected Image", "Reconstructed Image", "Resampled Image", "Binary Image", "Extracted Particles Image", "Extracted Particles Filtered on Intensity"], state="readonly")
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
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.console_text.config(yscrollcommand=self.scrollbar.set)
        
        # Define tags for different message types
        self.console_text.tag_configure('info', foreground='white', font=("Segoe UI", 10))
        self.console_text.tag_configure('error', foreground='red', font=("Segoe UI", 10))
        self.console_text.tag_configure('success', foreground='lime', font=("Segoe UI", 10))
        self.console_text.tag_configure('new', foreground='#EEB902', font=("Segoe UI", 10))
        self.console_text.tag_configure('start', foreground='#EEB902', font=("Segoe UI", 10, "bold"))
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
        
        # Configure the grid weights
        self.console_frame.grid_columnconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(1, weight=0)
        self.console_frame.grid_rowconfigure(0, weight=1)
        
        # Set the min size for the console frame
        self.console_frame.update_idletasks()
        self.console_frame.config(height=self.console_frame.winfo_reqheight())
        
        #######################################################################
        # Right frame
        #######################################################################
        
        self.right_frame = tk.Frame(self.root, bg="#2c3e50", padx=5, pady=10)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        
        #######################################################################
        ### Particles extraction frame
        #######################################################################
        
        # Create canvas
        self.extraction_canvas = tk.Canvas(self.right_frame, bg="#2c3e50", bd=0, highlightthickness=0)
        self.extraction_canvas.grid(row=1, column=0, padx=(0,10), pady=(0, 5), sticky="ns")

        # Create a frame inside the canvas
        self.extraction_frame = tk.Frame(self.extraction_canvas, bg="#2c3e50", bd=0, relief="groove")
        self.extraction_canvas.create_window((0, 0), window=self.extraction_frame, anchor="nw")

        # Ensure that the frame takes up the full space of the canvas
        self.extraction_frame.update_idletasks()  
        self.extraction_canvas.config(scrollregion=self.extraction_canvas.bbox("all"))

        # Configure row and column weights for dynamic resizing
        self.right_frame.grid_rowconfigure(1, weight=3)
        self.right_frame.grid_columnconfigure(0, weight=0)
        
        #######################################################################
        # Filtering section
        #######################################################################
        
        self.filtering_title = tk.Label(self.extraction_frame,
                                         text="Particles filtration:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12))
        self.filtering_title.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")
        
        #######################################################################
        ### Adjust intensity of extracted particles section
        #######################################################################
    
        self.MaxInt = tk.DoubleVar(value=0.50)
        
            #######################################################################
            ##### Drop-down button
            #######################################################################
        
        self.dropdown_max_intensity_button = tk.Button(self.extraction_frame,
                                               text="› Filter particles on intensity",
                                               command=self.toggle_max_intensity_controls, 
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=28)
        self.dropdown_max_intensity_button.grid(row=3, column=0, columnspan=1, sticky="ew", padx=(5, 15), pady=(0, 5))
        
            #######################################################################
            ##### Max intensity label
            #######################################################################
        
        self.MaxInt_label = tk.Label(self.extraction_frame,
                                              text="Fraction of the max intensity:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11),
                                              justify="left",
                                              wraplength=150)
        self.MaxInt_label.grid(row=4, column=0, sticky="w", padx=10, pady=(5, 0))
        
        maxint_value = self.MaxInt.get()
        formatted_maxint = "{:.2f}".format(maxint_value)
        
        self.MaxInt_value = tk.Label(self.extraction_frame,
                                                    text=formatted_maxint,
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.MaxInt_value.grid(row=4, column=0, sticky="e", padx=(10,20), pady=(5, 0))
        
            #######################################################################
            ##### Max intensity slider
            #######################################################################
            
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=25,
                        sliderrelief="flat",
                        troughrelief="flat",
                        sliderthickness=12,
                        relief="flat",
                        borderwidth=0)
        style.map("TScale",
                  background=[("active", "#388E3C")],
                  sliderrelief=[("active", "flat")])
            
        self.MaxInt_slider = ttk.Scale(self.extraction_frame,
                                                from_=0, to=1,
                                                orient="horizontal",
                                                variable=self.MaxInt,
                                                style="TScale",
                                                command=self.update_MaxInt)         
        self.MaxInt_slider.grid(row=5, column=0, columnspan=1, sticky="ew", padx=(10,20), pady=(0, 10))

            #######################################################################
            ##### Apply filter on intensity button
            #######################################################################
        
        self.filter_intensity_button = ttk.Button(self.extraction_frame,
                                 text="Apply intensity filter",
                                 command=self.apply_intensity_filter, 
                                 style='TButton')
        self.filter_intensity_button.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=(10, 20))
        
        #######################################################################
        ### Filter based on size of extracted particles section
        #######################################################################
    
        self.MinSize = tk.DoubleVar(value=20)
        
            #######################################################################
            ##### Drop-down button
            #######################################################################
        
        self.dropdown_min_size_button = tk.Button(self.extraction_frame,
                                               text="› Filter particles on size",
                                               command=self.toggle_min_size_controls, 
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=28)
        self.dropdown_min_size_button.grid(row=7, column=0, columnspan=1, sticky="ew", padx=(5, 15), pady=(0, 5))
        
            #######################################################################
            ##### Min size label
            #######################################################################
        
        self.MinSize_label = tk.Label(self.extraction_frame,
                                              text="Minimum area (pixels):",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11),
                                              wraplength=200)
        self.MinSize_label.grid(row=8, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.MinSize_entry = tk.Entry(self.extraction_frame,
                                      textvariable=self.MinSize,
                                      bg="#243342",
                                      fg="white",
                                      width=6,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.MinSize_entry.grid(row=8, column=0, sticky="e", padx=(5, 20), pady=5)
        
            #######################################################################
            ##### Apply filter on size button
            #######################################################################
        
        self.filter_size_button = ttk.Button(self.extraction_frame,
                                 text="Apply size filter",
                                 command=self.apply_size_filter, 
                                 style='TButton')
        self.filter_size_button.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=(10, 20))
        
        #######################################################################
        ### Filter on aspect ratio section
        #######################################################################
    
        self.MinAspectRatio = tk.DoubleVar(value=0.20)
        
            #######################################################################
            ##### drop-down button
            #######################################################################
        
        self.dropdown_min_aspectratio_button = tk.Button(self.extraction_frame,
                                               text="› Filter particles on aspect ratio",
                                               command=self.toggle_min_aspectratio_controls, 
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#2C3E50", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=28)
        self.dropdown_min_aspectratio_button.grid(row=10, column=0, columnspan=1, sticky="ew", padx=(5, 15), pady=(0, 5))
        
            #######################################################################
            ##### Min aspect ratio label
            #######################################################################
        
        self.MinAspectRatio_label = tk.Label(self.extraction_frame,
                                              text="Minimum aspect ratio:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11),
                                              wraplength=150)
        self.MinAspectRatio_label.grid(row=11, column=0, sticky="w", padx=10, pady=(5, 0))
        
        formatted_minaspectratio = "{:.2f}".format(self.MinAspectRatio.get())
        
        self.MinAspectRatio_value = tk.Label(self.extraction_frame,
                                                    text=formatted_minaspectratio,
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.MinAspectRatio_value.grid(row=11, column=0, sticky="e", padx=(10,20), pady=(5, 0))
        
            #######################################################################
            ##### Min aspect ratio slider
            #######################################################################
            
        self.MinAspectRatio_slider = ttk.Scale(self.extraction_frame,
                                                from_=0, to=1,
                                                orient="horizontal",
                                                variable=self.MinAspectRatio,
                                                style="TScale",
                                                command=self.update_MinAspectRatio)         
        self.MinAspectRatio_slider.grid(row=12, column=0, columnspan=1, sticky="ew", padx=(10,20), pady=(0, 10))

            #######################################################################
            ##### Apply filter on intensity button
            #######################################################################
        
        self.filter_aspectratio_button = ttk.Button(self.extraction_frame,
                                 text="Apply aspect ratio filter",
                                 command=self.apply_aspect_ratio_filter, 
                                 style='TButton')
        self.filter_aspectratio_button.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=(10, 20))
        
        #######################################################################
        # Statistics computation section
        #######################################################################
        
        self.statistics_computation_title = tk.Label(self.extraction_frame,
                                         text="Statistics computation:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12))
        self.statistics_computation_title.grid(row=14, column=0, columnspan=2, padx=5, pady=(5, 5), sticky="w")
        
        #######################################################################
        # Compute image statistics button
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
        
        self.compute_statistics_button = ttk.Button(self.extraction_frame,
                                 text="Compute image statistics",
                                 command=self.apply_image_statistics_computation,
                                 style='Extraction.TButton',width=28)  
        self.compute_statistics_button.grid(row=15, column=0, columnspan=1, sticky="ew", pady=(0, 5), padx=(8, 15))
        
        #######################################################################
        # Save CSV & vignettes buttons
        #######################################################################
        
        self.save_csv_title = tk.Label(self.extraction_frame,
                                         text="Export outputs:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12))
        self.save_csv_title.grid(row=16, column=0, columnspan=2, padx=5, pady=(5, 5), sticky="w")
        
        self.save_csv_button = ttk.Button(self.extraction_frame,
                                 text="Save statistics",
                                 command=self.save_csv_button_clicked,
                                 style='Extraction.TButton',width=28)  
        self.save_csv_button.grid(row=17, column=0, columnspan=1, sticky="ew", pady=(0, 5), padx=(8, 15))
        
        self.save_vignettes = ttk.Button(self.extraction_frame,
                                  text="Save particle vignettes",
                                  command=self.save_vignettes_button_clicked,
                                  style='Extraction.TButton',width=28) 
        self.save_vignettes.grid(row=18, column=0, columnspan=1, sticky="ew", pady=(0, 5), padx=(8, 15))
        
        #######################################################################
        ##### Canvas for particles contours
        #######################################################################
               
        self.particle_canvas = tk.Canvas(self.right_frame, width=230, height=230, bd=0, bg='#2c3e50', relief='flat', highlightthickness=0)
        self.particle_canvas.grid(row=18, column=0, sticky="nw", padx=(20,10), pady=(0, 0))
        
        #######################################################################
        # Back to Homepage button
        #######################################################################
        
        self.back_button = tk.Button(self.right_frame, text="Back to Homepage", command=self.go_home,
                                     bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                     borderwidth=1, relief="flat", width=29)
        self.back_button.grid(row=19, column=0, columnspan=1, sticky="nw", pady=(3, 10), padx=(10, 10))
        
        self.back_button.bind("<Enter>", self.on_hover_buttons)
        self.back_button.bind("<Leave>", self.on_leave_buttons)
        
    ###########################################################################
    ########################### Log message function ##########################
    ###########################################################################
        
    def log_message(self, message_type, message):
        """
        Logs a message to the console.
    
        Parameters:
            message_type: Type of message ('info', 'error', 'success', 'new').
            message: The message to be logged.
        """
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, message + "\n", message_type)
        self.console_text.config(state=tk.DISABLED)
        self.console_text.yview(tk.END)
        
    ###########################################################################
    ############## Image import, reset all and destroy functions ##############
    ###########################################################################
        
    def open_file_button_clicked(self):
        """
        Open the file explorer to allow the user to select an image to be imported. Before importing the image, it resets all variables, canvas and figures.
    
        Functions called:
            open_file (from ImportImages file)    
            reset_all (from ImportImages file)
            plot_histogram (local)
        """
        reset_all()
        self.removed_particles = []
        self.plot_histogram(which="initialise")
        self.image_canvas.delete("all")
        self.particle_canvas.delete("all")
        self.tooltip_label.place_forget() 
        open_file(self)
        self.image_canvas.bind("<Button-1>", self.start_measurement) 
        self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
        self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
        self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
                        
    def reset_button_clicked(self):
        """
        Reset all values when clicked on the rest button.
    
        Functions called:  
            reset_all (from ImportImages file)
            plot_histogram (local)
            update_pixel_size_value (local)
            update_new_resolution (local)
        """
        reset_all()
        self.image_canvas.delete("all")
        self.plot_histogram(which='initialise')
        self.update_pixel_size_value()
        self.update_new_resolution()
        
        if IMG.selected_image is None:
            self.log_message('success', "All image variables have been successfully reset")
            self.log_message('info', f"Current image name is: {IMG.image_name}")
            self.log_message('info', f"Current image date is: {IMG.date_time}")
            self.log_message('info', f"Calculated pixel size is: {IMG.pixel_size} µm")
        else: 
            self.log_message('error', "Reset didn't function")
            self.log_message('info', f"Current image name is: {IMG.image_name}")
            self.log_message('info', f"Current image date is: {IMG.date_time}")
            self.log_message('info', f"Calculated pixel size is: {IMG.pixel_size} µm")
            
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
        Destroys current single image processing page.
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
    
        The function first checks if a valid image has been selected. It then converts the image 
        to greyscale and applies a denoising filter using a specified filter strength. The result 
        is stored in IMG.img_modified. If successful, the denoised image is displayed on the canvas 
        and its histogram is plotted. 
        
        Functions called:
            rgb_to_grey (from ImageEnhancement file)
            denoise (from ImageEnhancement file)
            plot histogram (local)
        """
        try:
            filter_strength = round(self.denoise_filter_strength.get(), 0)
    
            if IMG.img_modified is not None and len(IMG.img_modified.shape) == 2:
                self.original_denoising_image = IMG.img_modified
                image = rgb_to_grey(IMG.img_modified)
            else:
                self.original_denoising_image = IMG.selected_image
                image = rgb_to_grey(IMG.selected_image)
    
            # Apply denoising
            IMG.img_modified = denoise(image, filter_strength)
    
            if IMG.img_modified is not None:
                self.log_message('success', f"Denoising with a filter strength of {int(filter_strength)} has been performed successfully")
            else:
                self.log_message('error', "Denoising process failed: Modified image is None")
                return
    
            # Update display
            if IMG.tk_denoised_image:
                self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_denoised_image, tags="denoised img")
                self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
    
            # Plot histogram
            self.plot_histogram(which='modified_histogram')
            self.last_button_clicked = 'denoising'
    
        except Exception as e:
            self.log_message('error', f"Unexpected error during denoising: {e}")
        
    def reset_denoising_clicked(self):
        """
        Undoes the denoising operation conducted.
        
        Functions called:
            plot histogram (local)
        """
        if self.last_button_clicked == 'denoising':
            
            try:
                
                if self.original_denoising_image is not None:
                    IMG.img_modified = self.original_denoising_image
                    IMG.tk_denoised_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((900, 600)))
                    self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_denoised_image, tags="resampled img")
                    self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                    self.log_message('success', "Denoising has been undone")
                    self.plot_histogram(which="modified_histogram")
                else:
                    self.log_message('error', "No denoising has been performed yet")
                    
            except Exception as e:
                self.log_message('error', f"An error occurred while resetting the denoising: {e}")
                
        else:
            self.log_message('error', "No denoising has been performed yet")
            
    ###########################################################################
    ###################### Histogram stretching functions #####################
    ###########################################################################
    
    def apply_histogram_stretching(self):
        """
        Applies histogram stretching.
        
        Functions called:
            rgb_to_grey (from ImageEnhancement file)
            histogram_stretching (from ImageEnhancement file)
            plot histogram (local)
        """
        try:
            
            if IMG.img_modified is not None and len(IMG.img_modified.shape) == 2:
                self.original_histogram_image = IMG.img_modified
                image = IMG.img_modified
            else:
                self.original_histogram_image = IMG.selected_image
                image = rgb_to_grey(IMG.selected_image)
    
            minimum = self.min_value.get()
            maximum = self.max_value.get()
    
            if image is not None and image.size > 0:
                stretched = histogram_stretching(image, minimum, maximum)
                IMG.img_modified = stretched
                self.log_message('success', f"Histogram succesfully stretched between {int(minimum)} and {int(maximum)}")
            else:
                self.log_message('error', "An error occurred: Input image is empty or None")
                
        except Exception as e:
            self.log_message('error', f"An error occurred during the histogram stretching process: {e}")
            
        if IMG.tk_stretched_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_stretched_image, tags="stretched img")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
        self.plot_histogram(which="modified_histogram")
        self.last_button_clicked = 'histogram_stretching'
        
    def reset_histogram_clicked(self):
        """
        Undoes the histogram stretching.
        
        Functions called:
            plot histogram (local)
        """
        if self.last_button_clicked == 'histogram_stretching':
            
            try:
                
                if self.original_histogram_image is not None:
                    IMG.img_modified = self.original_histogram_image
                    IMG.tk_stretched_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((900, 600)))
                    self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_stretched_image, tags="resampled img")
                    self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                    self.log_message('success', "Histogram stretching has been undone.")
                    self.plot_histogram(which="modified_histogram")
                else:
                    self.log_message('error', "No histogram stretching has been performed yet")
                    
            except Exception as e:
                self.log_message('error', f"An error occurred while resetting the histogram stretching: {e}")
                
        else:
            self.log_message('error', "No histogram stretching has been performed yet")
        
    ###########################################################################
    ##################### Illumination processing functions ###################
    ###########################################################################
    
    def update_window_size_label(self, *args):
        """
        Updates the window size label.
        """
        self.background_window_size_value_label.config(
            text=f"{self.background_window_size.get():.2f}"
        )
    
    def apply_background_illumination_correction(self):
        """
        Applies background illumination correction.
        
        Functions called:
            rgb_to_grey (from ImageEnhancement file)
            correct_background_illumination (from ImageEnhancement file)
            plot histogram (local)
        """
        self.original_illumination_image = None
        
        try:
            if IMG.img_modified is not None and len(IMG.img_modified.shape) == 2:
                self.original_illumination_image = IMG.img_modified
                image = IMG.img_modified
            else:
                self.original_illumination_image = IMG.selected_image
                image = rgb_to_grey(IMG.selected_image)
                
            blocksize = round(self.background_window_size.get(), 2)
            
            if image is not None and image.size > 0:
                correct_background_illumination(image, blocksize, IMG.pixel_size)
                self.log_message('success', f"Correction of the background illumination with a window size of {blocksize:.2f} mm has been successfully performed")  
            else:
                self.log_message('error', f"An error occurred during the correction of the background illumination. Corrected image is {IMG.img_modified}")
                
            if IMG.tk_corrected_image:
                self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_corrected_image, tags="corrected img")
                self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                
            self.plot_histogram(which="modified_histogram")
            self.last_button_clicked = 'illumination'
            
        except Exception as e:
            self.log_message('error', f"An error occurred during the background illumination correction: {e}")
            
    def reset_illumination_clicked(self):
        """
        Undoes the background illumination correction.
        
        Functions called:
            plot histogram (local)
        """
        if self.last_button_clicked == 'illumination':
            
            try:
                if self.original_illumination_image is not None:
                    IMG.img_modified = self.original_illumination_image
                    IMG.tk_corrected_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((900, 600)))
                    self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_corrected_image, tags="resampled img")
                    self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                    self.log_message('success', "Background illumination correction has been undone")
                    self.plot_histogram(which="modified_histogram")
                else:
                    self.log_message('error', "No background illumination correction has been performed yet")
            except Exception as e:
                self.log_message('error', f"An error occurred while resetting the background illumination correction: {e}")
                
        else:
            self.log_message('error', "No background illumination correction has been performed yet")
        
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
            rgb_to_grey (from ImageEnhancement file)
            image_reconstruction (from ImageEnhancement file)
            plot histogram (local)
        """
        self.original_reconstruction_image = None
        
        try:
            if IMG.img_modified is not None and len(IMG.img_modified.shape) == 2:
                self.original_reconstruction_image = IMG.img_modified.copy()
                image = IMG.img_modified
            else:
                self.original_reconstruction_image = IMG.selected_image.copy()
                image = rgb_to_grey(IMG.selected_image)
            subdiff = round(self.SubDiff.get(), 0)
            
            if image is not None and image.size > 0:
                image_reconstruction(image, subdiff)
                self.log_message('success', f"Image reconstruction with a value of {str(int(self.SubDiff.get()))} has been successfully performed")
            else:
                self.log_message('error', f"An error occurred during the image reconstruction. Reconstructed image is {IMG.img_reconstructed}")
                
            if IMG.tk_reconstructed_image:
                self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_reconstructed_image, tags="reconstructed img")
                self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                
            self.plot_histogram(which="modified_histogram")
            self.last_button_clicked = 'reconstruction'
            
        except Exception as e:
            self.log_message('error', f"An error occurred during the image reconstruction: {e}")
    
    def reset_reconstruction_clicked(self):
        """
        Undoes the image reconstruction.
        
        Functions called:
            plot histogram (local)
        """
        if self.last_button_clicked == 'reconstruction':
            
            try:
                if self.original_reconstruction_image is not None:
                    IMG.img_modified = self.original_reconstruction_image
                    IMG.tk_reconstructed_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((900, 600)))
                    self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_reconstructed_image, tags="resampled img")
                    self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                    self.log_message('success', "Image reconstruction has been undone")
                    self.plot_histogram(which="modified_histogram")
                else:
                    self.log_message('error', "No image reconstruction has been performed yet")
                    
            except Exception as e:
                self.log_message('error', f"An error occurred while resetting the image reconstruction: {e}")
                
        else:
            self.log_message('error', "No image reconstruction has been performed yet")
            
    ###########################################################################
    ######################### Resampling option ########################
    ###########################################################################
    
    def update_pixel_size_value(self, *args):
        """
        Updates the pixel size label.
        """
        self.pixelsize_value.config(text="{:.2f}".format(IMG.pixel_size))
    
    def update_new_resolution(self, *args):
        """
        Updates the desired resolution.
        """
        resolution = self.new_resolution.get()
        self.resampling_value.config(text="{:.2f}".format(resolution))
    
    def apply_resampling(self):
        """
        Applies image resampling.
        
        Functions called:
            rgb_to_grey (from ImageEnhancement file)
            image_resampling (from ImageEnhancement file)
            plot histogram (local)
        """
        self.original_resampling_image = None 
        
        try:
            if IMG.img_modified is not None and len(IMG.img_modified.shape) == 2:
                self.original_resampling_image = IMG.img_modified.copy() 
                image = IMG.img_modified
            else:
                self.original_resampling_image = IMG.selected_image.copy() 
                image = rgb_to_grey(IMG.selected_image)
                
            if image is not None and image.size > 0:
                IMG.original_pixel_size = IMG.pixel_size
                new_resolution= round(self.new_resolution.get(), 2)
                image_resampling(image, new_resolution)
                self.log_message('success', f"Resampling at {new_resolution:.2f} µm has been successfully performed")
            else:
                self.log_message('error', "An error occurred during the resampling of the image")
                
            if IMG.tk_resampled_image:
                self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_resampled_image, tags="resampled img")
                self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                
            self.plot_histogram(which="modified_histogram")
            self.last_button_clicked = 'resampling'
            
        except Exception as e:
            self.log_message('error', f"An error occurred during the image resampling: {e}")
            
    def reset_resampling_clicked(self):
        """
        Undoes the image resampling.
        
        Functions called:
            plot histogram (local)
        """
        if self.last_button_clicked == 'resampling':
            try:
                if self.original_resampling_image is not None:
                    IMG.img_modified = self.original_resampling_image
                    IMG.pixel_size = IMG.original_pixel_size
                    IMG.tk_resampled_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((900, 600)))
                    self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_resampled_image, tags="resampled img")
                    self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
                    self.log_message('success', f"Resampling has been undone. Current pixel size: {IMG.pixel_size:.2f} µm")
                    self.plot_histogram(which="modified_histogram")
                else:
                    self.log_message('error', "No resampling has been performed yet")
                    
            except Exception as e:
                self.log_message('error', f"An error occurred while resetting the resampling: {e}")
        else:
            self.log_message('error', "No resampling has been performed yet")
            
    ###########################################################################
    ########################### Extraction functions ##########################
    ###########################################################################
        
    def apply_extract_particles(self):
        """
        Extracts particles and updates the canvas with contours, centroids and binds it with actions (measurement, tooltip).
        
        Functions called:
            extract_particles (from ParticleExtraction file)
            draw_centroids_on_canvas (local)
        """
        try:
            if IMG.selected_image is None:
                self.log_message('error', f"Selected image is {IMG.selected_image}")
                
            extract_particles(self, IMG.image_name)
            
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
                self.image_canvas.bind("<Button-3>", lambda event: self.show_context_menu(event, selected_particles, x_min, x_max, y_min, y_max))
                self.image_canvas.bind("<Button-3>", self.on_right_mouse_down)  
                self.image_canvas.bind("<B3-Motion>", self.on_mouse_drag) 
                self.image_canvas.bind("<ButtonRelease-3>", self.on_mouse_up) 
                
                self.image_canvas.bind("<Button-1>", self.start_measurement) 
                self.image_canvas.bind("<B1-Motion>", self.update_measurement)  
                self.image_canvas.bind("<ButtonRelease-1>", self.end_measurement) 
                self.image_canvas.bind("<Double-1>", self.clear_previous_measurements)
                self.last_button_clicked = 'extraction'
                
        except Exception as e:
            self.log_message('error', f"An error occurred during the particles extraction: {e}")
            
    ###########################################################################
    ######################## Filter intensity functions #######################
    ###########################################################################
    
    def update_MaxInt(self, *args):
        """
        Updates the desired intensity label.
        """
        maxint = self.MaxInt.get()
        self.MaxInt_value.config(text="{:.2f}".format(maxint))
    
    def apply_intensity_filter(self):
        """
        Filters particles based on their intensity.
        
        Functions called:
            filter_particles_on_intensity (from ParticleExtraction file)
            draw_centroids_on_canvas (local)
        """
        MaxInt = round(self.MaxInt.get(), 2)
        if IMG.stats is not None:
            filter_particles_on_intensity(self, IMG.stats, MaxInt)
            self.log_message('success', f"Particles with an intensity lower than {str(self.MaxInt.get())} of the maximum intensity on the image were filtered out.")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind('<Motion>', lambda event: self.show_particle_tooltip(event))
            self.draw_centroids_on_canvas()
        else:
            self.log_message('error', "An error occurred during the particle filtration.")
        
    ###########################################################################
    ########################### Filter size functions #########################
    ###########################################################################
    
    def apply_size_filter(self):
        """
        Filters particles based on their size (in pixels).
        
        Functions called:
            filter_particles_on_size (from ParticleExtraction file)
            draw_centroids_on_canvas (local)
        """
        MinSize = self.MinSize.get()
        if IMG.stats is not None:
            filter_particles_on_size(self, IMG.stats, MinSize)
            self.log_message('success', f"Particles smaller than {str(self.MinSize.get())} were filtered out.")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind('<Motion>', lambda event: self.show_particle_tooltip(event))
            self.draw_centroids_on_canvas()
        else:
            self.log_message('error', "An error occurred during the particle filtration.")
    
    ###########################################################################
    ###################### Filter aspect ratio functions ######################
    ###########################################################################
    
    def update_MinAspectRatio(self, *args):
        """
        Updates the desired aspect ratio label.
        """
        minaspectratio = self.MinAspectRatio.get()
        self.MinAspectRatio_value.config(text="{:.2f}".format(minaspectratio))
    
    def apply_aspect_ratio_filter(self):
        """
        Filters particles based on their aspect ratio.
        
        Functions called:
            filter_particles_on_aspect_ratio (from ParticleExtraction file)
            draw_centroids_on_canvas (local)
        """
        MinAspectRatio = self.MinAspectRatio.get()
        if IMG.stats is not None:
            filter_particles_on_aspect_ratio(self, IMG.stats, MinAspectRatio)
            self.log_message('success', f"Particles with an aspect ratio lower than {str(self.MinAspectRatio.get())} were filtered out.")
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            self.image_canvas.bind('<Motion>', lambda event: self.show_particle_tooltip(event))
            self.draw_centroids_on_canvas()
        else:
            self.log_message('error', "An error occurred during the particle filtration.")
            
    ###########################################################################
    ####################### Image statistics computation ######################
    ###########################################################################
        
    def apply_image_statistics_computation(self):     
        """
        Computes image statistics.
        
        Functions called:
            compute_image_statistics (from StatisticsComputation file)
            plot_histogram (local)
        """
        if IMG.stats is not None:
            compute_image_statistics(self, IMG.stats, IMG.image_height, IMG.image_width, IMG.image_depth)
            self.plot_histogram(which="PSD")
        else:
            self.log_message('error', "There is no particle statistics available")
        
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
            self.return_denoising_arrow_button.grid_remove()
            self.denoising_controls_visible = False
        else:
            self.filter_strength_label.grid()
            self.filter_strength_value_label.grid()
            self.filter_strength_slider.grid()
            self.denoise_button.grid()
            self.return_denoising_arrow_button.grid()
            self.denoising_controls_visible = True
            
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_controls_visible = False
            self.histogram_stretching_button.grid_remove()
            self.return_histogram_arrow_button.grid_remove()
            
            self.background_window_size_label.grid_remove()
            self.background_window_size_value_label.grid_remove()
            self.background_window_size_slider.grid_remove()
            self.background_illumination_button.grid_remove()
            self.return_illumination_arrow_button.grid_remove()
            self.background_illumination_controls_visible = False
            
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.return_reconstruction_arrow_button.grid_remove()
            self.reconstruction_controls_visible = False
            
            self.pixelsize_label.grid_remove()
            self.pixelsize_value.grid_remove()
            self.resampling_label.grid_remove()
            self.resampling_value.grid_remove()
            self.resampling_slider.grid_remove()
            self.resampling_button.grid_remove()
            self.return_arrow_button.grid_remove()
            self.resampling_controls_visible = False
            
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
            self.return_histogram_arrow_button.grid_remove()
            self.histogram_controls_visible = False
        else:
            self.min_value_label.grid()
            self.max_value_label.grid()
            self.max_value_entry.grid()
            self.min_value_entry.grid() 
            self.histogram_stretching_button.grid()
            self.return_histogram_arrow_button.grid()
            self.histogram_controls_visible = True
            
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.return_denoising_arrow_button.grid_remove()
            self.denoising_controls_visible = False
            
            self.background_window_size_label.grid_remove()
            self.background_window_size_value_label.grid_remove()
            self.background_window_size_slider.grid_remove()
            self.background_illumination_button.grid_remove()
            self.return_illumination_arrow_button.grid_remove()
            self.background_illumination_controls_visible = False
            
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.return_reconstruction_arrow_button.grid_remove()
            self.reconstruction_controls_visible = False
            
            self.pixelsize_label.grid_remove()
            self.pixelsize_value.grid_remove()
            self.resampling_label.grid_remove()
            self.resampling_value.grid_remove()
            self.resampling_slider.grid_remove()
            self.resampling_button.grid_remove()
            self.return_arrow_button.grid_remove()
            self.resampling_controls_visible = False
            
    def toggle_background_illumination_controls(self):
        """
        Shows or hides background illumination correction buttons.
        """
        if self.background_illumination_controls_visible:
            self.background_window_size_label.grid_remove()
            self.background_window_size_value_label.grid_remove()
            self.background_window_size_slider.grid_remove()
            self.background_illumination_button.grid_remove()
            self.return_illumination_arrow_button.grid_remove()
            self.background_illumination_controls_visible = False
        else:
            self.background_window_size_label.grid()
            self.background_window_size_value_label.grid()
            self.background_window_size_slider.grid()
            self.background_illumination_button.grid()
            self.return_illumination_arrow_button.grid()
            self.background_illumination_controls_visible = True
            
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.return_denoising_arrow_button.grid_remove()
            self.denoising_controls_visible = False
            
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_stretching_button.grid_remove()
            self.return_histogram_arrow_button.grid_remove()
            self.histogram_controls_visible = False
            
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.return_reconstruction_arrow_button.grid_remove()
            self.reconstruction_controls_visible = False
            
            self.pixelsize_label.grid_remove()
            self.pixelsize_value.grid_remove()
            self.resampling_label.grid_remove()
            self.resampling_value.grid_remove()
            self.resampling_slider.grid_remove()
            self.resampling_button.grid_remove()
            self.return_arrow_button.grid_remove()
            self.resampling_controls_visible = False
            
    def toggle_reconstruction_controls(self):
        """
        Shows or hides image reconstruction buttons.
        """
        if self.reconstruction_controls_visible:
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.return_reconstruction_arrow_button.grid_remove()
            self.reconstruction_controls_visible = False
        else:
            self.SubDiff_label.grid()
            self.SubDiff_value.grid()
            self.SubDiff_slider.grid()
            self.reconstruction_button.grid()
            self.return_reconstruction_arrow_button.grid()
            self.reconstruction_controls_visible = True
            
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.return_denoising_arrow_button.grid_remove()
            self.denoising_controls_visible = False
            
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_stretching_button.grid_remove()
            self.return_histogram_arrow_button.grid_remove()
            self.histogram_controls_visible = False
            
            self.background_window_size_label.grid_remove()
            self.background_window_size_value_label.grid_remove()
            self.background_window_size_slider.grid_remove()
            self.background_illumination_button.grid_remove()
            self.return_illumination_arrow_button.grid_remove()
            self.background_illumination_controls_visible = False
            
            self.pixelsize_label.grid_remove()
            self.pixelsize_value.grid_remove()
            self.resampling_label.grid_remove()
            self.resampling_value.grid_remove()
            self.resampling_slider.grid_remove()
            self.resampling_button.grid_remove()
            self.return_arrow_button.grid_remove()
            self.resampling_controls_visible = False                       
            
    def toggle_resampling_controls(self):
        """
        Shows or hides resampling buttons.
        """
        if self.resampling_controls_visible:
            self.pixelsize_label.grid_remove()
            self.pixelsize_value.grid_remove()
            self.resampling_label.grid_remove()
            self.resampling_value.grid_remove()
            self.resampling_slider.grid_remove()
            self.resampling_button.grid_remove()
            self.return_arrow_button.grid_remove()
            self.resampling_controls_visible = False
        else:
            self.pixelsize_label.grid()
            self.pixelsize_value.grid()
            self.resampling_label.grid()
            self.resampling_value.grid()
            self.resampling_slider.grid()
            self.resampling_button.grid()
            self.return_arrow_button.grid()
            self.resampling_controls_visible = True
            
            self.SubDiff_label.grid_remove()
            self.SubDiff_value.grid_remove()
            self.SubDiff_slider.grid_remove()
            self.reconstruction_button.grid_remove()
            self.return_reconstruction_arrow_button.grid_remove()
            self.reconstruction_controls_visible = False
            
            self.filter_strength_label.grid_remove()
            self.filter_strength_value_label.grid_remove()
            self.filter_strength_slider.grid_remove()
            self.denoise_button.grid_remove()
            self.return_denoising_arrow_button.grid_remove()
            self.denoising_controls_visible = False
            
            self.min_value_label.grid_remove()
            self.max_value_label.grid_remove()
            self.max_value_entry.grid_remove()
            self.min_value_entry.grid_remove()
            self.histogram_stretching_button.grid_remove()
            self.return_histogram_arrow_button.grid_remove()
            self.histogram_controls_visible = False
            
            self.background_window_size_label.grid_remove()
            self.background_window_size_value_label.grid_remove()
            self.background_window_size_slider.grid_remove()
            self.background_illumination_button.grid_remove()
            self.return_illumination_arrow_button.grid_remove()
            self.background_illumination_controls_visible = False
                
    def toggle_max_intensity_controls(self):
        """
        Shows or hides intensity filtering buttons.
        """
        if self.max_intensity_controls_visible:
            self.MaxInt_label.grid_remove()
            self.MaxInt_value.grid_remove()
            self.MaxInt_slider.grid_remove()
            self.filter_intensity_button.grid_remove()
            self.max_intensity_controls_visible = False
        else:
            self.MaxInt_label.grid()
            self.MaxInt_value.grid()
            self.MaxInt_slider.grid()
            self.filter_intensity_button.grid()
            self.max_intensity_controls_visible = True
            
            self.MinSize_label.grid_remove()
            self.MinSize_entry.grid_remove()
            self.filter_size_button.grid_remove()
            self.min_size_controls_visible = False
            
            self.MinAspectRatio_label.grid_remove()
            self.MinAspectRatio_value.grid_remove()
            self.MinAspectRatio_slider.grid_remove()
            self.filter_aspectratio_button.grid_remove()
            self.min_aspect_ratio_controls_visible = False
            
    def toggle_min_size_controls(self):
        """
        Shows or hides size filtering buttons.
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
            
            self.MaxInt_label.grid_remove()
            self.MaxInt_value.grid_remove()
            self.MaxInt_slider.grid_remove()
            self.filter_intensity_button.grid_remove()
            self.max_intensity_controls_visible = False
            
            self.MinAspectRatio_label.grid_remove()
            self.MinAspectRatio_value.grid_remove()
            self.MinAspectRatio_slider.grid_remove()
            self.filter_aspectratio_button.grid_remove()
            self.min_aspect_ratio_controls_visible = False
            
    def toggle_min_aspectratio_controls(self):
        """
        Shows or hides aspect ratio filtering buttons.
        """
        if self.min_aspect_ratio_controls_visible:
            self.MinAspectRatio_label.grid_remove()
            self.MinAspectRatio_value.grid_remove()
            self.MinAspectRatio_slider.grid_remove()
            self.filter_aspectratio_button.grid_remove()
            self.min_aspect_ratio_controls_visible = False
        else:
            self.MinAspectRatio_label.grid()
            self.MinAspectRatio_value.grid()
            self.MinAspectRatio_slider.grid()
            self.filter_aspectratio_button.grid()
            self.min_aspect_ratio_controls_visible = True
            
            self.MaxInt_label.grid_remove()
            self.MaxInt_value.grid_remove()
            self.MaxInt_slider.grid_remove()
            self.filter_intensity_button.grid_remove()
            self.max_intensity_controls_visible = False
            
            self.MinSize_label.grid_remove()
            self.MinSize_entry.grid_remove()
            self.filter_size_button.grid_remove()
            self.min_size_controls_visible = False
    
    ###########################################################################
    ########################### Plot image histogram ##########################
    ###########################################################################
    
    def plot_histogram(self, which):
        """
        Computes and shows image histogram or PSD.
        """
        # Initialize figure
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
            for spine in self.ax2.spines.values():
                spine.set_visible(False)
        if hasattr(self, 'expanded_ax2') and self.expanded_ax2 is not None:
            self.expanded_ax2.cla()  
            self.expanded_ax2.set_xticks([])
            self.expanded_ax2.set_yticks([])
            self.expanded_ax2.set_xlabel('')
            self.expanded_ax2.set_ylabel('')
            for spine in self.expanded_ax2.spines.values():
                spine.set_visible(False) 
        self.ax.set_xscale('linear')  
        self.expanded_ax.set_xscale('linear')
    
        # Plot original image histogram
        if which == 'original_histogram':
            
            hist = cv2.calcHist([IMG.selected_image], [0], None, [256], [0, 256])
            bars = self.ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            expanded_bars = self.expanded_ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            
            self.ax.set_xlim([0, 255])
            self.ax.set_ylim([0, np.max(hist) * 1.1])
            self.ax.set_xlabel('Pixel intensity', color='white', fontsize=6, labelpad=2)
            self.ax.set_ylabel('Frequency', color='white', fontsize=6, labelpad=2)
            self.ax.grid(axis='both', which='both', linewidth=0.1)
            self.ax.tick_params(axis='both', labelsize=6, length=2, colors='white')
            
            self.expanded_ax.set_xlim([0, 255])
            self.expanded_ax.set_ylim([0, np.max(hist) * 1.1])
            self.expanded_ax.set_xlabel('Pixel intensity', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.set_ylabel('Frequency', color='white', fontsize=8, labelpad=2)
            self.expanded_ax.grid(axis='both', which='both', linewidth=0.1)
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
            mplcursors.cursor(expanded_bars, hover=True).connect("add", lambda sel: (sel.annotation.set_text(
                f'Intensity: {sel.index}\nFrequency: {sel.target[1]:.0f}'
            ),
            setattr(sel.annotation, 'arrowstyle', 'fancy'),
            setattr(sel.annotation, 'linewidth', 0.3),
            sel.annotation.set_fontsize(5),
            sel.annotation.set_backgroundcolor('black'),
            sel.annotation.set_color('lime')
            ))
    
        # Plot histogram of the modified image
        elif which == 'modified_histogram':
            
            if IMG.img_modified.dtype != np.uint8:
                IMG.img_modified = (IMG.img_modified * 255).astype('uint8')
                
            hist = cv2.calcHist([IMG.img_modified], [0], None, [256], [0, 256])
            bars = self.ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            expanded_bars = self.expanded_ax.bar(range(256), hist.flatten(), color='#3A506B', edgecolor='none')
            
            self.ax.set_xlim([0, 255])
            self.ax.set_ylim([0, np.max(hist) * 1.1])
            self.ax.tick_params(axis='both', labelsize=6, length=2, colors='white')
            self.ax.set_xlabel('Pixel intensity', color='white', fontsize=6, labelpad=2)
            self.ax.set_ylabel('Frequency', color='white', fontsize=6, labelpad=2)
            self.ax.grid(axis='both', which='both', linewidth=0.1)
            
            self.expanded_ax.set_xlim([0, 255])
            self.expanded_ax.set_ylim([0, np.max(hist) * 1.1])      
            self.expanded_ax.tick_params(axis='both', which='both', labelsize=6, length=2, colors='white')
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
            
        # Plot PSD    
        elif which == 'PSD':
    
            bars = self.ax.bar(IMG.volume_per_bin['Particle Size'], IMG.volume_per_bin['Total Volume'], width=np.diff(IMG.bin_edges), edgecolor='lightgrey', color='#3A506B', linewidth=0.5)
            expanded_bars = self.expanded_ax.bar(IMG.volume_per_bin['Particle Size'], IMG.volume_per_bin['Total Volume'], width=np.diff(IMG.bin_edges), edgecolor='lightgrey', color='#3A506B', linewidth=0.5)
            
            self.ax.set_xlabel('Equivalent area diameter (µm)', fontsize=6, labelpad=2, color='white')
            self.ax.set_ylabel('Total volume (µL)', fontsize=6, labelpad=2, color='white')
            self.ax.grid(axis='both', which='both', linewidth=0.1)
            self.ax.set_xscale('log')  
            
            self.expanded_ax.set_xlabel('Equivalent spherical diameter (µm)', color='white', fontsize=8, labelpad=2)        
            self.expanded_ax.set_ylabel('Total volume (µL)', fontsize=8, labelpad=2, color="white")
            self.expanded_ax.grid(axis='both', which='both', linewidth=0.1)
            self.expanded_ax.set_xscale('log')
        
            self.ax2 = self.ax.twinx()
            self.ax2.plot(IMG.bin_edges[:-1], IMG.cdf, color='lime', linewidth=0.3)
            self.ax2.scatter(IMG.bin_edges[:-1], IMG.cdf, color='lime', marker='o', s=1)
            self.ax2.set_ylabel('Cumulative percentage', color='lime', fontsize=6, labelpad=2)  # Reduce label padding
            self.ax2.set_ylim([0, 100])
            self.ax2.grid(axis='both', which='both', linewidth=0.2, linestyle='--')
        
            self.expanded_ax2 = self.expanded_ax.twinx()
            self.expanded_ax2.plot(IMG.bin_edges[:-1], IMG.cdf, color='lime', linewidth=0.3)
            self.expanded_ax2.scatter(IMG.bin_edges[:-1], IMG.cdf, color='lime', marker='o', s=1)
            self.expanded_ax2.set_ylabel('Cumulative percentage', color='lime', fontsize=8, labelpad=2)  # Reduce label padding
            self.expanded_ax2.set_ylim([0, 100])
            self.expanded_ax2.grid(axis='both', which='both', linewidth=0.2, linestyle='--')
            
            self.ax.tick_params(axis='both', labelsize=6, length=2, colors='white')
            self.ax2.tick_params(axis='both', labelsize=6, colors='white', length=2)
            
            self.expanded_ax.tick_params(axis='both', which='both', labelsize=6, length=2, colors='white')
            self.expanded_ax2.tick_params(axis='both', which='both', labelsize=6, length=2, colors='white')
        
            # Annotate with D10, D50, and D90 values
            d10_annotation = f"D10 = {IMG.D10:.0f} µm"
            d50_annotation = f"D50 = {IMG.D50:.0f} µm"
            d90_annotation = f"D90 = {IMG.D90:.0f} µm"
            N_annotation = f"N = {len(IMG.stats)}"
        
            self.expanded_ax2.annotate(d10_annotation, xy=(0.02, 0.92), xycoords='axes fraction', fontsize=5, color='lime')
            self.expanded_ax2.annotate(d50_annotation, xy=(0.02, 0.86), xycoords='axes fraction', fontsize=5, color='lime')
            self.expanded_ax2.annotate(d90_annotation, xy=(0.02, 0.80), xycoords='axes fraction', fontsize=5, color='lime')
            self.expanded_ax2.annotate(N_annotation, xy=(0.02, 0.74), xycoords='axes fraction', fontsize=5, color='white')
            
            # Add vertical line at mean diameter
            self.expanded_ax.axvline(IMG.mean_diameter, color='cyan', linewidth=0.5, label=f'Mean diameter: {IMG.mean_diameter:.2f} µm')
            
            self.expanded_ax.legend(fontsize=5, loc='lower left', frameon=False, facecolor='black', labelcolor='white')
            
            self.ax.spines['top'].set_color('white')
            self.ax.spines['right'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.spines['bottom'].set_color('white')
            
            self.expanded_ax.spines['top'].set_color('white')
            self.expanded_ax.spines['right'].set_color('white')
            self.expanded_ax.spines['left'].set_color('white')
            self.expanded_ax.spines['bottom'].set_color('white')
            
            self.ax2.spines['top'].set_color('white')
            self.ax2.spines['right'].set_color('white')
            self.ax2.spines['left'].set_color('white')
            self.ax2.spines['bottom'].set_color('white')
            
            self.expanded_ax2.spines['top'].set_color('white')
            self.expanded_ax2.spines['right'].set_color('white')
            self.expanded_ax2.spines['left'].set_color('white')
            self.expanded_ax2.spines['bottom'].set_color('white')
        
            self.figure.tight_layout(pad=1.0)
            self.expanded_figure.tight_layout(pad=1.0)
            
            mplcursors.cursor(bars, hover=True).connect("add", lambda sel: (
                sel.annotation.set_text(
                    f'Diameter: {IMG.volume_per_bin["Particle Size"][sel.index]:.2f} µm\n'
                    f'Volume: {IMG.volume_per_bin["Total Volume"][sel.index]:.4f} µL\n'
                    f'Number of particles: {IMG.volume_per_bin["Particle Count"][sel.index]}'
                ),
                setattr(sel.annotation, 'arrowstyle', 'fancy'),
                setattr(sel.annotation, 'linewidth', 0.3),
                sel.annotation.set_fontsize(5),
                sel.annotation.set_backgroundcolor('black'),
                sel.annotation.set_color('lime')
            ))
            
            mplcursors.cursor(expanded_bars, hover=True).connect("add", lambda sel: (
                sel.annotation.set_text(
                    f'Diameter: {IMG.volume_per_bin["Particle Size"][sel.index]:.2f} µm\n'
                    f'Volume: {IMG.volume_per_bin["Total Volume"][sel.index]:.4f} µL\n'
                    f'Number of particles: {IMG.volume_per_bin["Particle Count"][sel.index]}'
                ),
                setattr(sel.annotation, 'arrowstyle', 'fancy'),
                setattr(sel.annotation, 'linewidth', 0.3),
                sel.annotation.set_fontsize(5),
                sel.annotation.set_backgroundcolor('black'),
                sel.annotation.set_color('lime')
            ))
            
        # Empty figure    
        else:
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
            save_particles_csv (from ExportToCSV file)
            save_image_csv (from ExportToCSV file)
        """
        save_particles_csv(IMG.stats, IMG.image_paths, self)
        save_image_csv(IMG.stats, IMG.csv_file_path, self)
        save_single_image_PSD_figure(IMG.csv_file_path, self)
        save_single_image_spiderchart_figure(IMG.csv_file_path, self)
            
    def save_vignettes_button_clicked(self):
        """
        Exports individual vignettes when button clicked.
        
        Functions called:
            generate_vignette (from VignetteGeneration file)
        """
        generate_vignette(self, "suspended particles", IMG.stats)
        
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
    ########################## Image canvas functions #########################
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
        elif selected_image =="Corrected Image" and IMG.tk_corrected_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_corrected_image, tags="img")
        elif selected_image =="Reconstructed Image" and IMG.tk_reconstructed_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_reconstructed_image, tags="img")
        elif selected_image =="Resampled Image" and IMG.tk_resampled_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_resampled_image, tags="img")
        elif selected_image =="Binary Image" and IMG.tk_binary_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_binary_image, tags="img")
        elif selected_image == "Extracted Particles Image" and IMG.tk_extracted_particles_image:
            self.image_canvas.create_image(0,0,anchor=tk.NW, image=IMG.tk_extracted_particles_image, tags = "extracted particles img")
        elif selected_image =="Extracted Particles Filtered on Intensity" and IMG.tk_extracted_intensity_image:
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=IMG.tk_extracted_intensity_image, tags="extracted intensity img")

        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
    def show_particle_tooltip(self, event):
        """
        Shows a yellow popup when the mouse goes over detected contours (within a radius of 10) and updates the particle canvas with the corresponding contours.
        """
        x, y = event.x, event.y
        tooltip_text = ""
        
        proximity_radius = 10
        matched_particle = None
        
        # Loop through IMG.stats and find a matching centroid
        for i, prop in enumerate(IMG.stats):
            centroid_x, centroid_y = prop.scaled_centroid
    
            if (centroid_x - proximity_radius <= x <= centroid_x + proximity_radius and
                centroid_y - proximity_radius <= y <= centroid_y + proximity_radius):
    
                tooltip_text = f"Particle: {i}\nArea: {prop.area_um2:.1f} µm²\nEquivalent diameter: {prop.equivalent_diameter_um:.1f} µm\nMajor axis length: {prop.major_axis_length_um:.1f} µm\nMinor axis length: {prop.minor_axis_length_um:.1f} µm\nPerimeter: {prop.perimeter_um:.1f} µm\nVolume: {prop.volume_ul:.4f} µl\nSolidity: {prop.solidity:.2f}\nAspect ratio: {prop.aspect_ratio:.2f}\nForm Factor: {prop.form_factor:.2f}\nSphericity: {prop.sphericity:.2f}\nRoundess: {prop.roundness:.2f}\nExtent: {prop.extent:.2f}\nFractal dimension 2D: {prop.fractal_dimension_2D:.2f}\nFractal dimension 3D: {prop.fractal_dimension_3D:.2f}\nOrientation: {prop.orientation:.2f} radians\nMean intensity: {prop.mean_intensity:.2f}\nKurtosis: {prop.kurtosis:.2f}\nSkewness: {prop.skewness:.2f}"
                
                # Get the mouse position relative to the canvas
                canvas_x = self.image_canvas.winfo_pointerx() - self.image_canvas.winfo_rootx()
                canvas_y = self.image_canvas.winfo_pointery() - self.image_canvas.winfo_rooty()
                
                # Get the canvas width and height
                canvas_width = self.image_canvas.winfo_width()
                canvas_height = self.image_canvas.winfo_height()
                
                # Define tooltip dimensions based on actual size
                tooltip_width = self.tooltip_label.winfo_reqwidth()
                tooltip_height = self.tooltip_label.winfo_reqheight()
                
                # Add margin to prevent tooltip from touching edges
                margin = 10
                
                # Calculate initial tooltip position near the mouse cursor
                tooltip_x = canvas_x + margin
                tooltip_y = canvas_y + margin
                
                # Adjust tooltip position if it exceeds the canvas boundaries
                if tooltip_x + tooltip_width > canvas_width:  
                    tooltip_x = canvas_x - tooltip_width - margin  
                    if tooltip_x < 0:  
                        tooltip_x = margin
                
                if tooltip_y + tooltip_height > canvas_height:
                    tooltip_y = canvas_y - tooltip_height - margin  
                    if tooltip_y < 0:  
                        tooltip_y = margin
                
                # Update tooltip position
                self.tooltip_label.place_forget()
                self.tooltip_label.config(text=tooltip_text)
                self.image_canvas.update_idletasks() 
    
                matched_particle = (prop.scaled_centroid, i, prop.contour) 
                break  
    
        if matched_particle is not None:
            centroid, index, contours = matched_particle
    
            # Clear the existing drawing on the canvas
            self.particle_canvas.delete("all")
    
            # Set the background color for the canvas
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
    
                # Calculate the center of the bounding box
                bbox_center_x = min_x + bbox_width / 2
                bbox_center_y = min_y + bbox_height / 2
    
                # Determine the canvas center
                canvas_center_x = canvas_width / 2
                canvas_center_y = canvas_height / 2
    
                # Calculate the scale factor while preserving the aspect ratio
                scale_margin = 0.9  # Scale to 90% of the canvas size
                scale_factor = min(canvas_width / bbox_width, canvas_height / bbox_height) * scale_margin
                if scale_factor <= 0:
                    self.log_message('error', "Invalid scaling factor.")
                    return
    
                # Translate to center the particle on the canvas
                translate_x = canvas_center_x - (bbox_center_x * scale_factor)
                translate_y = canvas_center_y - (bbox_center_y * scale_factor)
    
                # Separate outer contour from inner contours
                outer_contour = contours[0]  
                inner_contours = contours[1:]  
    
                # Scale and translate the outer contour
                scaled_outer_contour = [
                    (point[0] * scale_factor + translate_x, point[1] * scale_factor + translate_y)
                    for point in np.array(outer_contour).reshape(-1, 2)
                ]
    
                # Draw the outer contour 
                if len(scaled_outer_contour) > 2:
                    self.particle_canvas.create_polygon(
                        scaled_outer_contour, fill='#3A506B', outline='lime', width=2
                    )
    
                # Scale and translate the inner contours
                for inner_contour in inner_contours:
                    scaled_inner_contour = [
                        (point[0] * scale_factor + translate_x, point[1] * scale_factor + translate_y)
                        for point in np.array(inner_contour).reshape(-1, 2)
                    ]
    
                    # Draw the inner contours 
                    self.particle_canvas.create_polygon(
                        scaled_inner_contour, fill='#2c3e50', outline='lime', width=2
                    )

                # Draw the adaptive scale bar
                scale_bar_pixel_length = canvas_width / 3  
    
                # Convert the scale bar length to real-world units in µm, considering the scale factor
                scale_bar_real_length_um = scale_bar_pixel_length * IMG.pixel_size / scale_factor
    
                # Position the scale bar at the bottom-left corner of the canvas
                scale_bar_x1, scale_bar_y1 = 20, canvas_height - 20
                scale_bar_x2 = scale_bar_x1 + scale_bar_pixel_length 
    
                # Draw the scale bar (fixed pixel length)
                self.particle_canvas.create_line(
                    scale_bar_x1, scale_bar_y1, scale_bar_x2, scale_bar_y1, fill="white", width=3
                )
    
                # Add a label to the scale bar displaying the real-world units in µm
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
        Shows the centroids of all particles on the image canvas.
        """
        if not IMG.stats:
            self.log_message('error', "No particles to draw.")
            return
        
        self.image_canvas.delete("centroid", "contour")
        
        for i, prop in enumerate(IMG.stats):
            centroid_x, centroid_y = prop.scaled_centroid 
            
            # Draw a red dot on the canvas to represent the centroid
            self.image_canvas.create_oval(
                centroid_x - 1, centroid_y - 1, centroid_x + 1, centroid_y + 1,
                outline="red", fill="red", tags=("centroid", f"particle_{i}")
            )
            
            # Draw contours if available
            if hasattr(prop, 'scaled_contour') and prop.scaled_contour:
                for cnt in prop.scaled_contour:
                    if cnt is not None:
                        cnt = np.array(cnt, dtype=np.int32).tolist()
                        self.image_canvas.create_polygon(cnt, outline='lime', fill='', width=1, tags=("contour", f"particle_{i}"))
            
    def on_right_mouse_down(self, event):
        """
        Start selection rectangle creation on right-click.
        """
        if not self.dragging:
            self.start_x, self.start_y = event.x, event.y
            self.rect_id = self.image_canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y, outline="blue", width=2
            )
            self.dragging = True

    def on_mouse_drag(self, event):
        """
        Drag selection rectangle with the mouse.
        """
        if self.dragging and self.rect_id:
            self.image_canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        """
        Finalize rectangle creation or show context menu on right-click.
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
            self.log_message('info', "No particles were selected.")
    
    def show_context_menu(self, event, selected_particles, x_min, x_max, y_min, y_max):
        """
        Shows a menu when right-clicking on a particle (within radius of 10).
        
        Functions called:
            remove_particle (local)
            restore_particle (local)
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
                label="Remove selected particles",
                command=lambda: self.remove_particles([p[0] for p in selected_particles])
            )

        elif matched_particle or len(selected_particles) == 1:
            self.context_menu.add_command(
                label="Remove selected particle",
                command=lambda: self.remove_particle(matched_particle[0] if matched_particle else selected_particles[0][0])
            )

        self.context_menu.add_command(
            label="Restore deleted particle(s)",
            command=lambda: self.restore_particle()
        )
        
        self.context_menu.post(event.x_root, event.y_root)
    
    def remove_particle(self, index):
        """
        Removes a selected particle and updates the contours and centroids on the image canvas.
        
        Functions called:
            draw_centroids_on_canvas (local)
        """
        removed_particle = IMG.stats[index]
        self.removed_particles.append((index, removed_particle)) 
        del IMG.stats[index] 
        self.log_message('info', f"Successfully removed particle {index + 1}.")
        self.image_canvas.delete("centroid") 
        self.draw_centroids_on_canvas()
        
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
            
    def restore_particle(self):
        """
        Restores the last deleted particle(s) and updates the contours and centroids on the image canvas.
        
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
            self.removed_particles.clear()
        else:
            self.log_message('warning', "No particle to restore.")
        
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
                fill="#DDA0DD", outline="#DDA0DD"
            )
            self.start_circles.append(start_circle)
            
        else:
            self.clear_previous_measurements(event)
            self.start_point = (event.x, event.y)
            start_circle = self.image_canvas.create_oval(
                event.x - 3, event.y - 3, event.x + 3, event.y + 3,
                fill="#DDA0DD", outline="#DDA0DD"
            )
            self.start_circles.append(start_circle)
    
    def update_measurement(self, event):
        """
        Updates measurement line.
        """
        if self.start_point:
            self.end_point = (event.x, event.y)
    
            # Clear previous distance lines and labels 
            for line in self.distance_lines:
                self.image_canvas.delete(line)
            self.distance_lines.clear()
    
            if self.distance_label:
                self.image_canvas.delete(self.distance_label)
                self.distance_label = None
    
            # Clear previous end circles if they exist
            for circle in self.end_circles:
                self.image_canvas.delete(circle)
            self.end_circles.clear()
    
            # Draw new distance line for live feedback
            distance_line = self.image_canvas.create_line(
                self.start_point[0], self.start_point[1],
                self.end_point[0], self.end_point[1],
                fill="#DDA0DD", width=1, dash=(2, 2)  # Dashed line for temporary display
            )
            self.distance_lines.append(distance_line)
    
            # Draw end point circle
            end_circle = self.image_canvas.create_oval(
                self.end_point[0] - 3, self.end_point[1] - 3,
                self.end_point[0] + 3, self.end_point[1] + 3,
                fill="#DDA0DD", outline="#DDA0DD"
            )
            self.end_circles.append(end_circle)
    
    def end_measurement(self, event):
        """
        Ends measurement.
        """
        if IMG.img_modified is not None:
            image = IMG.img_modified
        else:
            image = IMG.selected_image
        if self.start_point and self.end_point:
            img_width = image.shape[1]  
            img_height = image.shape[0]  
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
    
            # Calculate scaling factors
            scale_x = img_width / canvas_width
            scale_y = img_height / canvas_height
    
            # Calculate pixel coordinates in the original image
            start_x = int(self.start_point[0] * scale_x)
            start_y = int(self.start_point[1] * scale_y)
            end_x = int(self.end_point[0] * scale_x)
            end_y = int(self.end_point[1] * scale_y)
    
            # Calculate distance in pixels using original coordinates
            distance_pixels = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
    
            # Draw the final distance line
            distance_line = self.image_canvas.create_line(
                self.start_point[0], self.start_point[1],
                self.end_point[0], self.end_point[1],
                fill="#DDA0DD", width=2
            )
            self.distance_lines.append(distance_line)
    
            # Draw final end point circle
            end_circle = self.image_canvas.create_oval(
                self.end_point[0] - 3, self.end_point[1] - 3,
                self.end_point[0] + 3, self.end_point[1] + 3,
                fill="#DDA0DD", outline="#DDA0DD"
            )
            self.end_circles.append(end_circle)
    
            # Calculate distance in µm
            distance_um = distance_pixels * IMG.pixel_size
            
            # Display distance label
            if self.distance_label:
                self.image_canvas.delete(self.distance_label)  
            self.distance_label = self.image_canvas.create_text(
                self.end_point[0] + 10, self.end_point[1] + 10,
                text=f"{distance_pixels:.1f} px / {distance_um:.2f} µm",
                fill="#DDA0DD", anchor="nw"
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