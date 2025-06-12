# -*- coding: utf-8 -*-
"""
File: IMG class
Version: SANDI v1.0.0-beta
Created on Mon Aug 19 15:08:27 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: This file defines the IMG class, which stores attributes needed for (or creating during)
             the processing (image metadata, calculated statistics). 
"""

###############################################################################
# Import packages
###############################################################################

import pandas as pd

###############################################################################
# Create IMG class
###############################################################################

class IMG:
    """
    Class to store image metadata, attributes and derived statistics.
    """
    image_height= 0
    image_width = 0
    image_depth = 0
    image_background = None
    
    filename = None
    selected_image = None
    image_name = None
    date_time = None
    tk_resized_image = None
    image_paths = []
    pixel_size = 0.0
    pixel_sizes = 0.0
    exif_data = None
    focal_length = None
    camera = None
    aperture = None
    height = None
    width = None
    lens = None
    iso = None
    exposure = None
    img_original = None
    tk_image = None
    img_grey = None
    img_modified = None
    img_binary = None
    img_original_resampled = None
    particles = []
    batch_results_df = []
    
    tk_denoised_image = None
    tk_stretched_image = None
    tk_corrected_image = None
    img_reconstructed = None
    tk_reconstructed_image = None
    tk_binary_image = None
    extracted_particles_image = None
    tk_extracted_particles_image = None
    tk_extracted_intensity_image = None
    tk_gamma_corrected_image = None
    tk_resampled_image = None
    img_original_resampled = None
    
    stats = []
    
    volume_per_bin = pd.DataFrame
    bin_edges = []
    volume_concentration_per_bin = []
    total_volume_concentration = None
    mean_diameter = None
    diameter_standard_deviation = None
    mean_area = None
    mean_perimeter = None
    mean_major_axis_length = None
    mean_minor_axis_length = None
    mean_aspect_ratio = None
    mean_solidity = None
    mean_form_factor = None
    mean_circularity = None
    mean_irregularity = None
    mean_sphericity = None
    mean_roundness = None
    mean_extent = None
    
    D10 = None
    D50 = None
    D90 = None

    major_axis_count = []
    minor_axis_count = []
    eq_diameter_histogram = None
    cdf = []
    
    csv_file_path = None