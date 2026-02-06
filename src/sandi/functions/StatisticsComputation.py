# -*- coding: utf-8 -*-
"""
File: Statistics computation
Version: SANDI v1.0.0-beta
Created on Fri Apr 12 13:39:41 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: File containing the functions needed to compute the statistics from extracted particles.
"""

############################
# Import required packages #
############################

import concurrent.futures
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
import pandas as pd
from skimage.morphology import convex_hull_image
from functools import partial
import os
import sys
from scipy.stats import skew, kurtosis
from importlib import resources

###############################################################################
# Import local packages
###############################################################################

from sandi.attributes.IMG import IMG

###############################################################################
# SPM
###############################################################################

def compute_image_statistics(app_instance, stats, image_height, image_width, image_depth):
    """
    Computes PSD and mean particle statistics per image (SPM).
    """
    if stats is not None: 
        
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
        
        bin_edges = bins[:, 0]
        midpoints = np.sqrt(bin_edges[1:] * bin_edges[:-1]) 
        IMG.bin_edges = bin_edges.flatten()
        
        #######################################################################
        ## 2 ## Assign each particle to its corresponding bin
        #######################################################################
        
        EqDiameter = np.array([prop.equivalent_diameter_um for prop in stats]) 
        BinInd = np.digitize(EqDiameter, bin_edges) - 1 
        BinInd = BinInd[BinInd >= 0]
        particles_per_bin = np.bincount(BinInd)
        particles_per_bin = np.pad(particles_per_bin, (0, len(midpoints) - len(particles_per_bin)), 'constant')

        #######################################################################
        ## 3 ## Calculate the total volume per bin
        #######################################################################
        
        volume_ul = np.array([prop.volume_ul for prop in stats]) 
        volume_per_bin = np.zeros((len(midpoints),)) 
        volume_per_bin[:len(np.bincount(BinInd, weights=volume_ul))] = np.bincount(BinInd, weights=volume_ul) 
        
        IMG.volume_per_bin = pd.DataFrame({
            'Particle Size': midpoints.flatten(), 
            'Total Volume': volume_per_bin,
            'Particle Count': particles_per_bin
        })
        
        #######################################################################
        ## 4 ## Calculate volume concentration per size class
        #######################################################################
        
        IMG.volume_concentration_per_bin = volume_per_bin
        app_instance.log_message('error', f"image_height: {image_height}, image_width: {image_width}, image_depth: {image_depth}")
        IMG.volume_concentration_per_bin /= (image_height * image_width * image_depth * 10**-6) # scale volumes per bins (µL) relative to the total image volume (mm³) - giving volume concentration in µL/L
        IMG.volume_concentration_per_bin = np.array(IMG.volume_concentration_per_bin).flatten()
        IMG.total_volume_concentration = np.sum(IMG.volume_concentration_per_bin) # calculate total volume concentration
        
        #######################################################################
        ## 4 ## Calculate the cumulative volume distribution
        #######################################################################
        
        cumulative_volume = np.cumsum(IMG.volume_concentration_per_bin)
        IMG.cdf = (cumulative_volume / cumulative_volume[-1]) * 100
        
        #######################################################################
        ## 5 ## Calculate D10, D50, D90 (volume-based)
        #######################################################################
        
        freq_n, bin_edges = np.histogram(EqDiameter, bins=bin_edges)
        freq = freq_n / np.sum(freq_n) 

        IMG.cdf = IMG.cdf.flatten()
        midpoints = midpoints.flatten()

        # D10, D50, D90
        IMG.D10 = np.interp(10, IMG.cdf, midpoints)
        IMG.D50 = np.interp(50, IMG.cdf, midpoints)
        IMG.D90 = np.interp(90, IMG.cdf, midpoints)
        
        #######################################################################
        ## 6 ## Calculate volume weighted mean diameter weighted by volume and by surface area, volume moment mean diameter, Sauter diameter
        #######################################################################
        
        # Mean diameter weighted by volume 
        diameters = np.array([prop.equivalent_diameter_um for prop in stats])
        volumes = np.array([prop.volume_ul for prop in stats])
        IMG.mean_diameter = np.sum(volumes * diameters) / np.sum(volumes)
        
        # Mean diameter weighted by surface area
        if len(diameters) > 0:
            surface_areas = np.pi * diameters**2
            IMG.mean_diameter_surface = np.sum(surface_areas * diameters) / np.sum(surface_areas)
        else:
            IMG.mean_diameter_surface = None
        
        # Sauter diameter
        if len(diameters) > 0:
            IMG.Sauter_diameter = np.sum(diameters**3) / np.sum(diameters**2)
        else:
            IMG.Sauter_diameter = None
            
        # Volume moment mean diameter
        if len(diameters) > 0:
            IMG.volume_moment_mean = np.sum(diameters**4) / np.sum(diameters**3)
        else:
            IMG.volume_moment_mean = None
            
        # Specific Surface Area    
        if IMG.Sauter_diameter is not None and IMG.Sauter_diameter > 0:
            IMG.SSA = 6 / IMG.Sauter_diameter  # µm²/µm³
        else:
            IMG.SSA = None
                    
        #######################################################################
        ## 7 ## Calculate mean shape descriptors
        #######################################################################
        
        # Area
        areas = np.array([prop.area_um2 for prop in stats])
        IMG.mean_area = np.nanmean(areas)
        
        # Perimeter
        perimeters = np.array([prop.perimeter_um for prop in stats])
        IMG.mean_perimeter = np.nanmean(perimeters)
        
        # Major axis length
        major_axis_lengths = np.array([prop.major_axis_length_um for prop in stats])
        IMG.mean_major_axis_length = np.nanmean(major_axis_lengths)
        
        # Minor axis length
        minor_axis_lengths = np.array([prop.minor_axis_length_um for prop in stats])
        IMG.mean_minor_axis_length = np.nanmean(minor_axis_lengths)
        
        # Aspect ratio
        aspect_ratios = np.array([prop.aspect_ratio for prop in stats])
        IMG.mean_aspect_ratio = np.nanmean(aspect_ratios)
        
        # Solidity
        solidities = np.array([prop.solidity for prop in stats])
        IMG.mean_solidity = np.nanmean(solidities)
        
        # Form Factor
        form_factors = np.array([prop.form_factor for prop in stats])
        IMG.mean_form_factor = np.nanmean(form_factors)
        
        # Sphericity
        sphericities = np.array([prop.sphericity for prop in IMG.stats if isinstance(prop.sphericity, (int, float))])
        IMG.mean_sphericity = np.nanmean(sphericities)
        
        # Roundness
        roundnesses = np.array([prop.roundness for prop in IMG.stats if isinstance(prop.roundness, (int, float))])
        IMG.mean_roundness = np.nanmean(roundnesses)
        
        # Extent
        extents = np.array([prop.extent for prop in stats])
        IMG.mean_extent = np.nanmean(extents)
        
        # Fractal Dimension 2D
        fractal_dim_2D = np.array([prop.fractal_dimension_2D for prop in stats])
        IMG.mean_fractal_dimension_2D = np.nanmean(fractal_dim_2D)
        
        # Fractal Dimension 3D
        fractal_dim_3D = np.array([prop.fractal_dimension_3D for prop in stats])
        IMG.mean_fractal_dimension_3D = np.nanmean(fractal_dim_3D)

        # Maximum Feret diameter
        ferets = np.array([prop.max_feret_diameter for prop in stats])
        IMG.mean_feret = np.nanmean(ferets)
        
        # Kurtosis
        kurtosiss = np.array([prop.kurtosis for prop in stats if prop.kurtosis is not None])
        IMG.mean_kurtosis = np.nanmean(kurtosiss) if kurtosiss.size > 0 else np.nan
        
        # Skewness
        skewnesss = np.array([prop.skewness for prop in stats if prop.skewness is not None])
        IMG.mean_skewness = np.nanmean(skewnesss) if skewnesss.size > 0 else np.nan
        
        # Mean Intensity
        mean_intensities = np.array([prop.mean_intensity_original for prop in stats if prop.mean_intensity_original is not None])
        IMG.mean_mean_intensity = np.nanmean(mean_intensities) if mean_intensities.size > 0 else np.nan
        
        #######################################################################
        ## 8 ## Print image statistics
        #######################################################################
        
        app_instance.log_message('success', "Image statistics successfully computed:")
        app_instance.log_message('info', f"Total volume concentration: {IMG.total_volume_concentration:.2f} µL/L\nMean diameter: {IMG.mean_diameter:.2f} µm\nD10: {IMG.D10:.2f} µm; D50: {IMG.D50:.2f} µm; D90: {IMG.D90:.2f} µm\nMean particle area: {IMG.mean_area:.0f} µm²; mean particle perimeter: {IMG.mean_perimeter:.0f} µm\nMean major axis length: {IMG.mean_major_axis_length:.0f} µm; mean minor axis length: {IMG.mean_minor_axis_length:.0f} µm\nMean aspect ratio: {IMG.mean_aspect_ratio:.2f}; mean solidity: {IMG.mean_solidity:.2f}; mean form factor: {IMG.mean_form_factor:.2f}; mean sphericity: {IMG.mean_sphericity:.2f}; mean roundness: {IMG.mean_roundness:.2f}; mean extent: {IMG.mean_extent:.2f}; mean fractal dimension 2D: {IMG.mean_fractal_dimension_2D:.2f}; mean fractal dimension 3D: {IMG.mean_fractal_dimension_3D:.2f}; mean mean intensity: {IMG.mean_mean_intensity:.2f}; mean kurtosis: {IMG.mean_kurtosis:.2f}; mean skewness: {IMG.mean_skewness:.2f}")
    
    else:
        app_instance.log_message('error', "Statistics couldn't be computed for this image")
        
