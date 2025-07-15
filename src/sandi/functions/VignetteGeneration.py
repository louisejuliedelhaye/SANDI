# -*- coding: utf-8 -*-
"""
File: vignettes generation
Version: SANDI v1.0.0-beta
Created on Tue Jul  9 20:13:28 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: File containing the functions needed to generate individual vignettes for the single image processing, batch processing and gravel processing.
"""

###############################################################################
# Import packages
###############################################################################

import numpy as np
import cv2
import os
import sys
from tkinter import filedialog
from PIL import Image

###############################################################################
# Import local packages
###############################################################################

from sandi.attributes.IMG import IMG

###############################################################################
# For single images processing (SPM and gravels)
###############################################################################

def generate_vignette(app_instance, sample_type, stats):
    """
    Creates the vignettes for gravels and suspended particles for the processing of a single image.
    
    Called functions:
        add_scale_bar (local)
    """
    if not stats:
        if sample_type == "gravel":
            app_instance.log_message('error', "No gravel data found in IMG.stats.")
        elif sample_type == "suspended particles":
            app_instance.log_message('error', "No particle data found in IMG.stats.")
    else:
        vignette_folder_path = filedialog.askdirectory(title="Select folder to save vignettes")
        
        if not vignette_folder_path:
            app_instance.log_message('info', "Vignette saving canceled by user.")
        else:
            if IMG.img_original_resampled is not None:
                original_image = IMG.img_original_resampled
            else:
                original_image = np.array(Image.open(IMG.filename).convert("RGB"))
                original_image = cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR)
            black_and_white_image = IMG.img_binary
        
            # Ensure the black-and-white image is in uint8 format
            if black_and_white_image.dtype != np.uint8:
                black_and_white_image = (black_and_white_image * 255).astype(np.uint8)
            
            if original_image.ndim == 2: 
                original_image = cv2.cvtColor(original_image, cv2.COLOR_GRAY2BGR)
            
            overlayed_image = original_image.copy()
        
            # Find contours in the bw image
            contours, _ = cv2.findContours(black_and_white_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            if sample_type == "gravel":
                thickness = 2
            elif sample_type == "suspended particles":
                thickness = 1
            
            # Draw contours in yellow
            cv2.drawContours(overlayed_image, contours, -1, (66, 188, 255), 1)
            for contour in contours:
                cv2.drawContours(overlayed_image, [contour], 0, (66, 188, 255), thickness=thickness)
                
            if sample_type == "gravel":
                # Define a green range for masking
                overlayed_image_hsv = cv2.cvtColor(overlayed_image, cv2.COLOR_BGR2HSV)
                lower_green = np.array([35, 80, 75])  
                upper_green = np.array([85, 255, 255])
                green_mask = cv2.inRange(overlayed_image_hsv, lower_green, upper_green)             
                # Replace the green background with white
                overlayed_image[green_mask != 0] = [0, 0, 0]
        
            # Process each particle in IMG.stats
            for i, prop in enumerate(IMG.stats):
                # Extract x and y coordinates for the particle
                x_coords = prop.coords[:, 1]
                y_coords = prop.coords[:, 0]
                margin = 15
        
                # Define the bounding box around the particle with a margin
                x_min = max(0, min(x_coords) - margin)
                x_max = min(overlayed_image.shape[1], max(x_coords) + margin)
                y_min = max(0, min(y_coords) - margin)
                y_max = min(overlayed_image.shape[0], max(y_coords) + margin)
        
                # Crop the overlayed image to the bounding box
                cropped_image = overlayed_image[y_min:y_max, x_min:x_max]
                
                # Calculate ideal scale length (SPM)
                cropped_width = x_max - x_min
                raw_length = cropped_width / 5
                scale_length_pixels = int(round(raw_length / 10) * 10)
                min_pixels = int(10 / IMG.pixel_size)
                scale_length_pixels = max(scale_length_pixels, min_pixels)
        
                # Check for a valid cropped image size
                rows, cols = cropped_image.shape[:2]
                if rows == 0 or cols == 0:
                    if sample_type == "gravel":
                        app_instance.log_message('error', f"Invalid cropped image size for gravel {i}: rows={rows}, cols={cols}")
                    elif sample_type == "suspended particles":
                        app_instance.log_message('error', f"Invalid cropped image size for particle {i}: rows={rows}, cols={cols}")
                    continue
                
                # Add a scale bar to the cropped image
                if sample_type == "gravel":
                    vignette_with_scale = add_scale_bar(cropped_image, scale_length_pixels=None, sample_type="gravel")
                elif sample_type == "suspended particles":
                    vignette_with_scale = add_scale_bar(cropped_image, scale_length_pixels=scale_length_pixels, sample_type="suspended particles")
                
                if sample_type == "gravel":
                    vignette_name = f"{IMG.image_name}_gravel_{i}.png"
                elif sample_type == "suspended particles":
                    vignette_name = f"{IMG.image_name}_particle_{i}.png"
                
                vignette_path = os.path.join(vignette_folder_path, vignette_name)
        
                # Check if the user canceled the save dialog
                if not vignette_path:
                    if sample_type == "gravel":
                        app_instance.log_message('info', f"Vignette save canceled by user for gravel {i}.")
                    elif sample_type == "suspended particles":
                        app_instance.log_message('info', f"Vignette save canceled by user for particle {i}.")
                    continue
        
                # Save the vignette image
                cv2.imwrite(vignette_path, vignette_with_scale)
                
            app_instance.log_message('success', 'Vignettes successfully exported')


def add_scale_bar(image, scale_length_pixels, sample_type):
    """
    Add a scale bar to the vignette.
    """
    # Convert the image to BGR if needed
    if len(image.shape) == 2:
        image_with_scale = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        image_with_scale = image.copy()

    pixelsize = IMG.pixel_size

    height, width = image_with_scale.shape[:2]

    # Default scale bar length is 1/3 of the image width
    if scale_length_pixels is None:
        fraction = 1 / 3
        scale_length_pixels = int(width * fraction)
    
    # Calculate the required size for the scale bar legend
    if sample_type == "gravel":
        scale_length_cm = 1 
        scale_length_pixels = int(scale_length_cm / pixelsize)
        scale_text = f"{scale_length_cm:.0f} cm"
    elif sample_type == "suspended particles":
        scale_length_um = scale_length_pixels * pixelsize
        if scale_length_um >= 1000:
            scale_text = f"{scale_length_um / 1000:.1f} mm"
        else:
            scale_text = f"{scale_length_um:.0f} µm"

    # Characteristics of the scale bar
    bar_height = max(2, height // 100)
    bar_color = (255, 255, 255)  
    text_color = (255, 255, 255)  
    font = cv2.FONT_HERSHEY_SIMPLEX
    if sample_type == "suspended particles":
        font_scale = max(0.4, width / 800)
    elif sample_type == "gravel":
        font_scale = 0.2
    font_thickness = 1

    # Margins
    horizontal_margin = int(width * 0.05)
    vertical_margin = int(height * 0.03)
    
    if sample_type == "suspended particles":
        if scale_length_um <= 50:
            distance_text_scale = 1
        elif scale_length_um > 50 and scale_length_um <= 100:
            distance_text_scale = 5
        elif scale_length_um > 100:
            distance_text_scale = 10
    elif sample_type == "gravel":
        distance_text_scale = 1
        
    text_size, _ = cv2.getTextSize(scale_text, font, font_scale, font_thickness)

    min_vignette_height = text_size[1] + bar_height + 2 * vertical_margin
    min_vignette_width = scale_length_pixels + 2 * horizontal_margin

    # Resize the image if necessary
    if image_with_scale.shape[0] < min_vignette_height or image_with_scale.shape[1] < min_vignette_width:
        new_height = max(image_with_scale.shape[0], min_vignette_height)
        new_width = max(image_with_scale.shape[1], min_vignette_width)
        new_image = np.zeros((new_height, new_width, 3), dtype=np.uint8)
        new_image[:image_with_scale.shape[0], :image_with_scale.shape[1]] = image_with_scale
        image_with_scale = new_image

    # Recalculate start point based on adjusted image size
    start_point = (image_with_scale.shape[1] - horizontal_margin - scale_length_pixels, image_with_scale.shape[0] - vertical_margin)
    end_point = (image_with_scale.shape[1] - horizontal_margin, image_with_scale.shape[0] - vertical_margin)

    # Draw the scale bar
    image_with_scale = cv2.rectangle(image_with_scale, start_point, (end_point[0], end_point[1] - bar_height), bar_color, -1)

    # Put the scale text
    text_position = (start_point[0], start_point[1] - text_size[1] - distance_text_scale)
    image_with_scale = cv2.putText(image_with_scale, scale_text, text_position, font, font_scale, text_color, font_thickness, cv2.LINE_AA)

    return image_with_scale

###############################################################################
# For SPM batch processing (already added possibility to perform gravel batch processing, to be implemented in the future)
###############################################################################

def generate_batch_vignettes(app_instance, sample_type, stats, i, vignette_folder_path, pixelsize, image_name):
    """
    Creates the vignettes for suspended particles for the processing of multiple images.
    
    Called functions:
        add_scale_bar_batch (local)
    """
    if not stats:
        error_msg = "No gravel data found in IMG.stats." if sample_type == "gravel" else "No particle data found in IMG.stats."
        app_instance.log_message('error', error_msg)
        return

    if not vignette_folder_path:
        app_instance.log_message('info', "Vignette saving canceled by user.")
        return

    if not isinstance(i, int):
        app_instance.log_message('error', f"Invalid index type: {type(i)}. Expected integer.")
        return

    if not isinstance(IMG.img_original_resampled, list) or i >= len(IMG.img_original_resampled):
        app_instance.log_message('error', f"Index {i} is out of range for IMG.img_original_resampled.")
        return

    if IMG.img_original_resampled[i] is not None and IMG.img_original_resampled[i].any():
        original_image = IMG.img_original_resampled[i]
    else:
        original_image = np.array(Image.open(IMG.file_paths[i]))

    black_and_white_image = IMG.img_binary[i]

    if black_and_white_image.dtype != np.uint8:
        black_and_white_image = (black_and_white_image * 255).astype(np.uint8)

    if len(original_image.shape) == 2: 
        overlayed_image = cv2.cvtColor(original_image, cv2.COLOR_GRAY2BGR)
    else: 
        overlayed_image = original_image.copy()

    # Find contours in the bw image
    contours, _ = cv2.findContours(black_and_white_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contours in yellow
    cv2.drawContours(overlayed_image, contours, -1,  (66, 188, 255), 1)

    # Process each particle in IMG.stats
    for particle_idx, particle in enumerate(IMG.stats[i]):  
        x_coords = particle["coords"][:, 1]
        y_coords = particle["coords"][:, 0]
        margin = 15

        # Define the bounding box around the particle with a margin
        x_min = max(0, min(x_coords) - margin)
        x_max = min(overlayed_image.shape[1], max(x_coords) + margin)
        y_min = max(0, min(y_coords) - margin)
        y_max = min(overlayed_image.shape[0], max(y_coords) + margin)

        cropped_image = overlayed_image[y_min:y_max, x_min:x_max]

        rows, cols = cropped_image.shape[:2]
        if rows == 0 or cols == 0:
            error_msg = f"Invalid cropped image size for {sample_type} {i}: rows={rows}, cols={cols}"
            app_instance.log_message('error', error_msg)
            continue
                
        # Calculate ideal scale length (SPM)
        cropped_width = x_max - x_min
        raw_length = cropped_width / 5
        scale_length_pixels = int(round(raw_length / 10) * 10)
        min_pixels = int(10 / pixelsize)
        scale_length_pixels = max(scale_length_pixels, min_pixels)
        
        # Add a scale bar 
        if sample_type == "gravel":
            vignette_with_scale = add_scale_bar_batch(cropped_image, 100, "gravel", pixelsize)
        elif sample_type == "suspended particles":
            vignette_with_scale = add_scale_bar_batch(cropped_image, scale_length_pixels, "suspended particles", pixelsize)
        
        if sample_type == "gravel":
            vignette_name = f"{image_name}_gravel_{particle_idx}.png"
        elif sample_type == "suspended particles":
            vignette_name = f"{image_name}_particle_{particle_idx}.png"
        
        vignette_path = os.path.join(vignette_folder_path, vignette_name)

        # Check if the user canceled the save dialog
        if not vignette_path:
            if sample_type == "gravel":
                app_instance.log_message('info', f"Vignette save canceled by user for gravel {particle_idx}.")
            elif sample_type == "suspended particles":
                app_instance.log_message('info', f"Vignette save canceled by user for particle {particle_idx}.")
            continue

        try:
            cv2.imwrite(vignette_path, vignette_with_scale)
        except Exception as e:
            app_instance.log_message('error', f"Error saving vignette at {vignette_path}: {e}")
        
    app_instance.log_message('success', 'Vignettes successfully saved')


def add_scale_bar_batch(image, scale_length_pixels, sample_type, pixelsize):
    """
    Add a scale bar to the vignettes created during the batch processing.
    """
    for i in enumerate(IMG.stats):

        if len(image.shape) == 2:
            image_with_scale = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            image_with_scale = image.copy()
    
        # Calculate the required size for the scale bar 
        if sample_type == "gravel":
            scale_length_cm = scale_length_pixels * pixelsize
            scale_text = f"{scale_length_cm:.0f} cm"
        elif sample_type == "suspended particles":
            scale_length_um = scale_length_pixels * pixelsize
            scale_text = f"{scale_length_um:.0f} um"
            
        # Characteristics of the scale bar
        bar_height = int(max(scale_length_pixels/10, 2))   
        bar_color = (255, 255, 255)  
        text_color = (255, 255, 255)  
        font = cv2.FONT_HERSHEY_SIMPLEX
        if sample_type == "suspended particles":
            if scale_length_um <= 50:
                font_scale = 0.2
            if scale_length_um > 50:
                font_scale = 0.4
        elif sample_type == "gravel":
            font_scale = 0.2
        font_thickness = 1
        horizontal_margin = 25  
        vertical_margin = 5 
        
        if sample_type == "suspended particles":
            if scale_length_um <= 50:
                distance_text_scale = 1
            elif scale_length_um > 50 and scale_length_um <= 100:
                distance_text_scale = 5
            elif scale_length_um > 100:
                distance_text_scale = 10
        elif sample_type == "gravel":
            distance_text_scale = 1
            
        text_size, _ = cv2.getTextSize(scale_text, font, font_scale, font_thickness)
    
        min_vignette_height = text_size[1] + bar_height + vertical_margin
        min_vignette_width = scale_length_pixels + horizontal_margin
    
        if image_with_scale.shape[0] < min_vignette_height or image_with_scale.shape[1] < min_vignette_width:
            new_height = max(image_with_scale.shape[0], min_vignette_height)
            new_width = max(image_with_scale.shape[1], min_vignette_width)
            new_image = np.zeros((new_height, new_width, 3), dtype=np.uint8)
            new_image[:image_with_scale.shape[0], :image_with_scale.shape[1]] = image_with_scale
            image_with_scale = new_image

        start_point = (image_with_scale.shape[1] - horizontal_margin - scale_length_pixels, image_with_scale.shape[0] - vertical_margin)
        end_point = (image_with_scale.shape[1] - horizontal_margin, image_with_scale.shape[0] - vertical_margin)
    
        image_with_scale = cv2.rectangle(image_with_scale, start_point, (end_point[0], end_point[1] - bar_height), bar_color, -1)
    
        text_position = (start_point[0], start_point[1] - text_size[1] - distance_text_scale)
        image_with_scale = cv2.putText(image_with_scale, scale_text, text_position, font, font_scale, text_color, font_thickness, cv2.LINE_AA)
    
        return image_with_scale