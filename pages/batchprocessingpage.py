# -*- coding: utf-8 -*-
"""
File: Batch SPM image processing page
Version: SANDI v1.0.0-beta
Created on Fri Feb 14 16:14:46 2025
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: layout of the batch SPM image processing page
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
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.ticker as ticker

###############################################################################
# Access everything in the directory
###############################################################################

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'functions'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'images'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'attributes'))

###############################################################################
# Import local packages
###############################################################################

from PCAM import PCam3_characteristics
from IMG import IMG
from BatchProcessing import open_multiple_files, reset_all_batch, start_batch_processing

###############################################################################
# Creation of the page layout
###############################################################################

class BatchProcessing:
        
    ###########################################################################
    # Initialize layout and variables
    ###########################################################################
    
    def __init__(self, root, on_go_home):
        self.root = root
        self.on_go_home = on_go_home
        self.setup_main_interface()
        self.plot_histogram('initialise', IMG.csv_file_path)
        self.plot_spider_chart('initialise', IMG.csv_file_path)
        
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
        
        self.file_button = tk.Button(self.left_frame, text="Select JPG images", command=self.open_multiple_files_button_clicked,
                                     bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                     borderwidth=1, relief="flat", width=30)
        self.file_button.grid(row=0, column=0, columnspan=2, pady=(6, 3), padx=(8,8), sticky="nw")
        
        self.file_button.bind("<Enter>", self.on_hover_buttons)
        self.file_button.bind("<Leave>", self.on_leave_buttons)
        
        #######################################################################
        ### Reset button
        #######################################################################
                
        self.reset_button = tk.Button(self.left_frame,
                                       text="Reset",
                                       command=self.reset_button_clicked,
                                       bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                       borderwidth=1, relief="flat", width=30)
        self.reset_button.grid(row=1, column=0, columnspan=2, sticky="nw", pady=(3, 10), padx=(8,8))
        
        self.reset_button.bind("<Enter>", self.on_hover_buttons)
        self.reset_button.bind("<Leave>", self.on_leave_buttons)
        
        #######################################################################
        ### Background processing section
        #######################################################################

        self.left_frame.grid_columnconfigure(0, weight=1)
        
        self.background_processing_frame_title = tk.Label(self.left_frame,
                                         text="Image enhancement parameters:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12, "bold"))
        self.background_processing_frame_title.grid(row=2, column=0, columnspan=1, padx=5, pady=(10, 5), sticky="w")
        
        #######################################################################
        ### Adjust denoising section
        #######################################################################
        
        def update_filter_strength_label(value):
            self.filter_strength_value_label.config(text=str(int(float(value))))
    
        self.denoise_filter_strength = tk.DoubleVar(value=10)
        
            #######################################################################
            ##### Section button
            #######################################################################
        
        self.test_denoising_button = tk.Button(self.left_frame,
                                               text="Denoising",
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#3A506B", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=30, state="disabled", disabledforeground="white")
        self.test_denoising_button.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Filter strength label
            #######################################################################
        
        self.filter_strength_label = tk.Label(self.left_frame,
                                              text="Filter strength:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.filter_strength_label.grid(row=4, column=0, sticky="nw", padx=10, pady=(5, 0))
        
        self.filter_strength_value_label = tk.Label(self.left_frame,
                                                    text=str(int(self.denoise_filter_strength.get())),
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.filter_strength_value_label.grid(row=4, column=0, sticky="ne", padx=10, pady=(5, 0))
        
            #######################################################################
            ##### Denoising slider
            #######################################################################
        
        style = ttk.Style()
        style.configure("TScale",
                        background="#1C2833",
                        troughcolor="#34495e",
                        sliderlength=30,
                        sliderrelief="flat",
                        troughrelief="flat",
                        sliderthickness=12,
                        relief="flat",
                        borderwidth=0)
        style.map("TScale",
                  background=[("active", "#388E3C")],
                  sliderrelief=[("active", "flat")])
        
        self.filter_strength_slider = ttk.Scale(self.left_frame,
                                                from_=0, to=100,
                                                orient="horizontal",
                                                variable=self.denoise_filter_strength,
                                                style="TScale",
                                                command=update_filter_strength_label)
        self.filter_strength_slider.grid(row=5, column=0, columnspan=1, sticky="nsew", padx=10, pady=(0, 10))
        
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
            ##### Section button
            #######################################################################
            
        self.test_histogram_button = tk.Button(self.left_frame,
                                               text="Histogram stretching",
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#3A506B", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=30, state="disabled", disabledforeground="white")
        self.test_histogram_button.grid(row=6, column=0, columnspan=2, sticky="ew", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Min/Max Input Fields and Labels
            #######################################################################
        
        self.min_value = tk.DoubleVar(value=0)
        self.max_value = tk.DoubleVar(value=255)
        
        self.min_value_label = tk.Label(self.left_frame,
                                      text="Min:",
                                      bg="#2c3e50",
                                      fg="white",
                                      font=("Segoe UI", 11))
        self.min_value_label.grid(row=7, column=0, sticky="nw", padx=(10, 5), pady=(6,0))
        
        self.min_value_entry = tk.Entry(self.left_frame,
                                      textvariable=self.min_value,
                                      bg="#243342",
                                      fg="white",
                                      width=6,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.min_value_entry.grid(row=7, column=0, sticky="ne", padx=(5, 10), pady=(5, 0))
        
        self.min_value_entry.bind("<Enter>", lambda e: self.on_hover(self.min_value_entry))
        self.min_value_entry.bind("<Leave>", lambda e: self.on_leave(self.min_value_entry))

        self.max_value_label = tk.Label(self.left_frame,
                                        text="Max:",
                                        bg="#2c3e50",
                                        fg="white",
                                        font=("Segoe UI", 11))
        self.max_value_label.grid(row=8, column=0, sticky="nw", padx=(10, 5), pady=6)
        
        self.max_value_entry = tk.Entry(self.left_frame,
                                        textvariable=self.max_value,
                                      bg="#243342",
                                      fg="white",
                                      width=6,
                                      font=("Segoe UI", 11),
                                      justify='center')
        self.max_value_entry.grid(row=8, column=0, sticky="ne", padx=(5, 10), pady=5)
        
        self.max_value_entry.bind("<Enter>", lambda e: self.on_hover(self.max_value_entry))
        self.max_value_entry.bind("<Leave>", lambda e: self.on_leave(self.max_value_entry))
        
        #######################################################################
        ### Background illumination section
        #######################################################################

        self.background_window_size = tk.DoubleVar(value=1.00)
        
            #######################################################################
            ##### Section button
            #######################################################################
        
        self.test_background_window_size_button = tk.Button(self.left_frame,
                                               text="Background illumination",
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#3A506B", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=30, state="disabled", disabledforeground="white")
        self.test_background_window_size_button.grid(row=9, column=0, columnspan=2, sticky="ew", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Window size label
            #######################################################################
        
        self.background_window_size_label = tk.Label(self.left_frame,
                                              text="Window size (mm):",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.background_window_size_label.grid(row=10, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.background_window_size_value_label = tk.Label(self.left_frame,
                                                    text=f"{self.background_window_size.get():.2f}",
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.background_window_size_value_label.grid(row=10, column=0, sticky="ne", padx=10, pady=(5, 0))
        
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
        
        self.background_window_size_slider = ttk.Scale(self.left_frame,
                                                from_=0, to=5,
                                                orient="horizontal",
                                                variable=self.background_window_size,
                                                style="TScale",
                                                command=self.update_window_size_label)
        self.background_window_size_slider.grid(row=11, column=0, columnspan=1, sticky="new", padx=10, pady=(0, 10))
        
        #######################################################################
        ### Reconstruction section
        #######################################################################
    
        self.SubDiff = tk.DoubleVar(value=50)
        
        def update_SubDiff(value):
            self.SubDiff_value.config(text=str(int(float(value))))   
        
            #######################################################################
            ##### drop-down button
            #######################################################################
        
        self.test_image_reconstuction_button = tk.Button(self.left_frame,
                                               text="Image reconstruction",
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#3A506B", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=30, state="disabled", disabledforeground="white")
        self.test_image_reconstuction_button.grid(row=12, column=0, columnspan=2, sticky="ew", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Filter strength label
            #######################################################################
        
        self.SubDiff_label = tk.Label(self.left_frame,
                                              text="Difference:",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.SubDiff_label.grid(row=13, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.SubDiff_value = tk.Label(self.left_frame,
                                                    text=str(int(self.SubDiff.get())),
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.SubDiff_value.grid(row=13, column=0, sticky="e", padx=10, pady=(5, 0))
        
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
        
        self.SubDiff_slider = ttk.Scale(self.left_frame,
                                                from_=0, to=255,
                                                orient="horizontal",
                                                variable=self.SubDiff,
                                                style="TScale",
                                                command=update_SubDiff)
        self.SubDiff_slider.grid(row=14, column=0, columnspan=1, sticky="ew", padx=10, pady=(0, 10))
        
        #######################################################################
        ### Resampling section
        #######################################################################
    
        self.new_resolution = tk.DoubleVar(value=1.00)
        self.keep_original_resolution = tk.BooleanVar(value=False)
        
            #######################################################################
            ##### drop-down button
            #######################################################################
        
        self.dropdown_resampling_button = tk.Button(self.left_frame,
                                               text="Image resampling",
                                               bg="#3A506B", fg="white", font=("Segoe UI", 11, "bold"),
                                               borderwidth=0, relief="flat",
                                               activebackground="#3A506B", activeforeground="white",
                                               padx=10, pady=5, anchor="w", width=30, state="disabled", disabledforeground="white")
        self.dropdown_resampling_button.grid(row=15, column=0, columnspan=2, sticky="ew", padx=(5, 5), pady=(0, 5))
        
            #######################################################################
            ##### Original pixel size label
            #######################################################################
        
        self.pixelsize_label = tk.Label(self.left_frame,
                                              text="Original pixel size (µm):",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.pixelsize_label.grid(row=16, column=0, sticky="w", padx=10, pady=(5, 0))
        
        formatted_pixel_size = "{:.2f}".format(IMG.pixel_size)
        
        self.pixelsize_value = tk.Label(self.left_frame,
                                                    text=formatted_pixel_size,
                                                    bg="#2c3e50",
                                                    fg="white",
                                                    font=("Segoe UI", 11, "bold"))
        self.pixelsize_value.grid(row=16, column=0, sticky="e", padx=10, pady=(5, 0))
        
            #######################################################################
            ##### Resampling value label
            #######################################################################
        
        self.resampling_label = tk.Label(self.left_frame,
                                              text="Resampling pixel size (µm):",
                                              bg="#2c3e50",
                                              fg="white",
                                              font=("Segoe UI", 11))
        self.resampling_label.grid(row=17, column=0, sticky="w", padx=10, pady=(5, 0))
        
        resolution_value = self.new_resolution.get()
        formatted_resolution = "{:.2f}".format(resolution_value)
        
        self.resampling_value = tk.Label(self.left_frame,
                                                    text=formatted_resolution,
                                                    bg="#2c3e50",
                                                    fg="#388E3C",
                                                    font=("Segoe UI", 11, "bold"))
        self.resampling_value.grid(row=17, column=0, sticky="e", padx=10, pady=(5, 0))
        
            #######################################################################
            ##### Resampling slider
            #######################################################################
        
        self.resampling_slider = ttk.Scale(self.left_frame,
                                                from_=0.50, to=5.00,
                                                orient="horizontal",
                                                variable=self.new_resolution,
                                                style="TScale",
                                                command=self.update_new_resolution)         
        self.resampling_slider.grid(row=18, column=0, columnspan=1, sticky="ew", padx=10, pady=(0, 0))
        
            #######################################################################
            ##### Keep original resolution
            #######################################################################
        
        self.keep_original_checkbox = tk.Checkbutton(
            self.left_frame,
            text="Keep original resolution",
            variable=self.keep_original_resolution,
            bg="#2c3e50",
            fg="white",
            font=("Segoe UI", 11),
            command = self.toggle_resampling
        )
        self.keep_original_checkbox.grid(row=19, column=0, sticky="w", padx=10, pady=(5, 10))
        
        #######################################################################
        # Middle frame
        #######################################################################
        
        self.middle_frame = tk.Frame(self.root, bg="#243342")
        self.middle_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.middle_frame.grid_rowconfigure(0, weight=0)
        self.middle_frame.grid_rowconfigure(1, weight=0)
        self.middle_frame.grid_rowconfigure(2, weight=2)
        
        #######################################################################
        ##### PSD Plot
        #######################################################################
        
        self.figure = Figure(figsize=(7.5, 3), dpi=120)
        self.ax = self.figure.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.middle_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=1, pady=(0,7), sticky="ew")

        #######################################################################
        ##### Console
        #######################################################################
                
        self.console_frame = tk.Frame(self.middle_frame, bg="#243342", bd=1, relief="flat")
        self.console_frame.grid(row=2, column=0, padx=0, pady=(0, 5), sticky="nsew")
        
        self.console_text = tk.Text(self.console_frame, bg="#243342", fg="white", wrap=tk.WORD, height=25)
        self.console_text.grid(row=0, column=0, sticky="nsew")
        self.console_text.config(state=tk.DISABLED)
        
        self.scrollbar = ttk.Scrollbar(self.console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.console_text.config(yscrollcommand=self.scrollbar.set)
        
        self.console_text.tag_configure('info', foreground='white', font=("Segoe UI", 10))
        self.console_text.tag_configure('error', foreground='red', font=("Segoe UI", 10))
        self.console_text.tag_configure('success', foreground='lime', font=("Segoe UI", 10))
        self.console_text.tag_configure('new', foreground='#EEB902', font=("Segoe UI", 10))
        self.console_text.tag_configure('start', foreground='#EEB902', font=("Segoe UI", 10, "bold"))
        self.console_text.tag_configure('complete', foreground='lime', font=("Segoe UI", 10, "bold"))
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
        
        self.right_frame = tk.Frame(self.root, bg="#2c3e50", padx=5, pady=10)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        
        #######################################################################
        # Batch processing button
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
        
        self.compute_statistics_button = ttk.Button(self.right_frame,
                                 text="Process batch",
                                 command=self.apply_batch_processing,
                                 style='Extraction.TButton', width=28) 
        self.compute_statistics_button.grid(row=1, column=0, columnspan=1, sticky="nw", pady=(6, 3), padx=(10, 15))
        
        #######################################################################
        # Back to Homepage button
        #######################################################################
        
        self.back_button = tk.Button(self.right_frame, text="Back to homepage", command=self.go_home,
                                     bg=self.button_color, fg="black", font=("Segoe UI", 12),
                                     borderwidth=1, relief="flat", width=29)
        self.back_button.grid(row=2, column=0, columnspan=1, sticky="nw", pady=(3, 10), padx=(10, 10))
        
        self.back_button.bind("<Enter>", self.on_hover_buttons)
        self.back_button.bind("<Leave>", self.on_leave_buttons)
        
        #######################################################################
        ##### Canvas for spider chart
        #######################################################################
        
        self.spider_title = tk.Label(self.right_frame,
                                         text="Mean shape indicators:",
                                         bg="#2c3e50",
                                         fg="white",
                                         wraplength=230,
                                         justify="left",
                                         font=("Segoe UI", 12))
        self.spider_title.grid(row=17, column=0, columnspan=1, padx=5, pady=(390, 5), sticky="w")
        
        self.spider_figure = Figure(figsize=(2, 2), dpi=120)
        self.spider_ax = self.spider_figure.add_subplot(111, polar=True)
               
        self.spider_canvas = FigureCanvasTkAgg(self.spider_figure, master=self.right_frame)
        self.spider_canvas.get_tk_widget().grid(row=18, column=0, sticky="nsew", padx=(0,0), pady=(0, 0))
        
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
        self.console_text.update_idletasks()
    
    ###########################################################################
    ######################### Image import functions ##########################
    ###########################################################################
        
    def open_multiple_files_button_clicked(self):
        """
        Resets all variables and import selected files.
        
        Functions called:
            reset_all_batch (BatchProcessing)
            open_multiple_files (BatchProcessing)
        """
        reset_all_batch()
        open_multiple_files(self)
            
    def reset_button_clicked(self):
        """
        Resets all variables.
        
        Functions called:
            rest_all_batch (BatchProcessing)
            update_pixel_size_value (local)
            update_new_resolution (local)
            plot_histogram (local)
            plot_spider_chart (local)
        """
        reset_all_batch()
        self.update_pixel_size_value()
        self.update_new_resolution()
        self.plot_histogram('initialise', IMG.csv_file_path)
        self.plot_spider_chart('initialise', IMG.csv_file_path)
        if not IMG.selected_image:
            self.log_message('success', "All image variables have been successfully reset")
            self.log_message('info', f"Current image name is: {IMG.image_name}")
            self.log_message('info', f"Current image date is: {IMG.date_time}")
            self.log_message('info', f"Calculated pixel size is: {IMG.pixel_sizes[1]} µm")
        else: 
            self.log_message('error', "Reset didn't function")
            self.log_message('info', f"Current image name is: {IMG.image_name}")
            self.log_message('info', f"Current image date is: {IMG.date_time}")
            self.log_message('info', f"Calculated pixel size is: {IMG.pixel_sizes[1]} µm")
        
    ###########################################################################
    ######################## Image enhancement options ########################
    ###########################################################################
    
    def update_window_size_label(self, *args):
        """
        Updates the window size label.
        """
        self.background_window_size_value_label.config(
            text=f"{self.background_window_size.get():.2f}"
        )
    
    def update_pixel_size_value(self, *args):
        """
        Updates the pixel size label.
        """
        if IMG.pixel_sizes:  
            pixel_size = IMG.pixel_sizes[0]
            self.pixelsize_value.config(text="{:.2f}".format(pixel_size))
    
    def update_new_resolution(self, *args):
        """
        Updates the desired resolution.
        """
        if self.keep_original_resolution.get():
            resolution = IMG.pixel_sizes[0]
        else:
            resolution = round(self.new_resolution.get(), 3) 
        
        self.new_resolution.set(resolution)  
        self.resampling_value.config(text="{:.2f}".format(resolution))
        
    def toggle_resampling(self):
        """
        Select or not the option to apply resampling on the image.
        """
        if self.keep_original_resolution.get():
            resolution = IMG.pixel_sizes[0]  
            self.new_resolution.set(resolution)
            self.resampling_value.config(text="{:.2f}".format(IMG.pixel_sizes[0]))
            self.resampling_slider.config(state="disabled")
            self.keep_original_checkbox.config(fg="#388E3C")
        else:
            self.resampling_slider.config(state="normal")
            self.keep_original_checkbox.config(fg="white")
        
    ###########################################################################
    ######################## Batch processing functions #######################
    ###########################################################################
        
    def apply_batch_processing(self):
        """
        Starts the batch processing.
        """        
        if IMG.image_paths:
            
            dataframe_fieldnames = [
            "Image Name", "Datetime", "D10 (µm)", "D50 (µm)", "D90 (µm)", "Mean Solidity", "Mean Form Factor", 
            "Mean Sphericity", "Mean Roundness", "Mean Extent", "Mean Aspect Ratio", "Mean Fractal Dimension 2D", "Mean Fractal Dimension 3D", "Mean Major-Axis-Length (µm)", "Mean Minor-Axis-Length (µm)",
            "Number of Particles", "Mean Area (µm²)", "Mean Perimeter (µm)", "Mean Diameter (µm)",
            "Total Volume Concentration (µl/l)"
        ] + [
            str(size) for size in [
                3.54, 5.59, 6.64, 7.84, 9.26, 10.94, 12.92, 15.25, 18.01, 21.27, 25.12, 29.66, 35.03, 41.37, 48.85, 
                57.69, 68.12, 80.44, 95.00, 112.18, 132.47, 156.44, 184.74, 218.16, 257.62, 304.23, 359.26, 424.25, 
                501.00, 591.63, 698.65, 825.04, 974.29, 1150.54, 1349.32, 1597.94, 1917.53, 2301.04, 2761.24, 3313.49, 
                3976.19, 4771.43, 5725.71, 6870.86, 8245.03, 9894.03, 11872.84, 14247.41, 17096.89
            ]
        ]

            IMG.batch_results_df = pd.DataFrame(columns=dataframe_fieldnames)
            
            filter_strength = round(self.denoise_filter_strength.get(), 0)
            background_window_size = round(self.background_window_size.get(), 2)
            subdiff = round(self.SubDiff.get(), 0)
            new_resolution = round(self.new_resolution.get(), 2)
            
            start_batch_processing(IMG.image_paths, self, filter_strength, self.min_value.get(), self.max_value.get(), background_window_size, subdiff, new_resolution, self.pcam_characteristics.image_height.get(), self.pcam_characteristics.image_width.get(), self.pcam_characteristics.image_depth.get(), self.canvas)

        else:
            self.log_message('error', "There is no particle statistics available")
            
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
    ############################### Plot functions ############################
    ###########################################################################
    
    def plot_histogram(self, which, csv_file_path):
        """
        Computes batch PSD in real time.
        """
        self.figure.patch.set_facecolor('#2c3e50')
        self.ax.set_facecolor('none')
        self.ax.clear()
        for spine in self.ax.spines.values():
            spine.set_visible(True)
        self.ax.set_xscale('linear')  

        if which == 'initialise':

            self.ax.clear()
            self.ax.text(0.5, 0.5, 'No processed image', color='#FFBC42',
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
            
            self.figure.tight_layout(pad=1.0)
            
        else:
            pass
        
        self.canvas.draw()
        
        
    def plot_spider_chart(self, which, csv_file_path):
        """
        Computes spider chart in real time.
        """
        self.spider_ax.clear()
        self.spider_ax.set_facecolor('none')
        self.spider_figure.patch.set_facecolor('#2c3e50')
        for spine in self.spider_ax.spines.values():
            spine.set_visible(False)
        self.spider_ax.set_xscale('linear')  
        self.spider_ax.spines['polar'].set_visible(True)
                
        if which =='initialise':
            self.spider_ax.clear()
            self.spider_ax.text(0.2, 0, 'No processed\nimage', color='#FFBC42',
                          fontsize=8, ha='center', va='center')
            self.spider_ax.set_xticks([])
            self.spider_ax.set_yticks([])
            self.spider_ax.set_xlabel('', color='white')  
            self.spider_ax.set_ylabel('', color='white')
            self.spider_ax.spines['polar'].set_color('#2c3e50')  
            self.spider_ax.tick_params(axis='both', colors='#2c3e50') 
            
        else:
            pass
            
        self.spider_canvas.draw()
        self.spider_canvas.draw_idle()
        
    ###########################################################################
    ########################### Escape page functions #########################
    ###########################################################################
        
    def go_home(self):
        """
        Reset all values and back to homepage.
    
        Functions called:  
            reset_all_batch (from BatchProcessing file)
            destroy (local)
            on_go_home (local)
        """
        self.destroy()
        self.on_go_home()
        reset_all_batch()

    def destroy(self):
        """
        Destroys current batch processing page.
        """
        for widget in self.root.winfo_children():
            widget.destroy()
            
        for i in range(self.root.grid_size()[0]):  # Number of columns
            self.root.grid_columnconfigure(i, weight=0, uniform='')
    
        for i in range(self.root.grid_size()[1]):  # Number of rows
            self.root.grid_rowconfigure(i, weight=0, uniform='')