###############################################################################
# Gravels
###############################################################################
        
def process_stone(prop, pixelsize):
    """
    Computes individual gravel measurements.
    """
    # Convert units to cm and add computed properties directly to prop
    prop.area_cm2 = prop.area * pixelsize**2
    prop.equivalent_diameter_cm = prop.equivalent_diameter * pixelsize
    prop.major_axis_length_cm = prop.major_axis_length * pixelsize
    prop.minor_axis_length_cm = prop.minor_axis_length * pixelsize
    prop.perimeter_cm = prop.perimeter * pixelsize
    prop.max_feret_diameter = prop.feret_diameter_max * pixelsize
        
   # Aspect Ratio 
    if prop.major_axis_length_cm > 0:
        prop.aspect_ratio = prop.minor_axis_length_cm / prop.major_axis_length_cm
    else:
        prop.aspect_ratio = None

    # Form Factor
    if prop.perimeter > 0:
        prop.form_factor = (4 * np.pi * prop.area) / (prop.perimeter ** 2)
    else:
        prop.form_factor = None

    # Sphericity
    if prop.area_cm2 > 0 and prop.perimeter_cm > 0:
        ideal_circle_perimeter = 2 * np.sqrt(np.pi * prop.area_cm2)
        prop.sphericity = ideal_circle_perimeter / prop.perimeter_cm
    else:
        prop.sphericity = None
        
    # Roundness
    if prop.area_cm2 > 0 and prop.major_axis_length_cm > 0:
        prop.roundness = (4 * prop.area_cm2) / (np.pi * (prop.max_feret_diameter**2))
    else:
        prop.roundness = None
        
    # Classification table
    classification = [
        ("sand", 0, 0.2),
        ("very fine gravel", 0.2, 0.4),
        ("fine gravel", 0.4, 0.8),
        ("medium gravel", 0.8, 1.6),
        ("coarse gravel", 1.6, 3.2),
        ("very coarse gravel", 3.2, 6.4),
        ("very small boulder", 6.4, 12.8),
        ("small boulder", 12.8, 25.6),
        ("medium boulder", 25.6, 51.2),
        ("large boulder", 51.2, 100)
    ]

    # Assign gravel class based on major_axis_length_cm
    prop.type = next(
        (cls for cls, lower, upper in classification if lower <= prop.major_axis_length_cm < upper),
        "unclassified" 
    )

    return prop

