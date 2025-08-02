# -*- coding: utf-8 -*-
"""
File: Particles extraction
Version: SANDI v1.0.0-beta
Created on Fri Apr 12 13:31:54 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: File containing the functions needed to extract the particles and gravels as well as to filter them.
"""

###############################################################################
# Import packages
###############################################################################

import concurrent.futures
import numpy as np
#import cv2
from skimage.filters import threshold_otsu
from skimage.segmentation import clear_border, watershed
from skimage.measure import label, regionprops
from skimage import morphology
from skimage.morphology import closing, square, binary_erosion, disk
from scipy.ndimage import binary_fill_holes
#import gc
#from tkinter import filedialog
import cv2
from PIL import Image, ImageTk
from scipy import ndimage as ndi
import os
import sys
#import csv
#import time
import datetime
import pandas as pd
from scipy.ndimage import binary_fill_holes
from scipy.stats import kurtosis, skew
import colorsys
from importlib import resources

###############################################################################
# Import local packages
###############################################################################

from sandi.attributes.IMG import IMG
from sandi.functions.ExportToCSV import save_batch_particles_csv
from sandi.functions.VignetteGeneration import generate_batch_vignettes

###############################################################################
# Set width, height for image canvas resizing
###############################################################################

RESIZE_WIDTH = 900
RESIZE_HEIGHT = 600

###############################################################################
# Single image processing (SPM)
###############################################################################

