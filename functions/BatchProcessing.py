# -*- coding: utf-8 -*-
"""
File: Batch processing functions
Version: SANDI v1.0.0-beta
Created on Tue Feb 18 16:00:39 2025
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: File containing the functions used for the batch processing (SPM).
"""

###############################################################################
# Import packages
###############################################################################

from tkinter import filedialog
from PIL import Image, ImageTk 
import PIL.ExifTags
import os
import sys
import datetime
import time
import csv
import numpy as np
from fractions import Fraction
import pandas as pd
import cv2
from skimage.morphology import reconstruction
from skimage import transform
import concurrent.futures
import matplotlib.ticker as ticker
import threading
import tkinter as tk
import matplotlib.pyplot as plt
import gc
import seaborn as sns
import traceback

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
from ParticleExtraction import extract_batch_particles

###############################################################################
# Functions
###############################################################################

def check_parameter_consistency(app_instance):
    """
    Checks if all extracted image parameters are consistent across images and keeps import order.
    """
    
    params_dict = {
        "Focal Length": IMG.focal_lengths,
        "Aperture": IMG.apertures,
        "Camera Model": IMG.cameras,
        "Image Height": IMG.heights,
        "Image Width": IMG.widths,
        "Lens Model": IMG.lenses,
        "ISO": IMG.isos,
        "Exposure Time": IMG.exposures,
        "Pixel Size": IMG.pixel_sizes,
    }
    
    inconsistent_params = {}  

    for param, values in params_dict.items():
        if len(set(values)) > 1: 
            inconsistent_params[param] = values 

    if inconsistent_params:
        app_instance.log_message('warning', "WARNING: Image parameters are inconsistent across images. Check camera and lens models used, focal length, aperture, iso, exposure and/or pixel dimensions")
        
        for param, values in inconsistent_params.items():
            details = ", ".join(f"Image {i+1}: {val}" for i, val in enumerate(values))
            app_instance.log_message('warning', f"- {param} differs: {details}")
    else:
        app_instance.log_message('info', "All selected images share identical camera and lens models, focal length, aperture, iso, exposure and pixel dimensions")

def open_multiple_files(app_instance):
    """
    Opens a file dialog to select multiple JPG images, resizes them for display,
    extracts EXIF data, and computes pixel size for each image.
    """
    reset_all_batch()
    file_paths = filedialog.askopenfilenames(
        initialdir="/",
        title="Select JPG Images",
        filetypes=(("JPEG files", "*.jpg"), ("All files", "*.*"))
    )
    filenames = file_paths

    if not file_paths:
        return False  

    # Initialize or clear lists to store multiple image attributes
    IMG.image_paths = list(file_paths)
    IMG.image_names = []
    IMG.date_times = []
    IMG.selected_images = []
    IMG.exif_data_list = []
    IMG.focal_lengths = []
    IMG.apertures = []
    IMG.cameras = []
    IMG.heights = []
    IMG.widths = []
    IMG.lenses = []
    IMG.isos = []
    IMG.exposures = []
    IMG.pixel_sizes = []
    IMG.img_grey = [None] * len(file_paths)
    IMG.img_modified = [None] * len(file_paths)
    IMG.img_original_resampled = [None] * len(file_paths)
    IMG.img_binary = [None] * len(file_paths)
    IMG.stats = [None] * len(file_paths)

    for i, file_path in enumerate(file_paths):
        try:
            image_name = os.path.splitext(os.path.basename(file_path))[0]
            IMG.image_names.append(image_name)
            IMG.date_times.append(datetime.datetime.fromtimestamp(os.path.getmtime(file_path)))

            with Image.open(file_path) as img:
                IMG.selected_images.append(np.array(img))
                exif_data = img._getexif()

                parsed_exif = {}
                if exif_data:
                    parsed_exif = {PIL.ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}
                
                IMG.exif_data_list.append(parsed_exif)
                IMG.focal_lengths.append(parsed_exif.get('FocalLength', None))
                IMG.apertures.append(parsed_exif.get('FNumber', None))
                IMG.cameras.append(parsed_exif.get('Model', None))
                IMG.heights.append(parsed_exif.get('ExifImageHeight', None))
                IMG.widths.append(parsed_exif.get('ExifImageWidth', None))
                IMG.lenses.append(parsed_exif.get('LensModel', None))
                IMG.isos.append(parsed_exif.get('ISOSpeedRatings', None))
                IMG.exposures.append(
                    Fraction(parsed_exif.get('ExposureTime', None)).limit_denominator()
                    if parsed_exif.get('ExposureTime', None) else None
                )
                
        except FileNotFoundError:
            app_instance.log_message('error', f"File not found: {file_path}")
        except IOError:
            app_instance.log_message('error', f"Error opening or processing the image: {file_path}")
        except Exception as e:
            app_instance.log_message('error', f"An unexpected error occurred with {file_path}: {e}")
    
    show_technical_frame_popup(app_instance, file_paths)
            
    return file_paths

