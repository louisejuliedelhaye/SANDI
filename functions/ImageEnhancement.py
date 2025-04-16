# -*- coding: utf-8 -*-
"""
File: functions for the image enhancement and background processing 
Version: SANDI v1.0.0-beta
Created on Wed Aug 21 14:06:22 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: functions for the image enhancement and background processing 
"""

###############################################################################
# Import packages
###############################################################################

import sys
import os
import numpy as np
import cv2
from skimage.morphology import reconstruction
import concurrent.futures
from PIL import Image, ImageTk 
from skimage import transform

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
# Functions definition
###############################################################################

def rgb_to_grey(img_rgb):
    """
    Convert an RGB image to a grayscale image.
    """
    if len(img_rgb.shape) == 3:  
        IMG.img_grey = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    else:
        IMG.img_grey = img_rgb
    return IMG.img_grey

def denoise(img_grey, denoise_filter_strength):
    """
    Denoise a grayscale image using Non-Local Means Denoising with adjustable filter strength.
    """     
    denoised_image = cv2.fastNlMeansDenoising(img_grey, None, denoise_filter_strength, 7, 21)
    IMG.img_modified = denoised_image
    img_rgb = cv2.cvtColor(denoised_image, cv2.COLOR_GRAY2RGB)
    resized_img = cv2.resize(img_rgb, (RESIZE_WIDTH, RESIZE_HEIGHT))
    IMG.tk_denoised_image = ImageTk.PhotoImage(Image.fromarray(resized_img))
    return IMG.img_modified
    
def histogram_stretching(image, minimum, maximum):
    """
    Enhances the contrast of a grayscale image by stretching its clipped pixel intensity values to cover
    the full range of 0 to 255. 
    """
    if image is not None:
        img_clipped = np.clip(image, minimum, maximum)
        IMG.img_modified = np.uint8((img_clipped - minimum) / (maximum - minimum) * 255)
        IMG.tk_stretched_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((RESIZE_WIDTH, RESIZE_HEIGHT)))
        return IMG.img_modified
    else:
        pass
    
def correct_background_illumination(img, BlockSize, pixelsize):
    """
    Homogeneizes the background illumination by iterating a window of chosen size (BlockSize) over the image to detect the minimum value in each. 
    """
    w = int(np.ceil((BlockSize * 1000) / pixelsize))  
    bg = cv2.erode(img, np.ones((w, w)))  
    bg = cv2.resize(bg, (img.shape[1], img.shape[0]))  
    img = img - bg  
    IMG.img_modified = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)  
    IMG.tk_corrected_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((RESIZE_WIDTH, RESIZE_HEIGHT)))
    return IMG.img_modified
    
def lighten_shadows_with_gamma(img, gamma_value):
    """
    This function applies gamma correction to lighten the shadows in an image.
    """
    img_normalized = img / 255.0
    img_gamma_corrected = np.power(img_normalized, gamma_value)
    img_gamma_corrected = np.uint8(cv2.normalize(img_gamma_corrected, None, 0, 255, cv2.NORM_MINMAX))
    img_resized = cv2.resize(img_gamma_corrected, (RESIZE_WIDTH, RESIZE_HEIGHT))
    IMG.img_modified = img_gamma_corrected
    IMG.tk_gamma_corrected_image = ImageTk.PhotoImage(Image.fromarray(img_resized))
    return IMG.img_modified
    
def image_reconstruction(img, subdiff):
    """
    Reconstructs the image by dilation.
    """
    mask = img
    marker = np.where(img <= subdiff, 0, img - subdiff)
    IMG.img_reconstructed = reconstruction(marker, mask, method='dilation', footprint=np.ones((3,) * mask.ndim))
    IMG.img_modified = cv2.normalize(IMG.img_reconstructed, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    IMG.tk_reconstructed_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_reconstructed).resize((RESIZE_WIDTH, RESIZE_HEIGHT)))
    return IMG.img_modified

def image_resampling(image, new_resolution):
    """
    Resamples the image to a desired resolution.
    """
    initial_resolution = IMG.pixel_size
    IMG.pixel_size = new_resolution
    scaling_factor = initial_resolution / new_resolution

    # Determine the new shape after rescaling
    new_height = int(image.shape[0] * scaling_factor)
    new_width = int(image.shape[1] * scaling_factor)

    # Resize the image using cv2.resize
    IMG.img_modified = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    IMG.img_original_resampled = cv2.resize(IMG.img_grey, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    # Ensure the images are in the correct dtype (uint8)
    for img in [IMG.img_modified, IMG.img_original_resampled]:
        if img.dtype in [np.float64, np.float32]:
            img = (img * 255).clip(0, 255).astype(np.uint8)

    # Convert to PhotoImage for Tkinter display
    IMG.tk_resampled_image = ImageTk.PhotoImage(Image.fromarray(IMG.img_modified).resize((RESIZE_WIDTH, RESIZE_HEIGHT)))
    return IMG.img_modified