def stones_sample_statistics(prop, app_instance):
    """
    Computes PSD and mean particle statistics per image (gravels).
    """
    # Area
    areas = np.array([prop.area_cm2 for prop in IMG.stats])
    IMG.mean_area = np.nanmean(areas)
    
    # Perimeter
    perimeters = np.array([prop.perimeter_cm for prop in IMG.stats])
    IMG.mean_perimeter = np.nanmean(perimeters)
    
    # Equivalent diameter
    equivalent_diameters = np.array([prop.equivalent_diameter_cm for prop in IMG.stats])
    IMG.mean_equivalent_diameter_cm = np.nanmean(equivalent_diameters)
    
    # Major axis length
    major_axis_lengths = np.array([prop.major_axis_length_cm for prop in IMG.stats])
    IMG.mean_major_axis_length = np.nanmean(major_axis_lengths)
    
    # Minor axis length
    minor_axis_lengths = np.array([prop.minor_axis_length_cm for prop in IMG.stats])
    IMG.mean_minor_axis_length = np.nanmean(minor_axis_lengths)
    
    # Aspect Ratio
    aspect_ratios = np.array([prop.aspect_ratio for prop in IMG.stats if isinstance(prop.aspect_ratio, (int, float))])
    aspect_ratios = aspect_ratios[~np.isnan(aspect_ratios)]
    IMG.mean_aspect_ratio = np.nanmean(aspect_ratios)
    
    # Form Factor
    form_factors = np.array([prop.form_factor for prop in IMG.stats if isinstance(prop.form_factor, (int, float))])
    form_factors = form_factors[~np.isnan(form_factors)]
    IMG.mean_form_factor = np.nanmean(form_factors)
    
    # Solidity
    solidities = np.array([prop.solidity for prop in IMG.stats if isinstance(prop.solidity, (int, float))])
    solidities = solidities[~np.isnan(solidities)]
    IMG.mean_solidity = np.nanmean(solidities)
    
    # Extent
    extents = np.array([prop.extent for prop in IMG.stats if isinstance(prop.extent, (int, float))])
    extents = extents[~np.isnan(extents)]
    IMG.mean_extent = np.nanmean(extents)
    
    # Roundness
    roundnesses = np.array([prop.roundness for prop in IMG.stats if isinstance(prop.roundness, (int, float))])
    roundnesses = roundnesses[~np.isnan(roundnesses)]
    IMG.mean_roundness = np.nanmean(roundnesses)
    
    # Sphericity
    sphericities = np.array([prop.sphericity for prop in IMG.stats if isinstance(prop.sphericity, (int, float))])
    sphericities = sphericities[~np.isnan(sphericities)]
    IMG.mean_sphericity = np.nanmean(sphericities)
    
    bin_size = 0.1  
    num_bins = int(51.2 / bin_size) + 1  
    
    major_axis_count = np.zeros(num_bins)
    minor_axis_count = np.zeros(num_bins)
    
    # Count particles per size class for major axis lengths
    for length in major_axis_lengths:
        if 0 <= length <= 51.2:
            index = int(length // bin_size)  
            major_axis_count[index] += 1  
    
    # Count particles per size class for minor axis lengths
    for length in minor_axis_lengths:
        if 0 <= length <= 51.2:
            index = int(length // bin_size)
            minor_axis_count[index] += 1  
    
    IMG.major_axis_count = major_axis_count
    IMG.minor_axis_count = minor_axis_count
    
    # Sorting 
    sortings = np.std(equivalent_diameters)
    IMG.sorting = sortings
    
    # Skewness 
    skewnesses = skew(equivalent_diameters, nan_policy='omit')
    IMG.skewness = skewnesses
    
    # Kurtosis 
    kurtosises = kurtosis(equivalent_diameters, nan_policy='omit')
    IMG.kurtosis = kurtosises

    app_instance.log_message('success', "Statistics computation has been successfully completed.")
    app_instance.log_message('info', f"Mean area of the processed sample: {IMG.mean_area:.0f} cm²\nMean perimeter of the processed sample: {IMG.mean_perimeter:.0f} cm\nMean equivalent spherical diameter: {IMG.mean_equivalent_diameter_cm:.2f} cm\nMean major axis length of the processed sample: {IMG.mean_major_axis_length:.2f} cm\nMean minor axis length of the processed sample: {IMG.mean_minor_axis_length:.2f} cm\nMean aspect ratio of the processed sample: {IMG.mean_aspect_ratio:.2f}\nMean form factor of the processed sample: {IMG.mean_form_factor:.2f}\nMean solidity of the processed sample: {IMG.mean_solidity:.2f}\nMean extent of the processed sample: {IMG.mean_extent:.2f}\nMean roundness of the processed sample: {IMG.mean_roundness:.2f}\nMean sphericity of the processed sample: {IMG.mean_sphericity:.2f}\nSorting of the processed sample: {IMG.sorting:.2f}\nSkewness of the processed sample: {IMG.skewness:.2f}\nKurtosis of the processed sample: {IMG.kurtosis:.2f}")
        
def compute_stones_statistics(app_instance, stats, pixelsize):
    """
    Performs the 'process_stone' function in parallel for faster processing.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        process_with_pixelsize = partial(process_stone, pixelsize=pixelsize)
        results = list(executor.map(process_with_pixelsize, stats))

    for i, prop in enumerate(results):
        stats[i] = prop

    stones_sample_statistics(stats, app_instance)
    