def show_technical_frame_popup(app_instance, file_paths):
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
                          command=lambda: import_all_images(app_instance, file_paths, height_entry.get(), width_entry.get(), depth_entry.get(), popup),              
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
 
def import_all_images(app_instance, file_paths, height, width, depth, popup):
    """
    Once the user clicks on the "ok" button of the popup, this function extracts all metadata from the image to be imported, and reclaculates the pixel size based on the user input height.
    """
    try:
        IMG.image_height = float(app_instance.pcam_characteristics.image_height.get())
        IMG.image_width = float(app_instance.pcam_characteristics.image_width.get())
        IMG.image_depth = float(app_instance.pcam_characteristics.image_depth.get())

        app_instance.image_list = []  
        
        app_instance.log_message('start', "New batch processing started")
        
        num_images = len(file_paths)
        required_attrs = [
            ('image_names', IMG.image_names),
            ('date_times', IMG.date_times),
            ('cameras', IMG.cameras),
            ('lenses', IMG.lenses),
            ('apertures', IMG.apertures),
            ('focal_lengths', IMG.focal_lengths),
            ('exposures', IMG.exposures),
            ('isos', IMG.isos),
            ('height', IMG.heights),
        ]
        
        for name, attr_list in required_attrs:
            if len(attr_list) != num_images:
                app_instance.log_message('error', f"Metadata list '{name}' has {len(attr_list)} entries, expected {num_images}")
                return
            
        check_parameter_consistency(app_instance)
            
        IMG.pixel_sizes = []

        for i in range(num_images): 
            image_name = IMG.image_names[i]
            date_time = IMG.date_times[i]
            camera = IMG.cameras[i]
            lens = IMG.lenses[i]
            aperture = IMG.apertures[i]
            focal_length = IMG.focal_lengths[i]
            exposure = IMG.exposures[i]
            iso = IMG.isos[i]
            pixel_size = (IMG.image_height / IMG.heights[i]) * 1000  
            IMG.pixel_sizes.append(pixel_size)

            app_instance.log_message('new', f"Image name: {image_name}")
            app_instance.log_message('info', f"Image date: {date_time}")
            app_instance.log_message('info', f"Calculated pixel size: {pixel_size:.2f} µm")
            app_instance.log_message('info', f"Camera: {camera}, Lens: {lens}, f/{aperture}, {focal_length} mm, {exposure} s, ISO {iso}")
        app_instance.update_pixel_size_value()
        app_instance.update_new_resolution()
            
        app_instance.log_message('success', f"{len(file_paths)} images successfully imported")                   
        app_instance.log_message('info', f"Image height: {app_instance.pcam_characteristics.image_height.get()} mm, width: {app_instance.pcam_characteristics.image_width.get()} mm and depth: {app_instance.pcam_characteristics.image_depth.get()} mm")

        popup.destroy()

    except ValueError:
        print("Please enter valid numerical values for the technical details.")    


def reset_all_batch():
    """
    Reset all parameters of IMG class to their default value in batch processing.
    """   
    IMG.filename = []
    IMG.selected_image = []
    IMG.image_names = []
    IMG.date_time = []
    IMG.tk_resized_image = []
    IMG.image_paths = []
    IMG.pixel_size = 0.0
    IMG.pixel_sizes = []
    IMG.exif_data = []
    IMG.focal_length = []
    IMG.camera = []
    IMG.aperture = []
    IMG.height = []
    IMG.width = []
    IMG.lens = []
    IMG.iso = []
    IMG.exposure = []
    IMG.img_original = []
    IMG.tk_image = []
    IMG.img_grey = []
    IMG.img_modified = []
    IMG.img_binary = []
    IMG.particles = []
    IMG.img_original_resampled = []
    
    IMG.stats = []
    IMG.quality_score = []
    IMG.laplacian_score = []
    IMG.aspect_ratio_score = []
    IMG.directionality_score =[]
    
    IMG.volume_per_bin = []
    IMG.bin_edges = []
    IMG.volume_concentration_per_bin = []
    IMG.total_volume_concentration = []
    IMG.mean_diameter = []
    IMG.diameter_standard_deviation = []
    IMG.mean_area = []
    IMG.mean_perimeter = []
    IMG.mean_major_axis_length = []
    IMG.mean_minor_axis_length = []
    IMG.mean_aspect_ratio = []
    IMG.mean_convexity = []
    IMG.mean_circularity = []
    