def extract_particles(app_instance, image_name, erosion_value, particle_hole_filling, vignette_folder_path=None):
    """
    Extracts particles from the original or modified SPM image.
    """
    if IMG.img_modified is None:    
        image = IMG.selected_image
        IMG.img_modified = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
    
    if np.max(IMG.img_modified) <= 110 or np.std(IMG.img_modified) < 1 or np.mean(IMG.img_modified) < 2:
        app_instance.log_message('error', "Error: No particle detected")
        return

    threshold_value = threshold_otsu(IMG.img_modified)
    if IMG.image_background == 'white':
        IMG.img_binary = clear_border(IMG.img_modified < threshold_value)
    else:
        IMG.img_binary = clear_border(IMG.img_modified > threshold_value)
    if erosion_value != 0:
        IMG.img_binary = binary_erosion(IMG.img_binary, footprint=disk(erosion_value))

    if particle_hole_filling:
        IMG.img_binary = binary_fill_holes(IMG.img_binary)

    # Rescale the image for display
    original_height, original_width = IMG.img_modified.shape[:2]
    scale_w = RESIZE_WIDTH / original_width
    scale_h = RESIZE_HEIGHT / original_height
    scale = min(scale_w, scale_h)
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    IMG.tk_binary_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_binary).resize((new_width, new_height)))

    CC = label(IMG.img_binary, connectivity=1)
    IMG.stats = regionprops(CC, intensity_image=IMG.img_modified)
    
    def process_particle(prop):
        prop.area_um2 = prop.area * IMG.pixel_size**2
        prop.equivalent_diameter_um = prop.equivalent_diameter * IMG.pixel_size
        prop.major_axis_length_um = prop.major_axis_length * IMG.pixel_size
        prop.minor_axis_length_um = prop.minor_axis_length * IMG.pixel_size
        prop.perimeter_um = prop.perimeter * IMG.pixel_size
        prop.volume_um3 = (4/3) * np.pi * (prop.equivalent_diameter_um / 2)**3
        prop.volume_ul = prop.volume_um3 * 1e-9
        prop.max_feret_diameter = prop.feret_diameter_max * IMG.pixel_size

        # Get mean color inside particles
        if IMG.selected_image.ndim == 3:
            coords = prop.coords
            scale_row = IMG.selected_image.shape[0] / IMG.img_modified.shape[0]
            scale_col = IMG.selected_image.shape[1] / IMG.img_modified.shape[1]
            coords_rescaled = np.zeros_like(coords, dtype=float)
            coords_rescaled[:, 0] = coords[:, 0] * scale_row
            coords_rescaled[:, 1] = coords[:, 1] * scale_col
            coords_rescaled = np.round(coords_rescaled).astype(int)
            coords_rescaled[:, 0] = np.clip(coords_rescaled[:, 0], 0, IMG.selected_image.shape[0] - 1)
            coords_rescaled[:, 1] = np.clip(coords_rescaled[:, 1], 0, IMG.selected_image.shape[1] - 1)
            pixel_values = IMG.selected_image[coords_rescaled[:, 0], coords_rescaled[:, 1], :]
            prop.mean_RGB_color = np.mean(pixel_values, axis=0)

            r, g, b = prop.mean_RGB_color
            r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
            h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
            h_deg = h * 360

            if v < 0.2:
                prop.particle_color = 'black'
            elif s < 0.25 and v > 0.8:
                prop.particle_color = 'white'
            elif (h_deg >= 0 and h_deg < 20) or (h_deg > 340 and h_deg <= 360):
                prop.particle_color = 'red'
            elif h_deg >= 20 and h_deg < 40:
                prop.particle_color = 'orange'
            elif h_deg >= 40 and h_deg < 70:
                prop.particle_color = 'yellow'
            elif h_deg >= 70 and h_deg < 160:
                prop.particle_color = 'green'
            elif h_deg >= 160 and h_deg < 270:
                prop.particle_color = 'blue'
            else:
                prop.particle_color = 'unknown'
        else:
            prop.mean_RGB_color = 'unknown'
            prop.particle_color = 'unknown'

        if prop.major_axis_length_um > 0:
            prop.aspect_ratio = prop.minor_axis_length_um / prop.major_axis_length_um
        else:
            prop.aspect_ratio = None

        if prop.perimeter > 0:
            prop.form_factor = (4 * np.pi * prop.area) / (prop.perimeter ** 2)
        else:
            prop.form_factor = None
    
        if prop.area_um2 > 0 and prop.perimeter_um > 0:
            ideal_circle_perimeter = 2 * np.sqrt(np.pi * prop.area_um2)
            prop.sphericity = ideal_circle_perimeter / prop.perimeter_um
        else:
            prop.sphericity = None
            
        if prop.area_um2 > 0 and prop.major_axis_length_um > 0:
            prop.roundness = (4 * prop.area_um2) / (np.pi * (prop.max_feret_diameter**2))
        else:
            prop.roundness = None
            
        if prop.area_um2 > 0 and prop.perimeter_um > 0:
            prop.fractal_dimension_2D = 2 * (np.log(prop.perimeter_um) / np.log(prop.area_um2))
        else:
            prop.fractal_dimension_2D = None
            
        if prop.area_um2 > 0 and prop.perimeter_um > 0:
            prop.fractal_dimension_3D = -1.63 * prop.fractal_dimension_2D + 4.6
        else:
            prop.fractal_dimension_3D = None
         
        if prop.area_um2 > 0 and prop.perimeter_um > 0:    
            intensities = prop.intensity_image[prop.image]
            if intensities.size > 0 and np.std(intensities) > 1e-8:
                prop.kurtosis = kurtosis(intensities, fisher=True, bias=False)
                prop.skewness = skew(intensities, bias=False)
            else:
                prop.kurtosis = None
                prop.skewness = None
        else:
            prop.kurtosis = None
            prop.skewness = None
            
        return prop

    # Parallel processing of particles properties
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        processed_particles = list(executor.map(process_particle, IMG.stats))
    
    # Remove particles with invalid properties
    volume_threshold = 1e-8 
    IMG.stats = [
        particle for particle in processed_particles
        if all(getattr(particle, attr) is not None for attr in ['aspect_ratio', 'form_factor', 'sphericity', 'roundness']) and
           getattr(particle, 'volume_ul') > volume_threshold
    ]
    
    if IMG.stats:
        # Detect and draw contours
        if IMG.img_binary.dtype != np.uint8:
            IMG.img_binary = (IMG.img_binary * 255).astype(np.uint8)
        contours, _ = cv2.findContours(IMG.img_binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Rescale contours and centroids
        scale_x, scale_y = new_width / IMG.img_modified.shape[1], new_height / IMG.img_modified.shape[0]
        IMG.img_modified_8bit = cv2.normalize(IMG.img_modified, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        grayscale_with_contours = cv2.cvtColor(IMG.img_modified_8bit, cv2.COLOR_GRAY2BGR)
        updated_stats = [] 
        
        for i, prop in enumerate(IMG.stats):
            centroid = prop.centroid
            prop.scaled_centroid = (centroid[1] * scale_x, centroid[0] * scale_y)
    
            contour_within_bbox = []
            bbox = prop.bbox
            for contour in contours:
                if all(bbox[0] <= pt[0][1] <= bbox[2] and bbox[1] <= pt[0][0] <= bbox[3] for pt in contour):
                    contour_within_bbox.append(contour)
    
            prop.contour = contour_within_bbox if contour_within_bbox else None
            prop.scaled_contour = None 
            if prop.contour:
                scaled_contour = []
                for cnt in prop.contour:
                    cnt = np.array(cnt, dtype=np.float32)
                    scaled_cnt = [(pt[0][0] * scale_x, pt[0][1] * scale_y) for pt in cnt]
                    scaled_contour.append(np.array(scaled_cnt, dtype=np.float32))
                prop.scaled_contour = scaled_contour
                
            if prop.scaled_contour:
                updated_stats.append(prop)
    
            IMG.stats = updated_stats

        # Rescale the image for display
        original_height, original_width = IMG.img_modified.shape[:2]
        scale_w = new_width / original_width
        scale_h = new_height / original_height
        scale = min(scale_w, scale_h)
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        output_image_resized = cv2.resize(grayscale_with_contours, (new_width, new_height))
    
        for prop in IMG.stats:
            scaled_contour = getattr(prop, "scaled_contour", None)
            if scaled_contour:
                for contour in scaled_contour:
                    contour_points = contour.reshape((-1, 1, 2)).astype(np.int32)
                    cv2.polylines(output_image_resized, [contour_points], isClosed=True, color=(255, 190, 0), thickness=1)

        IMG.tk_extracted_particles_image = ImageTk.PhotoImage(Image.fromarray(output_image_resized))
        
        app_instance.log_message('success', f"Particle extraction is successfully completed with contour erosion of {erosion_value} pixel(s)")
        app_instance.log_message('info', f"{len(IMG.stats)} particles have been extracted")
    
def filter_particles_on_intensity(app_instance, stats, MaxInt):
    """
    Filters particles on their intensity.
    """
    if IMG.stats is None:
        app_instance.log_message('error', "Error: No particle detected")
        return
    
    initial_length = len(IMG.stats)
    if MaxInt != 0:
        MI = np.array([prop.max_intensity for prop in IMG.stats])
        ind = MI > (np.max(MI) * MaxInt)
        IMG.stats = [IMG.stats[i] for i in range(len(IMG.stats)) if ind[i]]
        app_instance.log_message('success', f"Particles with a maximum  intensity lower than {MaxInt:.2f} of the overall maximum intensity of the image have been successfully filtrated")
        app_instance.log_message('info', f"{initial_length - len(IMG.stats)} particles removed, {len(IMG.stats)} particles remaining")

    else:
        app_instance.log_message('info', "No intensity filtering applied")

def filter_particles_on_size(app_instance, stats, MinSize):
    """
    Filters particles on their size.
    """
    if IMG.stats is None:
        app_instance.log_message('error', "Error: No particle detected")
        return

    initial_length = len(IMG.stats)
    if MinSize != 0:
        areas = np.array([prop.area for prop in IMG.stats])
        size_mask = areas >= MinSize
        IMG.stats = [IMG.stats[i] for i in range(len(IMG.stats)) if size_mask[i]]
        app_instance.log_message('success', f"Particles smaller than {MinSize:.2f} pixels have been successfully filtrated")
        app_instance.log_message('success', f"{initial_length - len(IMG.stats)} particles removed, {len(IMG.stats)} particles remaining")
    else:
        app_instance.log_message('info', "No size filtering applied")
        
def filter_particles_on_aspect_ratio(app_instance, stats, MinAspectRatio):
    """
    Filters particles on their aspect ratio.
    """
    if IMG.stats is None:
        app_instance.log_message('error', "Error: No particle detected")
        return

    initial_length = len(IMG.stats)
    if MinAspectRatio != 0:
        aspectratios = np.array([prop.aspect_ratio for prop in IMG.stats])
        aspect_mask = aspectratios >= MinAspectRatio
        IMG.stats = [IMG.stats[i] for i in range(len(IMG.stats)) if aspect_mask[i]]
        app_instance.log_message('success', f"Particles with an aspect ratio lower than {MinAspectRatio:.2f} have been successfully filtrated")
        app_instance.log_message('success', f"{initial_length - len(IMG.stats)} particles removed, {len(IMG.stats)} particles remaining")
    else:
        app_instance.log_message('info', "No size filtering applied")

###############################################################################
# Batch processing (SPM)
###############################################################################

def extract_batch_particles(app_instance, file_paths, vignette_folder_path, csv_file_path, height, width, depth, erosion_value, particle_hole_filling, i):
    """
    Extract and computes particles properties on a batch of images.
    """
    if IMG.img_modified[i] is None:    
        image = IMG.selected_image[i]
        IMG.img_modified[i] = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

    threshold_value = threshold_otsu(IMG.img_modified[i])
    if IMG.image_background[i] == 'white':
        IMG.img_binary[i] = clear_border(IMG.img_modified[i] < threshold_value)
    else:
        IMG.img_binary[i] = clear_border(IMG.img_modified[i] > threshold_value)

    IMG.img_binary[i] = binary_erosion(IMG.img_binary[i], footprint=disk(erosion_value))

    if particle_hole_filling:
        IMG.img_binary[i] = binary_fill_holes(IMG.img_binary[i])

    CC = label(IMG.img_binary[i], connectivity=1)
    IMG.stats[i] = regionprops(CC, intensity_image=IMG.img_modified[i])

    def process_particle(prop, pixel_size):
        return {
            "coords": prop.coords,
            "area": prop.area,
            "area_um2": prop.area * pixel_size**2,
            "centroid": prop.centroid,
            "max_intensity": prop.max_intensity,
            "min_intensity": prop.min_intensity,
            "mean_intensity": prop.mean_intensity,
            "equivalent_diameter_um": prop.equivalent_diameter * pixel_size,
            "major_axis_length_um": prop.major_axis_length * pixel_size,
            "minor_axis_length_um": prop.minor_axis_length * pixel_size,
            "perimeter_um": prop.perimeter * pixel_size,
            "volume_um3": (4/3) * np.pi * (prop.equivalent_diameter * pixel_size / 2)**3,
            "volume_ul": (4/3) * np.pi * (prop.equivalent_diameter * pixel_size / 2)**3 * 1e-9,
            "max_feret_diameter": prop.feret_diameter_max * pixel_size,
            "aspect_ratio": (prop.minor_axis_length * pixel_size) / (prop.major_axis_length * pixel_size) if prop.major_axis_length > 0 else None,
            "solidity": prop.solidity,
            "form_factor": (4 * np.pi * prop.area) / (prop.perimeter ** 2) if prop.perimeter > 0 else None,
            "sphericity": (2 * np.sqrt(np.pi * (prop.area * pixel_size**2))) / (prop.perimeter * pixel_size) if prop.area > 0 and prop.perimeter > 0 else None,
            "roundness": (4 * (prop.area * pixel_size**2)) / (np.pi * ((prop.feret_diameter_max * pixel_size) ** 2)) if prop.area > 0 and prop.feret_diameter_max > 0 else None,
            "orientation": prop.orientation,
            "extent": prop.extent,
            "euler_number": prop.euler_number,
            "fractal_dimension_2D": 2 * (np.log(prop.perimeter * pixel_size) / np.log(prop.area * pixel_size**2)) if prop.perimeter > 0 and prop.area > 0 else None,
            "fractal_dimension_3D": -1.63 * (2 * (np.log(prop.perimeter * pixel_size) / np.log(prop.area * pixel_size**2))) + 4.6 if prop.perimeter > 0 and prop.area > 0 else None,
            "kurtosis": float(kurtosis(prop.intensity_image[prop.image], fisher=True, bias=False)) if np.std(prop.intensity_image[prop.image]) > 1e-8 else None,
            "skewness": float(skew(prop.intensity_image[prop.image], bias=False)) if np.std(prop.intensity_image[prop.image]) > 1e-8 else None,
            "mean_RGB_color": 'unknown',
            "particle_color": 'unknown'
        }

    # Parallel processing of properties
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        processed_particles = list(executor.map(lambda prop: process_particle(prop, IMG.pixel_sizes[i]), IMG.stats[i]))

    for i in range(len(IMG.selected_image)):
        if len(IMG.selected_image[i].shape) == 3 and IMG.selected_image[i].shape[2] == 3:
            for particle in processed_particles:
                coords = particle['coords']
                scale_row = IMG.selected_image[i].shape[0] / IMG.img_modified[i].shape[0]
                scale_col = IMG.selected_image[i].shape[1] / IMG.img_modified[i].shape[1]
                coords_rescaled = np.zeros_like(coords, dtype=float)
                coords_rescaled[:, 0] = coords[:, 0] * scale_row
                coords_rescaled[:, 1] = coords[:, 1] * scale_col
                coords_rescaled = np.round(coords_rescaled).astype(int)
                coords_rescaled[:, 0] = np.clip(coords_rescaled[:, 0], 0, IMG.selected_image[i].shape[0] - 1)
                coords_rescaled[:, 1] = np.clip(coords_rescaled[:, 1], 0, IMG.selected_image[i].shape[1] - 1)
                pixel_values = IMG.selected_image[i][coords_rescaled[:, 0], coords_rescaled[:, 1], :]

                particle['mean_RGB_color'] = np.mean(pixel_values, axis=0)

                r, g, b = particle['mean_RGB_color']
                r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
                h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
                h_deg = h * 360

                if v < 0.2:
                    particle['particle_color'] = 'black'
                elif s < 0.25 and v > 0.8:
                    particle['particle_color'] = 'white'
                elif (h_deg >= 0 and h_deg < 20) or (h_deg > 340 and h_deg <= 360):
                    particle['particle_color'] = 'red'
                elif h_deg >= 20 and h_deg < 40:
                    particle['particle_color'] = 'orange'
                elif h_deg >= 40 and h_deg < 70:
                    particle['particle_color'] = 'yellow'
                elif h_deg >= 70 and h_deg < 160:
                    particle['particle_color'] = 'green'
                elif h_deg >= 160 and h_deg < 270:
                    particle['particle_color'] = 'blue'
                else:
                    particle['particle_color'] = 'unknown'
        else:
            for particle in processed_particles:
                particle['particle_color'] = 'unknown'

    # Remove particles with invalid properties
    volume_threshold = 1e-8 
    IMG.stats[i] = [
        particle for particle in processed_particles
        if all(particle[attr] is not None for attr in ['aspect_ratio', 'form_factor', 'sphericity', 'roundness']) and
           particle['volume_ul'] > volume_threshold
    ]
    
    if IMG.stats[i]:
        if IMG.img_binary[i].dtype != np.uint8:
            IMG.img_binary[i] = (IMG.img_binary[i] * 255).astype(np.uint8)
        contours, _ = cv2.findContours(IMG.img_binary[i], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    save_batch_particles_csv(IMG.stats[i], IMG.image_paths[i], app_instance, csv_file_path)

    if IMG.stats[i]:
        if IMG.img_binary[i].dtype != np.uint8:
            IMG.img_binary[i] = (IMG.img_binary[i] * 255).astype(np.uint8)
        contours, _ = cv2.findContours(IMG.img_binary[i], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        #######################################################################
        ## 1 ## Load particle size (ESD) bins/classes from bins.txt file
        #######################################################################
                
        try:
            resource = resources.files("sandi.attributes") / "bins.txt"
            with resources.as_file(resource) as bins_path:
                if not bins_path.exists():
                    raise FileNotFoundError(f"{bins_path} does not exist.")
                bins = np.genfromtxt(bins_path, delimiter=',', dtype=float)
                if bins.ndim == 1:
                    bins = bins.reshape(-1, 1)
        except Exception as e:
            app_instance.log_message('error', f"Error loading bins.txt: {e}")
        
        if os.path.exists(bins_txt_path):
            try:
                bins = np.loadtxt(bins_txt_path)
                bins = np.genfromtxt(bins_txt_path, delimiter=',')
                if bins.ndim == 1:
                    bins = bins.reshape(-1, 1)  
                bins = bins.astype(float)
                
            except Exception as e:
                app_instance.log_message('error', f"Error loading {bins_txt_path}: {e}")
        else:
            app_instance.log_message('error', f"{bins_txt_path} does not exist.")
        
        try:
            bin_edges = bins[:, 0]
            midpoints = np.sqrt(bin_edges[1:] * bin_edges[:-1]) 
            IMG.bin_edges = bin_edges.flatten()
            
        except Exception as e:
            app_instance.log_message('error', f"Error during bin edges and midpoints creation: {e}")
        
        #######################################################################
        ## 2 ## Assign each particle to its corresponding bin
        #######################################################################
        
        try:
            EqDiameter = np.array([particle['equivalent_diameter_um'] for particle in IMG.stats[i] if particle is not None])
            BinInd = np.digitize(EqDiameter, bin_edges) - 1 
            BinInd = BinInd[BinInd >= 0]
            particles_per_bin = np.bincount(BinInd)
            particles_per_bin = np.pad(particles_per_bin, (0, len(midpoints) - len(particles_per_bin)), 'constant')
        except Exception as e:
            app_instance.log_message('error', f"Error during assignment of particles in bins: {e}")
                
        #######################################################################
        ## 3 ## Calculate the total volume per bin
        #######################################################################
        
        try:
            volume_ul = np.array([particle['volume_ul'] for particle in IMG.stats[i]]) 
            volume_per_bin = np.zeros((len(midpoints),)) 
            volume_per_bin[:len(np.bincount(BinInd, weights=volume_ul))] = np.bincount(BinInd, weights=volume_ul)             
            volume_per_bin = pd.DataFrame({
                'Particle Size': midpoints.flatten(),  
                'Total Volume': volume_per_bin,
                'Particle Count': particles_per_bin
            }) 
        except Exception as e:
            app_instance.log_message('error', f"Error during bins volume calculation: {e}")
        
        #######################################################################
        ## 4 ## Calculate volume concentration per size class
        #######################################################################
        
        try:
            volume_concentration_per_bin = volume_per_bin['Total Volume'].values
            volume_concentration_per_bin /= (float(height) * float(width) * float(depth) * 10**-6)   
            volume_concentration_per_bin = np.array(volume_concentration_per_bin)
            total_volume_concentration = np.sum(volume_concentration_per_bin) 
        except Exception as e:
            app_instance.log_message('error', f"Error during calculation of the volume concentration: {e}")
        
        #######################################################################
        ## 4 ## Calculate the cumulative volume distribution
        #######################################################################
        
        try:
            cumulative_volume = np.cumsum(volume_concentration_per_bin) 
            cdf = (cumulative_volume / cumulative_volume[-1]) * 100 
        except Exception as e:
            app_instance.log_message('error', f"Error during calculation of the cumulative volume distribution: {e}")
        
        #######################################################################
        ## 5 ## Calculate D10, D50, D90 (volume-based)
        #######################################################################
    
        try:
            freq_n, bin_edges = np.histogram(EqDiameter, bins=bin_edges)
            freq = freq_n / np.sum(freq_n)
            
            cdf = cdf.flatten()
            midpoints = midpoints.flatten()   

            # D10, D50, D90
            D10 = np.interp(10, cdf, midpoints)
            D50 = np.interp(50, cdf, midpoints)
            D90 = np.interp(90, cdf, midpoints)
        except Exception as e:
            app_instance.log_message('error', f"Error during calculation of D10, D50, D90: {e}")
        
        #######################################################################
        ## 6 ## Calculate volume weighted mean diameter
        #######################################################################
        
        try:
            diameters = np.array([particle['equivalent_diameter_um'] for particle in IMG.stats[i]])
            volumes = np.array([particle['volume_ul'] for particle in IMG.stats[i]])
            mean_diameter = np.sum(volumes * diameters) / np.sum(volumes)
            
        except Exception as e:
            app_instance.log_message('error', f"Error during mean diameter calculation: {e}")
        
        #######################################################################
        ## 7 ## Calculate mean values and PSD for each image of the batch and save CSV
        #######################################################################
        
        try:
            image_name = os.path.basename(file_paths[i]) 
            image_date_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_paths[i]))
            mean_solidity = np.mean([particle['solidity'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_form_factor = np.mean([particle['form_factor'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_sphericity = np.mean([particle['sphericity'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_roundness = np.mean([particle['roundness'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_extent = np.mean([particle['extent'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_fractal_dimension_2D = np.mean([particle['fractal_dimension_2D'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_fractal_dimension_3D = np.mean([particle['fractal_dimension_3D'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_major_axis_length = np.mean([particle['major_axis_length_um'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_minor_axis_length = np.mean([particle['minor_axis_length_um'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_feret = np.mean([particle['max_feret_diameter'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            number_particles = len(IMG.stats[i])
            mean_aspect_ratio = np.mean([particle['aspect_ratio'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_area = np.mean([particle['area_um2'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            mean_perimeter = np.mean([particle['perimeter_um'] for particle in IMG.stats[i]]) if IMG.stats[i] else 0
            kurtosiss = np.array([particle['kurtosis'] for particle in IMG.stats[i] if particle['kurtosis'] is not None])
            mean_kurtosis = np.nanmean(kurtosiss) if kurtosiss.size > 0 else -99.99
            
            skewnesss = np.array([particle['skewness'] for particle in IMG.stats[i] if particle['skewness'] is not None])
            mean_skewness = np.nanmean(skewnesss) if skewnesss.size > 0 else -99.99
            
            mean_intensities = np.array([particle['mean_intensity'] for particle in IMG.stats[i] if particle['mean_intensity'] is not None])
            mean_mean_intensity = np.nanmean(mean_intensities) if mean_intensities.size > 0 else -99.99
            
        except Exception as e:
            app_instance.log_message('error', f"Error during image mean statistics calculation: {e}")
            
        try:    
            image_stats_dict = {
                "Image Name": image_name,
                "Datetime": image_date_time,
                "D10": D10,
                "D50": D50,
                "D90": D90,
                "Mean Solidity": mean_solidity,
                "Mean Form Factor": mean_form_factor,
                "Mean Sphericity": mean_sphericity,
                "Mean Roundness": mean_roundness,
                "Mean Extent": mean_extent,
                "Mean Aspect Ratio": mean_aspect_ratio,
                "Mean Fractal Dimension 2D": mean_fractal_dimension_2D,
                "Mean Fractal Dimension 3D": mean_fractal_dimension_3D,
                "Mean Major-Axis-Length (um)": mean_major_axis_length,
                "Mean Minor-Axis-Length (um)": mean_minor_axis_length,
                "Mean Feret (um)": mean_feret,
                "Number of Particles": number_particles,
                "Mean Area (um²)": mean_area,
                "Mean Perimeter (um)": mean_perimeter,
                "Mean Diameter (um)": mean_diameter,
                "Mean Mean Intensity": mean_mean_intensity,
                "Mean Kurtosis": mean_kurtosis,
                "Mean Skewness": mean_skewness,
                "Total Volume Concentration (ul/l)": total_volume_concentration,
                "1.21449578": volume_concentration_per_bin[0],
                "1.60249025": volume_concentration_per_bin[1],
                "1.891035166": volume_concentration_per_bin[2],
                "2.23134399": volume_concentration_per_bin[3],
                "2.633450968": volume_concentration_per_bin[4],
                "3.107850704": volume_concentration_per_bin[5],
                "3.666961685": volume_concentration_per_bin[6],
                "4.327133347": volume_concentration_per_bin[7],
                "5.106510257": volume_concentration_per_bin[8],
                "6.025832888": volume_concentration_per_bin[9],
                "7.111107509": volume_concentration_per_bin[10],
                "8.39172807": volume_concentration_per_bin[11],
                "9.90256593": volume_concentration_per_bin[12],
                "11.68543358": volume_concentration_per_bin[13],
                "13.78971066": volume_concentration_per_bin[14],
                "16.27318162": volume_concentration_per_bin[15],
                "19.20366522": volume_concentration_per_bin[16],
                "22.66131587": volume_concentration_per_bin[17],
                "26.74179968": volume_concentration_per_bin[18],
                "31.55729789": volume_concentration_per_bin[19],
                "37.23981168": volume_concentration_per_bin[20],
                "43.94534164": volume_concentration_per_bin[21],
                "51.85865627": volume_concentration_per_bin[22],
                "61.19717694": volume_concentration_per_bin[23],
                "72.21641829": volume_concentration_per_bin[24],
                "85.2202712": volume_concentration_per_bin[25],
                "100.5661856": volume_concentration_per_bin[26],
                "118.6746248": volume_concentration_per_bin[27],
                "140.0438222": volume_concentration_per_bin[28],
                "165.261362": volume_concentration_per_bin[29],
                "195.0198203": volume_concentration_per_bin[30],
                "230.1369158": volume_concentration_per_bin[31],
                "272.6270346": volume_concentration_per_bin[32],
                "324.2098302": volume_concentration_per_bin[33],
                "385.5523982": volume_concentration_per_bin[34],
                "458.5019084": volume_concentration_per_bin[35],
                "545.2540692": volume_concentration_per_bin[36],
                "648.4201189": volume_concentration_per_bin[37],
                "771.1053416": volume_concentration_per_bin[38],
                "917.0038168": volume_concentration_per_bin[39],
                "1090.50768": volume_concentration_per_bin[40],
                "1296.839693": volume_concentration_per_bin[41],
                "1542.211142": volume_concentration_per_bin[42],
                "1834.008179": volume_concentration_per_bin[43],
                "2181.01536": volume_concentration_per_bin[44],
                "2593.678927": volume_concentration_per_bin[45],
                "3084.421738": volume_concentration_per_bin[46],
                "3668.016358": volume_concentration_per_bin[47],
                "4362.03072": volume_concentration_per_bin[48],
                "5187.357853": volume_concentration_per_bin[49],
                "6153.251669": volume_concentration_per_bin[50],
                "7282.771116": volume_concentration_per_bin[51],
                "8629.279192": volume_concentration_per_bin[52],
                "10256.59673": volume_concentration_per_bin[53],
                "12224.88304": volume_concentration_per_bin[54],
                "14609.54506": volume_concentration_per_bin[55],
                "17494.89787": volume_concentration_per_bin[56]
            }
        except Exception as e:
            app_instance.log_message('error', f"Error during image_stats_dict creation: {e}")       

    app_instance.log_message('info', f"{len(IMG.stats[i])} particles have been extracted for image {IMG.image_names[i]}")  
    app_instance.log_message('success', f"Particle extraction is successfully completed for image {IMG.image_names[i]}")
    app_instance.log_message('success', 'CSV file containing the detailed particles measurements successfully exported and mean statistics have been added to the batch_statistics file')
    
    generate_batch_vignettes(app_instance, "suspended particles", IMG.stats[i], i, vignette_folder_path, IMG.pixel_sizes[i], image_name)
        
    return image_stats_dict    
        
###############################################################################
# Single image processing (gravels)
###############################################################################

def extract_stones(app_instance, image_name, vignette_folder_path=None):
    """
    Extracts gravels from an image with a white background.
    """
    # Step 1: Load and preprocess the image
    if IMG.img_modified is None:    
        image = IMG.selected_image
        if len(image.shape) == 3: 
            IMG.img_modified = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            IMG.img_modified = image
            
    app_instance.log_message('info', f"Pixel size is: {IMG.pixel_size:.3f}")
    
    # Step 2: Check if the image is empty or lacks enough contrast
    if np.max(IMG.img_modified) <= 110 or np.std(IMG.img_modified) < 1 or np.mean(IMG.img_modified) < 2:
        app_instance.log_message('error', "Error: No particle detected")
        return

    # Step 3: Convert to binary using Otsu thresholding
    threshold_value = threshold_otsu(IMG.img_modified)
    IMG.img_binary = IMG.img_modified < threshold_value
    IMG.img_binary = clear_border(IMG.img_binary) 

    # Step 4: Fill holes inside particles using morphological closing
    IMG.img_binary = morphology.closing(IMG.img_binary, morphology.square(3))  
    IMG.img_binary = ndi.binary_fill_holes(IMG.img_binary)

    # Step 5: Get original image dimensions
    original_image_height, original_image_width = IMG.img_modified.shape[:2]

    # Step 6: Make binary image displayable on canvas
    IMG.tk_binary_image = ImageTk.PhotoImage(
        Image.fromarray(IMG.img_binary).resize((RESIZE_WIDTH, RESIZE_HEIGHT))
    )

    # Step 7: Identify gravels and calculate statistics
    CC = label(IMG.img_binary, connectivity=1)
    IMG.stats = regionprops(CC, intensity_image=IMG.img_modified)

    # Step 8: Filter properties to keep only contours, centroids, and bounding boxes
    for prop in IMG.stats:
        prop.contour = None
        prop.scaled_centroid = None

    # Step 9: Parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        contours_and_props = list(executor.map(lambda p: (p, p.centroid), IMG.stats))

    # Step 10: Detect contours in the binary image
    if IMG.img_binary.dtype != np.uint8:
        IMG.img_binary = (IMG.img_binary * 255).astype(np.uint8)
    
    contours, _ = cv2.findContours(IMG.img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Step 11: Find contours for each particle
    for prop, centroid in contours_and_props:
        contour_within_bbox = []
        for contour in contours:
            if all(prop.bbox[0] <= pt[0][1] <= prop.bbox[2] and prop.bbox[1] <= pt[0][0] <= prop.bbox[3] for pt in contour):
                contour_within_bbox.append(contour)
        prop.contour = contour_within_bbox if contour_within_bbox else None
        if centroid:
            prop.scaled_centroid = centroid

    # Step 12: Draw contours on the grayscale image
    IMG.img_modified_8bit = cv2.normalize(IMG.img_modified, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    grayscale_with_contours = cv2.cvtColor(IMG.img_modified_8bit, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(grayscale_with_contours, contours, -1, (255, 190, 0), 6)
    
    # Step 13: Resize the image with contours for display
    output_image_resized = cv2.resize(grayscale_with_contours, (RESIZE_WIDTH, RESIZE_HEIGHT))
    IMG.tk_extracted_particles_image = ImageTk.PhotoImage(Image.fromarray(output_image_resized))
    
    # Step 14: Calculate scaling factors
    scale_x = RESIZE_WIDTH / original_image_width
    scale_y = RESIZE_HEIGHT / original_image_height
    
    # Step 15: Adapt centroids and contours to resized image
    for i, prop in enumerate(IMG.stats):
        if prop.centroid:
            centroid = prop.centroid
            prop.scaled_centroid = (centroid[1] * scale_x, centroid[0] * scale_y)
        contour = prop.contour
        if contour:
            scaled_contour = []
            for cnt in contour:
                scaled_cnt = [(pt[0][0] * scale_x, pt[0][1] * scale_y) for pt in cnt]
                scaled_contour.append(np.array(scaled_cnt, dtype=np.int32))
            prop.scaled_contour = scaled_contour
        IMG.stats[i] = prop

    app_instance.log_message('success', "Gravel extraction is successfully completed.")
    app_instance.log_message('info', f"{len(IMG.stats)} gravels have been extracted.")
    
def extract_stones_on_green(app_instance, image_name, vignette_folder_path=None):
    """
    Extracts gravels from an image with a green background.
    """
    # Step 1: Load and preprocess the image
    if IMG.img_modified is None:    
        image = IMG.selected_image
        if len(image.shape) == 3:  
            IMG.img_modified = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)  # Convert to HSV
        else:
            app_instance.log_message('error', "Error: Image is not in color")
            return

    app_instance.log_message('error', f"Pixel size is: {IMG.pixel_size}")
    
    IMG.img_modified = cv2.fastNlMeansDenoisingColored(IMG.img_modified, None, 15, 15, 7, 21)

    # Step 2: Define HSV range for green background removal
    lower_green = np.array([35, 80, 75])  
    upper_green = np.array([85, 255, 255])

    # Create a mask for the green background
    mask = cv2.inRange(IMG.img_modified, lower_green, upper_green)

    # Invert the mask to get the gravels
    IMG.img_binary = cv2.bitwise_not(mask) > 0  

    # Step 3: Remove particles touching the border
    IMG.img_binary = clear_border(IMG.img_binary)

    # Step 4: Fill holes inside gravels using morphological closing
    IMG.img_binary = closing(IMG.img_binary, square(3)) 
    IMG.img_binary = binary_fill_holes(IMG.img_binary)

    # Step 5: Get original image dimensions
    original_image_height, original_image_width = IMG.img_modified.shape[:2]

    # Step 6: Make binary image displayable on canvas
    IMG.tk_binary_image = ImageTk.PhotoImage(
        Image.fromarray(IMG.img_binary.astype(np.uint8) * 255).resize((RESIZE_WIDTH, RESIZE_HEIGHT))
    )

    # Step 7: Identify gravels and compute statistics
    CC = label(IMG.img_binary, connectivity=1)
    IMG.stats = regionprops(CC)

    # Step 8: Filter properties to keep only contours, centroids, and bounding boxes
    for prop in IMG.stats:
        prop.contour = None
        prop.scaled_centroid = None

    # Step 9: Parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        contours_and_props = list(executor.map(lambda p: (p, p.centroid), IMG.stats))

    # Step 10: Detect contours in the binary image
    if IMG.img_binary.dtype != np.uint8:
        IMG.img_binary = (IMG.img_binary * 255).astype(np.uint8)
    
    contours, _ = cv2.findContours(IMG.img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Step 11: Find contours for each particle
    for prop, centroid in contours_and_props:
        contour_within_bbox = [cnt for cnt in contours if all(prop.bbox[0] <= pt[0][1] <= prop.bbox[2] and prop.bbox[1] <= pt[0][0] <= prop.bbox[3] for pt in cnt)]
        prop.contour = contour_within_bbox if contour_within_bbox else None
        if centroid:
            prop.scaled_centroid = centroid

    # Step 12: Prepare the image for display with contours and white background
    IMG.img_modified = cv2.cvtColor(IMG.img_modified, cv2.COLOR_HSV2RGB) 
    cv2.drawContours(IMG.img_modified, contours, -1, (0, 0, 0), 6) 
    
    # Step 13: Resize the image with contours for display
    output_image_resized = cv2.resize(IMG.img_modified, (RESIZE_WIDTH, RESIZE_HEIGHT))
    IMG.tk_extracted_particles_image = ImageTk.PhotoImage(Image.fromarray(output_image_resized))
    
    # Step 14: Calculate scaling factors
    scale_x = RESIZE_WIDTH / original_image_width
    scale_y = RESIZE_HEIGHT / original_image_height
    
    # Step 15: Adapt centroids and contours to resized image
    for i, prop in enumerate(IMG.stats):
        if prop.centroid:
            centroid = prop.centroid
            prop.scaled_centroid = (centroid[1] * scale_x, centroid[0] * scale_y)
        contour = prop.contour
        if contour:
            prop.scaled_contour = [np.array([(pt[0][0] * scale_x, pt[0][1] * scale_y) for pt in cnt], dtype=np.int32) for cnt in contour]
        IMG.stats[i] = prop

    app_instance.log_message('success', "Gravel extraction is successfully completed.")
    app_instance.log_message('info', f"{len(IMG.stats)} gravels have been extracted.")
    
def filter_stones_on_size(app_instance, stats, MinSize):
    """
    Filters gravels based on their size.
    """
    if IMG.stats is None:
        app_instance.log_message('error', "Error: No gravel detected")
        return
    if MinSize != 0:
        lengths = np.array([prop.major_axis_length for prop in IMG.stats])
        MinSize_pix = MinSize / IMG.pixel_size
        size_mask = lengths >= MinSize_pix
        IMG.stats = [IMG.stats[i] for i in range(len(IMG.stats)) if size_mask[i]]
        app_instance.log_message('success', f"{len(IMG.stats)} gravels have been retained after filtrating particles smaller than {MinSize:.2f} cm.")
    else:
        app_instance.log_message('info', "No size filtering applied.")