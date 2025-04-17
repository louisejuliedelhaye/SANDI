# -*- coding: utf-8 -*-
"""
File: functions for the image import and variables resetting 
Version: SANDI v1.0.0-beta
Created on Mon Aug 19 14:52:28 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: functions for the image import and variables resetting 
"""

###############################################################################
# Import packages
###############################################################################

import os
import sys
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk 
import PIL.ExifTags
import os
import datetime
import numpy as np
from fractions import Fraction
import pandas as pd

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

from IMG import IMG

###############################################################################
# Set width, height for image canvas resizing
###############################################################################

RESIZE_WIDTH = 900
RESIZE_HEIGHT = 600

###############################################################################
# Functions for the single SPM image processing
###############################################################################

def open_file(app_instance):
    """
    Opens a file dialog to select a JPG image, resizes the image for display,
    extracts EXIF data, and computes pixel size. Before doing so, it resets every variable.
    """
    reset_all()
    IMG.filename = filedialog.askopenfilename(
        initialdir="/",
        title="Select JPG Image",
        filetypes=(
            ("Image files", "*.jpg *.jpeg *.png *.tif *.tiff"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("TIFF files", "*.tif *.tiff"),
            ("All files", "*.*"),
        )
    )

    if IMG.filename is not None:
        
        try:
            
            IMG.image_name = os.path.splitext(os.path.basename(IMG.filename))[0]
            IMG.image_paths.append(IMG.filename)
            IMG.date_time = datetime.datetime.fromtimestamp(os.path.getmtime(IMG.filename))

            with Image.open(IMG.filename) as img:
                IMG.img_original = Image.open(IMG.filename)
                IMG.selected_image = np.array(img)
                IMG.tk_resized_image = ImageTk.PhotoImage(img.resize((RESIZE_WIDTH, RESIZE_HEIGHT)))
                IMG.exif_data = img._getexif()
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                show_technical_frame_popup(app_instance, IMG.filename)

        except FileNotFoundError:
            app_instance.log_message('error', "File not found.")
        except IOError:
            app_instance.log_message('error', "Error opening or processing the image.")
        except Exception as e:
            app_instance.log_message('error', f"An unexpected error occurred: {e}")

    return True

def show_technical_frame_popup(app_instance, filename):
    """
    Creates a temporary popup window where the user can enter the image technical details (height, width and depth in mm). The image is only imported once this popup is validated.
    """
    
    # Create a new pop-up window
    popup = tk.Toplevel(app_instance.root)  
    popup.title("Image technical details")
    popup.configure(bg="#2c3e50")
    popup.geometry("350x300")
    
    popup_frame_title = tk.Label(popup, 
                                 text="Enter technical specifications of the selected image:", 
                                 bg="#2c3e50", 
                                 fg="white", 
                                 wraplength=350, 
                                 justify="left", 
                                 font=("Segoe UI", 12))
    popup_frame_title.grid(row=0, column=0, columnspan=2, padx=(10, 0), pady=(10, 10), sticky="nw")
    
    popup_frame_description = tk.Label(popup, 
                                 text="Default values are for the PCam3 developed by Herbst Environmental Science used at F5.6.", 
                                 bg="#2c3e50", 
                                 fg="lime", 
                                 wraplength=350, 
                                 justify="left", 
                                 font=("Segoe UI", 10))
    popup_frame_description.grid(row=2, column=0, columnspan=2, padx=(10, 0), pady=(0, 10), sticky="nw")
    
    # Height 
    height_label = tk.Label(popup, 
                           text="Height of the image (mm):", 
                           bg="#2c3e50", 
                           fg="white", 
                           font=("Segoe UI", 11))
    height_label.grid(row=3, column=0, sticky="w", padx=(10, 5), pady=6)
    
    height_entry = tk.Entry(popup, 
                            textvariable=app_instance.pcam_characteristics.image_height,
                            bg="#243342", 
                            fg="white", 
                            width=6, 
                            font=("Segoe UI", 11), 
                            justify='center')
    height_entry.grid(row=3, column=1, sticky="e", padx=(5, 5), pady=5)

    # Width 
    width_label = tk.Label(popup, 
                           text="Width of the image (mm):", 
                           bg="#2c3e50", 
                           fg="white", 
                           font=("Segoe UI", 11))
    width_label.grid(row=4, column=0, sticky="w", padx=(10, 5), pady=6)
    
    width_entry = tk.Entry(popup, 
                            textvariable=app_instance.pcam_characteristics.image_width,
                            bg="#243342", 
                            fg="white", 
                            width=6, 
                            font=("Segoe UI", 11), 
                            justify='center')
    width_entry.grid(row=4, column=1, sticky="e", padx=(5, 5), pady=5)
    
    # Depth 
    depth_label = tk.Label(popup, 
                           text="Depth of field (mm):", 
                           bg="#2c3e50", 
                           fg="white", 
                           font=("Segoe UI", 11))
    depth_label.grid(row=5, column=0, sticky="w", padx=(10, 5), pady=6)
    
    depth_entry = tk.Entry(popup, 
                            textvariable=app_instance.pcam_characteristics.image_depth,
                            bg="#243342", 
                            fg="white", 
                            width=6, 
                            font=("Segoe UI", 11), 
                            justify='center')
    depth_entry.grid(row=5, column=1, sticky="e", padx=(5, 5), pady=5)
    
    # OK
    ok_button = tk.Button(popup, text="OK", 
                          command=lambda: import_image(app_instance, filename, height_entry.get(), width_entry.get(), depth_entry.get(), popup),              
                          width=10, 
                          font=("Segoe UI", 11), 
                          justify='left')
    ok_button.grid(row=6, column=0, padx=(50,5), pady=20, sticky="w")
    
    # Cancel
    cancel_button = tk.Button(popup, 
                          text="Cancel", 
                          command=popup.destroy,                              
                          width=10, 
                          font=("Segoe UI", 11), 
                          justify='right')
    cancel_button.grid(row=6, column=1, padx=(5,40), pady=20, sticky="w")
    
def import_image(app_instance, filename, height, width, depth, popup):
    """
    Once the user clicks on the "ok" button of the popup, this function extracts all metadata from the image to be imported, and reclaculates the pixel size based on the user input height.
    """
    
    try:
        IMG.image_height = float(app_instance.pcam_characteristics.image_height.get())
        IMG.image_width = float(app_instance.pcam_characteristics.image_width.get())
        IMG.image_depth = float(app_instance.pcam_characteristics.image_depth.get())
        
        if IMG.exif_data:
            IMG.exif_data = {PIL.ExifTags.TAGS.get(k, k): v for k, v in IMG.exif_data.items()}
            IMG.focal_length = IMG.exif_data.get('FocalLength', None)
            IMG.aperture = IMG.exif_data.get('FNumber', None)
            IMG.camera = IMG.exif_data.get('Model', None)
            IMG.height = IMG.exif_data.get('ExifImageHeight', None)
            IMG.width = IMG.exif_data.get('ExifImageWidth', None)
            IMG.lens = IMG.exif_data.get('LensModel', None)
            IMG.iso = IMG.exif_data.get('ISOSpeedRatings', None)
            IMG.exposure = Fraction(IMG.exif_data.get('ExposureTime', None)).limit_denominator() if IMG.exif_data.get('ExposureTime', None) else None
            IMG.pixel_size = (IMG.image_height / IMG.height) * 1000
        
        if IMG.tk_resized_image:
            app_instance.image_list = [IMG.tk_resized_image] 
            app_instance.current_image_index = 0
            app_instance.display_image(app_instance.current_image_index)
            app_instance.update_pixel_size_value()
            app_instance.update_new_resolution()
            app_instance.log_message('start', "New processing started.")
            app_instance.log_message('success', f"Image '{IMG.filename}' successfully imported")
            app_instance.log_message('info', f"Image height: {app_instance.pcam_characteristics.image_height.get()} mm, width: {app_instance.pcam_characteristics.image_width.get()} mm and depth: {app_instance.pcam_characteristics.image_depth.get()} mm")
            app_instance.log_message('info', f"Image name is: {IMG.image_name}")
            app_instance.log_message('info', f"Image date is: {IMG.date_time}")
            app_instance.log_message('info', f"Calculated pixel size is: {IMG.pixel_size} µm")
            app_instance.log_message('info', f"Image was shot using {IMG.camera} equipped with {IMG.lens}, at aperture of f/{IMG.aperture}, focal length of {IMG.focal_length} mm, exposure time of {IMG.exposure} s and ISO {IMG.iso}")
        
            if IMG.selected_image is not None:
                app_instance.plot_histogram(which='original_histogram')  
            else:
                app_instance.plot_histogram(which='initialise') 
                
            popup.destroy()
            
    except ValueError:
        print("Please enter valid numerical values for the technical details.")
        
###############################################################################
# Functions for the gravels image processing
###############################################################################      
        
def open_stones_file(app_instance, image_height):
    """
    Opens a file dialog to select a JPG image, resizes the image for display,
    extracts EXIF data, and computes pixel size.
    """
    reset_all()
    IMG.filename = filedialog.askopenfilename(
        initialdir="/",
        title="Select JPG Image",
        filetypes=(("JPEG files", "*.jpg"), ("All files", "*.*"))
    )

    if IMG.filename is not None:
        try:
            IMG.image_name = os.path.splitext(os.path.basename(IMG.filename))[0]
            IMG.image_paths.append(IMG.filename)
            IMG.date_time = datetime.datetime.fromtimestamp(os.path.getmtime(IMG.filename))

            with Image.open(IMG.filename) as img:
                IMG.img_original = Image.open(IMG.filename)
                IMG.selected_image = np.array(img)
                IMG.tk_resized_image = ImageTk.PhotoImage(img.resize((RESIZE_WIDTH, RESIZE_HEIGHT)))
                IMG.exif_data = img._getexif()

                if IMG.exif_data:
                    IMG.exif_data = {PIL.ExifTags.TAGS.get(k, k): v for k, v in IMG.exif_data.items()}
                    IMG.focal_length = IMG.exif_data.get('FocalLength', None)
                    IMG.aperture = IMG.exif_data.get('FNumber', None)
                    IMG.camera = IMG.exif_data.get('Model', None)
                    IMG.height = IMG.exif_data.get('ExifImageHeight', None)
                    IMG.width = IMG.exif_data.get('ExifImageWidth', None)
                    IMG.lens = IMG.exif_data.get('LensModel', None)
                    IMG.iso = IMG.exif_data.get('ISOSpeedRatings', None)
                    IMG.exposure = Fraction(IMG.exif_data.get('ExposureTime', None)).limit_denominator() if IMG.exif_data.get('ExposureTime', None) else None

        except FileNotFoundError:
            app_instance.log_message('error', "File not found.")
        except IOError:
            app_instance.log_message('error', "Error opening or processing the image.")
        except Exception as e:
            app_instance.log_message('error', f"An unexpected error occurred: {e}")

    return True

###############################################################################
# Functions to reset everything
###############################################################################

def reset_all():
    """
    Reset all parameters of IMG class to their default value.
    """   
    IMG.image_height= 0
    IMG.image_width = 0
    IMG.image_depth = 0
    
    IMG.filename = None
    IMG.selected_image = None
    IMG.image_name = None
    IMG.date_time = None
    IMG.tk_resized_image = None
    IMG.image_paths = []
    IMG.pixel_size = 0.0
    IMG.exif_data = None
    IMG.focal_length = None
    IMG.camera = None
    IMG.aperture = None
    IMG.height = None
    IMG.width = None
    IMG.lens = None
    IMG.iso = None
    IMG.exposure = None
    IMG.img_original = None
    IMG.tk_image = None
    IMG.img_grey = None
    IMG.img_modified = None
    IMG.img_binary = None
    IMG.particles = []
    
    IMG.tk_denoised_image = None
    IMG.tk_stretched_image = None
    IMG.tk_corrected_image = None
    IMG.img_reconstructed = None
    IMG.tk_reconstructed_image = None
    IMG.tk_binary_image = None
    IMG.extracted_particles_image = None
    IMG.tk_extracted_particles_image = None
    IMG.tk_extracted_intensity_image = None
    
    IMG.stats = []
    IMG.quality_score = None
    IMG.laplacian_score = None
    IMG.aspect_ratio_score = None
    IMG.directionality_score =None
    
    IMG.volume_per_bin = []
    IMG.bin_edges = []
    IMG.volume_concentration_per_bin = []
    IMG.total_volume_concentration = None
    IMG.mean_diameter = None
    IMG.diameter_standard_deviation = None
    IMG.mean_area = None
    IMG.mean_perimeter = None
    IMG.mean_major_axis_length = None
    IMG.mean_minor_axis_length = None
    IMG.mean_aspect_ratio = None
    IMG.mean_convexity = None
    IMG.mean_circularity = None