def background_batch_processing(app_instance, file_paths, i, denoising_strength, min_histogram_value, max_histogram_value, background_illumination_window_size, image_reconstruction_value, resampling_pixel_size, corrected_image_file_path):
    """
    Enhances all the images of the batch using the input values from the user.
    """   
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')        
    app_instance.log_message('new', f"{current_time} - Initiated processing {IMG.image_names[i]}. Image {i+1}/{len(file_paths)}")
    
    #######################################################################
    ### 1. Image conversion to greyscale
    #######################################################################
        
    IMG.img_grey[i]= cv2.cvtColor(IMG.selected_images[i], cv2.COLOR_RGB2GRAY)
    
    if IMG.img_grey[i] is None:
        app_instance.log_message('error', f"An error occurred during the conversion to greyscale of {IMG.image_names[i]}. Batch processing stopped")
    else:
        app_instance.log_message('info', f"{IMG.image_names[i]} successfully converted to greyscale")
    
    ###################################################################
    ### 2. Image denoising
    ###################################################################
        
    IMG.img_modified[i] = cv2.fastNlMeansDenoising(IMG.img_grey[i], None, denoising_strength, 7, 21)
    
    if IMG.img_modified[i] is None:
        app_instance.log_message('error', f"An error occurred during the denoising of {IMG.image_names[i]}. Batch processing stopped")
    else:
        app_instance.log_message('info', f"{IMG.image_names[i]} successfully denoised")
    
    before_histogram = IMG.img_modified[i].copy()
    
    ###############################################################
    ### 3. Image histogram stretching
    ###############################################################
        
    IMG.img_modified[i] = np.uint8(((np.clip(IMG.img_modified[i], min_histogram_value, max_histogram_value)) - min_histogram_value) / (max_histogram_value - min_histogram_value) * 255)
    
    if np.array_equal(before_histogram, IMG.img_modified[i]) and max_histogram_value != 255 and min_histogram_value != 0:
        app_instance.log_message('error', f"Image remained the same after histogram stretching of {IMG.image_names[i]}. Batch processing was stopped")
        return
    else:
        app_instance.log_message('info', f"{IMG.image_names[i]} histogram successfully stretched")
    
    before_illumination = IMG.img_modified[i].copy()
    
    ###########################################################
    ### 4. Background illumination correction
    ###########################################################
    
    w = int(np.ceil((background_illumination_window_size * 1000) / IMG.pixel_sizes[i]))  
    bg = cv2.erode(IMG.img_modified[i], np.ones((w, w)))  
    bg = cv2.resize(bg, (IMG.img_modified[i].shape[1], IMG.img_modified[i].shape[0]))  
    IMG.img_modified[i] = IMG.img_modified[i] - bg  
    IMG.img_modified[i] = cv2.normalize(IMG.img_modified[i], None, 0, 255, cv2.NORM_MINMAX) 
    
    if np.array_equal(before_illumination, IMG.img_modified[i]) and background_illumination_window_size != 0:
        app_instance.log_message('error', f"Image remained the same after background illumination correction of {IMG.image_names[i]}")
    else:
        app_instance.log_message('info', f"{IMG.image_names[i]} background illumination successfully corrected")
    
    before_reconstruction = IMG.img_modified[i].copy()
    
    #######################################################
    ### 5. Image reconstruction
    #######################################################
    
    mask = IMG.img_modified[i]
    marker = np.where(IMG.img_modified[i] <= image_reconstruction_value, 0, IMG.img_modified[i] - image_reconstruction_value)
    img_reconstructed = reconstruction(marker, mask, method='dilation', footprint=np.ones((3,) * mask.ndim))
    IMG.img_modified[i] = cv2.normalize(img_reconstructed, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    if np.array_equal(before_reconstruction, IMG.img_modified[i]) and image_reconstruction_value != 0:
        app_instance.log_message('error', f"Image remained the same after image reconstruction of {IMG.image_names[i]}. Batch processing stopped")
        return
    else:
        app_instance.log_message('info', f"{IMG.image_names[i]} successfully reconstructed")
    
    before_resampling = IMG.img_modified[i].copy()
    
    ###################################################
    ### 6. Image resampling
    ###################################################
    
    initial_resolution = IMG.pixel_sizes[i]
    IMG.pixel_sizes[i] = resampling_pixel_size
    scaling_factor = initial_resolution / resampling_pixel_size
    
    # Determine the new shape after rescaling
    new_height = int(IMG.img_modified[i].shape[0] * scaling_factor)
    new_width = int(IMG.img_modified[i].shape[1] * scaling_factor)
    
    # Resize the image to the new size using cv2.resize
    IMG.img_modified[i] = cv2.resize(IMG.img_modified[i], (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    IMG.img_original_resampled[i] = cv2.resize(IMG.img_grey[i], (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
    if np.array_equal(before_resampling, IMG.img_modified[i]) and scaling_factor != 1:
        app_instance.log_message('error', f"Image remained the same after image resampling of {IMG.image_names[i]}. Batch processing stopped")
        return
    else:
        app_instance.log_message('info', f"{IMG.image_names[i]} successfully resampled")
        app_instance.log_message('success', f"Image enhancement successfully completed for {IMG.image_names[i]} ")
    
    try:
        corrected_image_file_path = os.path.join(corrected_image_file_path, f"{IMG.image_names[i]}_enhanced_image.png")
        success = cv2.imwrite(corrected_image_file_path, IMG.img_modified[i])
        if success:
            app_instance.log_message('success', f"Enhanced image {IMG.image_names[i]} successfully saved")
    except Exception as e:
        app_instance.log_message('error', f"Failed to save enhanced image {IMG.image_names[i]}: {e}")

def batch_processing_thread(file_paths, app_instance, denoising_strength, min_histogram_value, max_histogram_value,background_illumination_window_size, image_reconstruction_value, resampling_pixel_size, height, width, depth, canvas):
    """
    Defines the process for each batch: creates output dircetory based on user selection, opens a CSV to store mean statistics of each image, starts a loop over ea-very image of the batch that 1. enhances the image, extracts particles and stores statistics in the CSV files. After each image processed, it updates the graphs displayed on the batch processing page.
    
    Functions called:
        background_batch_processing (local)
        extract_batch_particles (from ParticleExtraction)
        update_plot (local)
        update_spider_plot (local)
    """   
    try:
        app_instance.log_message('info', f"Images being processed are {file_paths}")
        
        if not file_paths:
            app_instance.log_message('error', "No files selected")
            return

        try:
            main_file_path = filedialog.askdirectory(title="Select directory to save processing outputs")
            if not main_file_path:
                app_instance.log_message('error', "No directory selected. Processing aborted")
                return
        except Exception as e:
            app_instance.log_message('error', f"Error selecting output directory: {str(e)}")
            return
            
        try:
            IMG.csv_file_path = os.path.join(main_file_path, "statistics")
            csv_file_path = os.path.join(main_file_path, "statistics")
            os.makedirs(csv_file_path, exist_ok=True)
            app_instance.log_message('info', f"CSV files will be saved to {csv_file_path}")
            
            vignette_file_path = os.path.join(main_file_path, "vignettes")
            os.makedirs(vignette_file_path, exist_ok=True) 
            app_instance.log_message('info', f"Vignettes will be saved to {vignette_file_path}")
            
            corrected_image_file_path = os.path.join(main_file_path, "enhanced_images")
            os.makedirs(corrected_image_file_path, exist_ok=True) 
            app_instance.log_message('info', f"Enhanced images will be saved to {corrected_image_file_path}")
        except Exception as e:
            app_instance.log_message('error', f"Error creating directories: {str(e)}")
            return    
        
        try:
            app_instance.log_message('info', f"Image enhancement parameters:\nDenoising: {denoising_strength:.0f}\nHistogram stretching between {min_histogram_value:.0f} and {max_histogram_value:.0f}\nBackground illumination with window size of {background_illumination_window_size:.2f}\nImage reconstruction: {image_reconstruction_value:.0f}\nResampling at pixel size: {resampling_pixel_size:.2f} µm")
        except Exception as e:
            app_instance.log_message('error', f"Error logging parameters: {str(e)}")
            return
        
        try:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            start_time = time.time()
            app_instance.log_message('start', f"{current_time} - Batch processing initiated on {len(file_paths)} images")
        except Exception as e:
            app_instance.log_message('error', f"Error logging start of batch processing: {str(e)}")
            return
        
        IMG.img_modified = [None] * len(file_paths)
        
        batch_file = os.path.join(csv_file_path, "batch_statistics.csv")
        if os.path.exists(batch_file):
            os.remove(batch_file)

        try:
            with open(os.path.join(csv_file_path, "batch_statistics.csv"), mode='a', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    "Image Name", "Datetime", "D10", "D50", "D90", "Mean Solidity", "Mean Form Factor", 
                    "Mean Sphericity", "Mean Roundness", "Mean Extent", "Mean Aspect Ratio", "Mean Fractal Dimension 2D", "Mean Fractal Dimension 3D", "Mean Major-Axis-Length (um)", 
                    "Mean Minor-Axis-Length (um)", "Number of Particles", "Mean Area (um²)", "Mean Perimeter (um)", 
                    "Mean Diameter (um)", "Mean Mean Intensity", "Mean Kurtosis", "Mean Skewness", "Total Volume Concentration (ul/l)", "1.21449578", "1.60249025", "1.891035166", "2.23134399", "2.633450968", "3.107850704", "3.666961685", "4.327133347", "5.106510257", "6.025832888", 
                               "7.111107509", "8.39172807", "9.90256593", "11.68543358", "13.78971066", "16.27318162", "19.20366522", "22.66131587", "26.74179968", "31.55729789", "37.23981168", "43.94534164", 
                               "51.85865627", "61.19717694", "72.21641829", "85.2202712", "100.5661856", "118.6746248", "140.0438222", "165.261362", "195.0198203", "230.1369158", "272.6270346", "324.2098302", 
                               "385.5523982", "458.5019084", "545.2540692", "648.4201189", "771.1053416", "917.0038168", "1090.50768", "1296.839693", "1542.211142", "1834.008179", "2181.01536", "2593.678927", 
                               "3084.421738", "3668.016358", "4362.03072", "5187.357853", "6153.251669", "7282.771116", "8629.279192", "10256.59673", "12224.88304", "14609.54506", "17494.89787"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
                if csvfile.tell() == 0:
                    writer.writeheader()
    
                for i, file_path in enumerate(file_paths):
                    try:
                        background_batch_processing(app_instance, file_paths, i, denoising_strength, min_histogram_value, 
                                                    max_histogram_value, background_illumination_window_size, image_reconstruction_value, 
                                                    resampling_pixel_size, corrected_image_file_path)
                    except Exception as e:
                        app_instance.log_message('error', f"Error processing background for {file_path}: {str(e)}")
                        continue 
    
                    try:
                        image_stats_dict = extract_batch_particles(app_instance, file_paths, vignette_file_path, csv_file_path, height, width, depth, i)
                        writer.writerow(image_stats_dict)
                        IMG.batch_results_df = pd.concat([IMG.batch_results_df, pd.DataFrame([image_stats_dict])], ignore_index=True)
                    except Exception as e:
                        app_instance.log_message('error', f"Error extracting particles for {file_path}: {str(e)}. Processing stopped.")
                        app_instance.log_message('error', f"Traceback: {traceback.format_exc()}")
                        raise  
    
                    try:
                        update_plot(app_instance)
                        update_spider_plot(app_instance)
                    except Exception as e:
                        app_instance.log_message('error', f"Error updating plots: {str(e)}")
                    
                    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    app_instance.log_message('success', f"{current_time} - Processing completed for {IMG.image_names[i]}")
                        
                    IMG.img_modified[i] = None 
                    IMG.stats[i] = None
                    IMG.img_grey[i] = None 
                    IMG.img_original_resampled[i] = None 
                    IMG.img_binary[i] = None
                    del image_stats_dict
                    gc.collect() 
                
        except Exception as e:
            app_instance.log_message('error', f"Error during CSV writing: {str(e)}")
    
        folder_path = csv_file_path
        file_name = "log.txt"
        file_path = os.path.join(folder_path, file_name)
    
        try:
            full_text = app_instance.console_text.get("1.0", tk.END)
            start_index = full_text.rfind("Images being processed are")
            if start_index == -1:
                app_instance.log_message('error', "Sentence not found in logs.")
                return
            logs_to_export = full_text[start_index:]
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(logs_to_export)
            app_instance.log_message('success', f"Logs exported to {csv_file_path}")
            
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elapsed_time = (time.time() - start_time)
            
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            
            if hours > 0:
                time_str = f"{hours}h {minutes}m {seconds}s"
            if hours <= 1 and minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"
            
            app_instance.log_message('success', "Batch statistics successfully saved in batch_statistics CSV file")
            app_instance.log_message('complete', f"{current_time} - Batch processing completed for {len(file_paths)} images in {time_str}")
            
        except Exception as e:
            app_instance.log_message('error', f"Error exporting logs: {str(e)}")
    
        try:
            save_PSD_figure(IMG.csv_file_path, IMG.batch_results_df)
        except Exception as e:
            app_instance.log_message('error', f"Error saving PSD figure: {str(e)}")
    
        try:
            save_spiderchart_figure(IMG.csv_file_path, IMG.batch_results_df)
        except Exception as e:
            app_instance.log_message('error', f"Error saving spiderchart figure: {str(e)}")
    
    except Exception as e:
        app_instance.log_message('error', f"Error during batch processing: {str(e)}")

def update_plot(app_instance):
    """
    Updates the PSD graph displayed on the 'batch processing' page.
    """   

    df = IMG.batch_results_df
    
    particle_size_columns = [
"1.21449578", "1.60249025", "1.891035166", "2.23134399", "2.633450968", "3.107850704", "3.666961685", "4.327133347", "5.106510257", "6.025832888", 
           "7.111107509", "8.39172807", "9.90256593", "11.68543358", "13.78971066", "16.27318162", "19.20366522", "22.66131587", "26.74179968", "31.55729789", "37.23981168", "43.94534164", 
           "51.85865627", "61.19717694", "72.21641829", "85.2202712", "100.5661856", "118.6746248", "140.0438222", "165.261362", "195.0198203", "230.1369158", "272.6270346", "324.2098302", 
           "385.5523982", "458.5019084", "545.2540692", "648.4201189", "771.1053416", "917.0038168", "1090.50768", "1296.839693", "1542.211142", "1834.008179", "2181.01536", "2593.678927", 
           "3084.421738", "3668.016358", "4362.03072", "5187.357853", "6153.251669", "7282.771116", "8629.279192", "10256.59673", "12224.88304", "14609.54506", "17494.89787"
]

    particle_size_columns = [str(size) for size in particle_size_columns]

    summed_data = df[particle_size_columns].sum(axis=0, skipna=True).apply(pd.to_numeric, errors='coerce').fillna(0)
    total_volume = summed_data.sum()
    percentage_data = (summed_data / total_volume) * 100
    
    particle_sizes = [float(size) for size in particle_size_columns]
    
    app_instance.figure.patch.set_facecolor('#2c3e50')
    app_instance.ax.set_facecolor('none')
    app_instance.ax.clear()
    for spine in app_instance.ax.spines.values():
        spine.set_visible(True)
    app_instance.ax.set_xscale('linear') 
    bars = app_instance.ax.bar(particle_sizes, percentage_data.values, width=np.diff(IMG.bin_edges), edgecolor='grey', color='lightgrey', linewidth=0.5)
    
    app_instance.ax.set_xlabel('Equivalent spherical diameter (µm)', fontsize=9, labelpad=2, color='white') 
    app_instance.ax.set_ylabel('Relative volume concentration (%)', fontsize=9, labelpad=2, color='white')
    app_instance.ax.grid(axis='both', which='both', linewidth=0.1) 
    app_instance.ax.set_xlim(1,20000)
    app_instance.ax.set_xscale('log') 
    app_instance.ax.xaxis.set_major_locator(ticker.LogLocator(base=10.0, subs=np.arange(1.0, 10.0, 10.0), numticks=10))
    app_instance.ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.0f}'))
    app_instance.ax.tick_params(axis='both', which="major", labelsize=8, length=4, colors='white')
    app_instance.ax.tick_params(axis='both', which="minor", labelsize=6, length=2, colors='white')

    # Annotate with D10, D50, and D90 values
    D10 = df['D10'].mean()
    D50 = df['D50'].mean()
    D90 = df['D90'].mean()
    mean_diameter = df['Mean Diameter (um)'].mean()
    d10_annotation = f"D10 = {D10:.0f} µm"
    d50_annotation = f"D50 = {D50:.0f} µm"
    d90_annotation = f"D90 = {D90:.0f} µm"
    N_annotation = f"N = {len(df['Image Name'])} images"
    
    # Plot vertical lines at D10, D50, and D90
    app_instance.ax.axvline(D10, color='lime', linestyle=':', linewidth=1)
    app_instance.ax.axvline(D50, color='lime', linestyle='-', linewidth=1)
    app_instance.ax.axvline(D90, color='lime', linestyle=':', linewidth=1)
    app_instance.ax.axvline(mean_diameter, color='#FFBC42', linestyle='-', linewidth=1)
    
    app_instance.ax.annotate(d10_annotation, xy=(0.02, 0.92), xycoords='axes fraction', fontsize=9, color='lime')
    app_instance.ax.annotate(d50_annotation, xy=(0.02, 0.86), xycoords='axes fraction', fontsize=9, color='lime')
    app_instance.ax.annotate(d90_annotation, xy=(0.02, 0.80), xycoords='axes fraction', fontsize=9, color='lime')
    app_instance.ax.annotate(f'Mean diameter = {mean_diameter:.0f} µm', xy=(0.02, 0.74), xycoords='axes fraction', fontsize=9, color='#FFBC42')
    app_instance.ax.annotate(N_annotation, xy=(0.02, 0.68), xycoords='axes fraction', fontsize=9, color='white')
    
    app_instance.ax.spines['top'].set_color('white')
    app_instance.ax.spines['right'].set_color('white')
    app_instance.ax.spines['left'].set_color('white')
    app_instance.ax.spines['bottom'].set_color('white')

    app_instance.figure.tight_layout(pad=1.0)
    app_instance.canvas.draw()
    
def update_spider_plot(app_instance):
    """
    Updates the spider graph displayed on the 'batch processing' page.
    """  
    try:
        app_instance.spider_ax.clear()
        app_instance.spider_ax.set_facecolor('none')
        app_instance.spider_figure.patch.set_facecolor('#2c3e50')
        for spine in app_instance.spider_ax.spines.values():
            spine.set_visible(True)

        df = IMG.batch_results_df

        parameters = [
            "Mean Solidity", "Mean Form Factor", "Mean Aspect Ratio", "Mean Sphericity", "Mean Roundness", "Mean Extent"
        ]
        values = df[parameters].mean().values
        parameters_no_mean = [param.replace("Mean ", "") for param in parameters]

        num_vars = len(parameters)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

        values = np.concatenate((values, [values[0]]))
        angles = np.concatenate((angles, [angles[0]]))  

        app_instance.spider_ax.set_yticks([0, 0.25, 0.50, 0.75, 1])  
        app_instance.spider_ax.set_xticks(angles[:-1])  
        app_instance.spider_ax.set_xticklabels(parameters_no_mean)  
        app_instance.spider_ax.set_ylim(0, 1)  
        app_instance.spider_ax.margins(0.2)
        app_instance.spider_ax.spines['polar'].set_visible(True)
        app_instance.spider_ax.spines['polar'].set_edgecolor('white')   
        app_instance.spider_ax.tick_params(axis='both',colors='white', labelsize=6)
        app_instance.spider_ax.fill(angles, values, color='lime', alpha=0.4, edgecolor='grey', linewidth=2.5)
        app_instance.spider_ax.plot(angles, values, color='white', linewidth=1)
        app_instance.spider_ax.set_position([0.20, 0.20, 0.6, 0.6])

        app_instance.spider_canvas.draw()
        app_instance.spider_canvas.draw_idle()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise 

def save_PSD_figure(csv_file_path, df):
    """
    Saves the PSD graph in the 'statistics' output directory.
    """  
    csv_file_path = csv_file_path.replace("\\", "/")
    csv_path = (os.path.join(csv_file_path, "batch_statistics.csv"))
    csv_path = csv_path.replace("\\", "/")
    df = pd.read_csv(csv_path)
    
    particle_size_columns = ["1.21449578", "1.60249025", "1.891035166", "2.23134399", "2.633450968", "3.107850704", "3.666961685", "4.327133347", "5.106510257", "6.025832888", 
           "7.111107509", "8.39172807", "9.90256593", "11.68543358", "13.78971066", "16.27318162", "19.20366522", "22.66131587", "26.74179968", "31.55729789", "37.23981168", "43.94534164", 
           "51.85865627", "61.19717694", "72.21641829", "85.2202712", "100.5661856", "118.6746248", "140.0438222", "165.261362", "195.0198203", "230.1369158", "272.6270346", "324.2098302", 
           "385.5523982", "458.5019084", "545.2540692", "648.4201189", "771.1053416", "917.0038168", "1090.50768", "1296.839693", "1542.211142", "1834.008179", "2181.01536", "2593.678927", 
           "3084.421738", "3668.016358", "4362.03072", "5187.357853", "6153.251669", "7282.771116", "8629.279192", "10256.59673", "12224.88304", "14609.54506", "17494.89787"
    ]
    
    # Calculate relative volume distribution
    particle_size_data = df[particle_size_columns].sum(axis=0, skipna=True).apply(pd.to_numeric, errors='coerce').fillna(0)
    total_volume = particle_size_data.sum()
    percentage_data = (particle_size_data / total_volume) * 100
    
    particle_sizes = [float(size) for size in particle_size_columns]
    
    D10 = df['D10'].mean()
    D50 = df['D50'].mean()
    D90 = df['D90'].mean()
    mean_diameter = df['Mean Diameter (um)'].mean()
    number_of_images = len(df['Image Name'])
    
    # Calculate relative count
    all_csv_files = [f for f in os.listdir(csv_file_path) if f.endswith(".csv") and f != "batch_statistics.csv"]
    final_df_list = []
    for file in all_csv_files:
        df = pd.read_csv(os.path.join(csv_file_path, file), encoding="latin1")
        df["source_file"] = file  # Add the source file name
        final_df_list.append(df)  
    final_df = pd.concat(final_df_list, ignore_index=True)
    bin_edges = np.array([
        1, 1.475, 1.741, 2.054, 2.424, 2.861, 3.376, 3.983, 4.701, 5.547, 6.546, 7.725, 9.116, 10.757, 12.694, 14.98, 
        17.678, 20.861, 24.617, 29.05, 34.281, 40.454, 47.738, 56.335, 66.479, 78.449, 92.576, 109.246, 128.917, 152.131, 
        179.525, 211.852, 250, 297.302, 353.553, 420.448, 500, 594.604, 707.107, 840.896, 1000, 1189.207, 1414.214, 
        1681.793, 2000, 2378.414, 2828.427, 3363.586, 4000, 4756.82
    ])
    particle_sizes_all = final_df["Equivalent spherical diameter (um)"].dropna()
    hist_counts, _ = np.histogram(particle_sizes_all, bins=bin_edges)
    hist_percentage = (hist_counts / hist_counts.sum()) * 100
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Plot
    sns.set_context("paper", font_scale=1.1)
    
    fig, ax1 = plt.subplots(figsize=(7, 4), dpi=300)
    fig.patch.set_facecolor('white')
    ax1.set_facecolor('white')
    
    ax1.plot(particle_sizes, percentage_data.values,
             linestyle='-', linewidth=1,
             color='#3A506B', label='Relative volume (%)')
    ax1.fill_between(particle_sizes, percentage_data.values, color='#3A506B', alpha=0.2)
    
    ax2 = ax1.twinx()
    ax2.plot(bin_centers, hist_percentage,
             linestyle='--', linewidth=1,
             color='#E74C3C', label='Relative particle count (%)')
    
    lime = '#32CD32'
    mean_color = '#FFBC42'
    ax1.axvline(D10, color='k', linestyle='--', linewidth=0.7)
    ax1.axvline(D50, color='k', linestyle='-', linewidth=0.7)
    ax1.axvline(D90, color='k', linestyle='--', linewidth=0.7)
    ax1.axvline(mean_diameter, color=lime, linestyle='-', linewidth=0.7)
    
    annotation_text = (
        f"Mean = {mean_diameter:.0f} µm\n"
        f"D10 = {D10:.0f} µm\n"
        f"D50 = {D50:.0f} µm\n"
        f"D90 = {D90:.0f} µm\n"
        f"N = {number_of_images} images"
    )
    ax1.text(0.02, 0.98, annotation_text,
             transform=ax1.transAxes,
             fontsize=9,
             verticalalignment='top',
             horizontalalignment='left',
             color='black')
    
    ax1.set_xlabel('Equivalent spherical diameter (µm)', fontsize=10)
    ax1.set_ylabel('Relative volume concentration (%)', fontsize=10)
    ax2.set_ylabel('Relative particle count (%)', fontsize=10, color='#E74C3C')
    
    ax1.set_xscale('log')
    ax1.set_xlim(1, 20000)
    ax1.xaxis.set_major_locator(ticker.LogLocator(base=10.0))
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.0f}' if x >= 1 else ''))
    
    ax1.tick_params(axis='both', which='major', labelsize=9, length=4)
    ax1.tick_params(axis='both', which='minor', labelsize=7, length=2)
    ax2.tick_params(axis='y', labelsize=9, length=4, colors='#E74C3C')
    
    ax1.grid(which='both', linestyle=':', linewidth=0.4, color='gray')
    ax2.grid(which='both', linestyle=':', linewidth=0.2, color='gray')
    for spine in ax1.spines.values():
        spine.set_visible(True)
    for spine in ax2.spines.values():
        spine.set_visible(True)
    ax1.spines['top'].set_color('k')
    ax1.spines['right'].set_color('k')
    ax1.spines['left'].set_color('k')
    ax1.spines['bottom'].set_color('k')
    
    fig.tight_layout()
    
    jpg_path = os.path.join(csv_file_path, "particle_size_distribution.jpg")
    fig.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
def save_spiderchart_figure(csv_file_path, df):
    """
    Saves the spider graph in the 'statistics' output directory.
    """  
    csv_file_path = csv_file_path.replace("\\", "/")
    csv_path = (os.path.join(csv_file_path, "batch_statistics.csv"))
    csv_path = csv_path.replace("\\", "/")
    df = pd.read_csv(csv_path)
    
    try:
              
        fig, ax = plt.subplots(figsize=(6, 6), dpi=300, subplot_kw={'polar': True})
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        parameters = [
            "Mean Solidity", "Mean Form Factor", "Mean Aspect Ratio", "Mean Sphericity", "Mean Roundness", "Mean Extent"
        ]
        values = df[parameters].mean().values
        mean_values = df[parameters].mean().values
    
        parameters_no_mean = [
            f"{param.replace('Mean ', '')}\n{mean_value:.2f}" 
            for param, mean_value in zip(parameters, mean_values)
        ]
        
        num_vars = len(parameters)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        
        values = np.concatenate((values, [values[0]]))
        angles = np.concatenate((angles, [angles[0]])) 
        
        ax.set_ylim(0, 1)
        ax.set_yticks(np.arange(0, 1.1, 0.1))
        ax.set_yticklabels([f"{v:.1f}" for v in np.arange(0, 1.1, 0.1)])
        ax.set_xticks(angles[:-1])
        
        for angle in angles[:-1]: 
            ax.plot([angle, angle], [0, 1], linestyle="dashed", color="grey", linewidth=0.5, alpha=0.6)
    
        for tick in np.arange(0, 1.1, 0.2):
            gridline = ax.yaxis.get_gridlines()[int(tick * 10)]  
            gridline.set_linewidth(1) 
        
        ax.yaxis.grid(True, linestyle='dashed', linewidth=0.7, alpha=0.7)
        ax.tick_params(axis='y', which='major', length=6, width=1.5, labelsize=8)
    
        for label, angle in zip(ax.set_xticklabels(parameters_no_mean, fontsize=10, fontweight='bold'), angles[:-1]):
            angle_deg = np.degrees(angle)
            if 90 < angle_deg < 270:
                label.set_horizontalalignment('right')
            elif angle_deg == 90 or angle_deg == 270: 
                label.set_horizontalalignment('center')
            else:  
                label.set_horizontalalignment('left')
            label.set_y(0)
    
        ax.fill(angles, values, color='steelblue', alpha=0.3, edgecolor='steelblue', linewidth=2.5)
        ax.plot(angles, values, color='k', linewidth=1)
    
        fig.tight_layout(pad=1.0)
        
        jpg_path = os.path.join(csv_file_path, "mean_shape_indicators.jpg")
        fig.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise  
     
def start_batch_processing(file_paths, app_instance, denoising_strength, min_histogram_value, max_histogram_value,background_illumination_window_size, image_reconstruction_value, resampling_pixel_size,height, width, depth, canvas):
    """
    Function to start batch processing in a separate thread.
    """  
    processing_thread = threading.Thread(target=batch_processing_thread, args=(file_paths, app_instance, denoising_strength, min_histogram_value, max_histogram_value,background_illumination_window_size, image_reconstruction_value,resampling_pixel_size, height, width, depth, canvas))
    processing_thread.start()                        
            
        