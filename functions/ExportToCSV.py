# -*- coding: utf-8 -*-
"""
File: CSV files generation
Version: SANDI v1.0.0-beta
Created on Fri Apr 12 13:05:53 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: File containing the functions needed to save the output CSV files.
"""

###############################################################################
# Import packages
###############################################################################

import os
import sys
from tkinter import filedialog
import csv
import os
from PIL.ExifTags import TAGS, GPSTAGS
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
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

from IMG import IMG

###############################################################################
# SPM
###############################################################################

def save_particles_csv(stats, image_paths, app_instance):
    """
    Creates the CSV file containing the statistics of all the individual particles extracted in one image.
    """
    if stats:
        
        # Define the default file name using the image name
        imported_image_path = image_paths[0]
        imported_image_base_name = os.path.basename(imported_image_path)
        imported_image_name, _ = os.path.splitext(imported_image_base_name)
        default_filename = f"{imported_image_name}_particles_statistics"
        
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_filename,  filetypes=[("CSV files", "*.csv")])
        
        IMG.csv_file_path = os.path.dirname(file_path)
        
        if file_path:
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                
                fieldnames = ["Particle Number","Pixel IDs","Area um2", "Area", "Equivalent spherical diameter (um)", "Centroid", "Max Intensity", "Min Intensity", "Mean Intensity", "Major Axis Length (um)", "Minor Axis Length (um)", "Perimeter (um)", "Volume (ul)", "Euler Number", "Orientation", "Solidity", "Form Factor", "Aspect Ratio", "Sphericity", "Roundness", "Extent", "2D Fractal Dimension", "3D Fractal Dimension"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for i, prop in enumerate(stats):
                    solidity_value = str(prop.solidity).strip('[]')
                    particle_data = {
                        "Particle Number": i,
                        "Pixel IDs": prop.coords,
                        "Area": prop.area,
                        "Area um2": prop.area_um2,
                        "Equivalent spherical diameter (um)": prop.equivalent_diameter_um,
                        "Centroid": prop.centroid,
                        "Max Intensity": prop.max_intensity,
                        "Min Intensity": prop.min_intensity,
                        "Mean Intensity": prop.mean_intensity,
                        "Major Axis Length (um)": prop.major_axis_length_um,
                        "Minor Axis Length (um)": prop.minor_axis_length_um,
                        "Perimeter (um)": prop.perimeter_um,
                        "Volume (ul)": prop.volume_ul,
                        "Euler Number": prop.euler_number,
                        "Orientation": prop.orientation,
                        "Solidity": solidity_value,
                        "Form Factor": prop.form_factor,
                        "Aspect Ratio": prop.aspect_ratio,
                        "Sphericity": prop.sphericity,
                        "Roundness": prop.roundness,
                        "Extent": prop.extent,
                        "2D Fractal Dimension": prop.fractal_dimension_2D,
                        "3D Fractal Dimension": prop.fractal_dimension_3D
                    }
                    writer.writerow(particle_data)
                app_instance.log_message('success', 'CSV file containing the detailed particles measurements successfully exported')
                
    else:
        app_instance.log_message('error', "Error: No particle statistics to save")

def save_image_csv(stats, file_path, app_instance):        
    """
    Creates the CSV file containing the mean statistics and PSD of one image.
    """
    if stats:
        imported_image_path = IMG.image_paths[0]
        imported_image_base_name = os.path.basename(imported_image_path)
        imported_image_name, _ = os.path.splitext(imported_image_base_name)
        default_filename = f"{imported_image_name}_image_statistics.csv"
        
        file_path = os.path.join(IMG.csv_file_path, default_filename)
            
        if file_path:
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                
                fieldnames = ["Image Name", "Datetime", "D10", "D50", "D90", "Mean Solidity", "Mean Aspect Ratio", "Mean Form Factor", "Mean Sphericity", "Mean Roundness", "Mean Extent", "Mean Fractal Dimension 2D", "Mean Fractal Dimension 3D", "Mean Major-Axis-Length (um)",
           "Mean Minor-Axis-Length (um)", "Number of Particles", "Mean Area (um²)", "Mean Perimeter (um)", "Mean Diameter (um)",
           "Total Volume Concentration (ul/l)","1.21449578", "1.60249025", "1.891035166", "2.23134399", "2.633450968", "3.107850704", "3.666961685", "4.327133347", "5.106510257", "6.025832888", 
                      "7.111107509", "8.39172807", "9.90256593", "11.68543358", "13.78971066", "16.27318162", "19.20366522", "22.66131587", "26.74179968", "31.55729789", "37.23981168", "43.94534164", 
                      "51.85865627", "61.19717694", "72.21641829", "85.2202712", "100.5661856", "118.6746248", "140.0438222", "165.261362", "195.0198203", "230.1369158", "272.6270346", "324.2098302", 
                      "385.5523982", "458.5019084", "545.2540692", "648.4201189", "771.1053416", "917.0038168", "1090.50768", "1296.839693", "1542.211142", "1834.008179", "2181.01536", "2593.678927", 
                      "3084.421738", "3668.016358", "4362.03072", "5187.357853", "6153.251669", "7282.771116", "8629.279192", "10256.59673", "12224.88304", "14609.54506", "17494.89787"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                image_data = {
                    "Image Name": IMG.image_name,
                    "Datetime": IMG.date_time,
                    "D10": IMG.D10,
                    "D50": IMG.D50,
                    "D90": IMG.D90,
                    "Mean Solidity": IMG.mean_solidity,
                    "Mean Aspect Ratio": IMG.mean_aspect_ratio,
                    "Mean Form Factor": IMG.mean_form_factor,
                    "Mean Sphericity": IMG.mean_sphericity,
                    "Mean Roundness": IMG.mean_roundness,
                    "Mean Extent": IMG.mean_extent,
                    "Mean Fractal Dimension 2D": IMG.mean_fractal_dimension_2D,
                    "Mean Fractal Dimension 3D": IMG.mean_fractal_dimension_3D,
                    "Mean Major-Axis-Length (um)": IMG.mean_major_axis_length,
                    "Mean Minor-Axis-Length (um)": IMG.mean_minor_axis_length,
                    "Number of Particles": len(IMG.stats),
                    "Mean Area (um²)": IMG.mean_area,
                    "Mean Perimeter (um)": IMG.mean_perimeter,
                    "Mean Diameter (um)": IMG.mean_diameter,
                    "Total Volume Concentration (ul/l)": IMG.total_volume_concentration,
                    "1.21449578": IMG.volume_concentration_per_bin[0],
                    "1.60249025": IMG.volume_concentration_per_bin[1],
                    "1.891035166": IMG.volume_concentration_per_bin[2],
                    "2.23134399": IMG.volume_concentration_per_bin[3],
                    "2.633450968": IMG.volume_concentration_per_bin[4],
                    "3.107850704": IMG.volume_concentration_per_bin[5],
                    "3.666961685": IMG.volume_concentration_per_bin[6],
                    "4.327133347": IMG.volume_concentration_per_bin[7],
                    "5.106510257": IMG.volume_concentration_per_bin[8],
                    "6.025832888": IMG.volume_concentration_per_bin[9],
                    "7.111107509": IMG.volume_concentration_per_bin[10],
                    "8.39172807": IMG.volume_concentration_per_bin[11],
                    "9.90256593": IMG.volume_concentration_per_bin[12],
                    "11.68543358": IMG.volume_concentration_per_bin[13],
                    "13.78971066": IMG.volume_concentration_per_bin[14],
                    "16.27318162": IMG.volume_concentration_per_bin[15],
                    "19.20366522": IMG.volume_concentration_per_bin[16],
                    "22.66131587": IMG.volume_concentration_per_bin[17],
                    "26.74179968": IMG.volume_concentration_per_bin[18],
                    "31.55729789": IMG.volume_concentration_per_bin[19],
                    "37.23981168": IMG.volume_concentration_per_bin[20],
                    "43.94534164": IMG.volume_concentration_per_bin[21],
                    "51.85865627": IMG.volume_concentration_per_bin[22],
                    "61.19717694": IMG.volume_concentration_per_bin[23],
                    "72.21641829": IMG.volume_concentration_per_bin[24],
                    "85.2202712": IMG.volume_concentration_per_bin[25],
                    "100.5661856": IMG.volume_concentration_per_bin[26],
                    "118.6746248": IMG.volume_concentration_per_bin[27],
                    "140.0438222": IMG.volume_concentration_per_bin[28],
                    "165.261362": IMG.volume_concentration_per_bin[29],
                    "195.0198203": IMG.volume_concentration_per_bin[30],
                    "230.1369158": IMG.volume_concentration_per_bin[31],
                    "272.6270346": IMG.volume_concentration_per_bin[32],
                    "324.2098302": IMG.volume_concentration_per_bin[33],
                    "385.5523982": IMG.volume_concentration_per_bin[34],
                    "458.5019084": IMG.volume_concentration_per_bin[35],
                    "545.2540692": IMG.volume_concentration_per_bin[36],
                    "648.4201189": IMG.volume_concentration_per_bin[37],
                    "771.1053416": IMG.volume_concentration_per_bin[38],
                    "917.0038168": IMG.volume_concentration_per_bin[39],
                    "1090.50768": IMG.volume_concentration_per_bin[40],
                    "1296.839693": IMG.volume_concentration_per_bin[41],
                    "1542.211142": IMG.volume_concentration_per_bin[42],
                    "1834.008179": IMG.volume_concentration_per_bin[43],
                    "2181.01536": IMG.volume_concentration_per_bin[44],
                    "2593.678927": IMG.volume_concentration_per_bin[45],
                    "3084.421738": IMG.volume_concentration_per_bin[46],
                    "3668.016358": IMG.volume_concentration_per_bin[47],
                    "4362.03072": IMG.volume_concentration_per_bin[48],
                    "5187.357853": IMG.volume_concentration_per_bin[49],
                    "6153.251669": IMG.volume_concentration_per_bin[50],
                    "7282.771116": IMG.volume_concentration_per_bin[51],
                    "8629.279192": IMG.volume_concentration_per_bin[52],
                    "10256.59673": IMG.volume_concentration_per_bin[53],
                    "12224.88304": IMG.volume_concentration_per_bin[54],
                    "14609.54506": IMG.volume_concentration_per_bin[55],
                    "17494.89787": IMG.volume_concentration_per_bin[56]
                }
                writer.writerow(image_data)
            app_instance.log_message('success', 'CSV file containing the image mean statistics and PSD successfully exported')
    else:
        app_instance.log_message('error', "Error: No particle statistics to save")
        
##

def save_batch_particles_csv(stats, image_paths, app_instance, csv_file_path):
    """
    Creates the CSV file containing the statistics of all the individual particles extracted in one image, adapted to handle multiple images and create a separate CSV for each image.
    """
    if stats:
        
        os.makedirs(csv_file_path, exist_ok=True)
        imported_image_base_name = os.path.basename(image_paths)  
        imported_image_name, _ = os.path.splitext(imported_image_base_name)
        csv_filename = f"{imported_image_name}_particles_statistics.csv"
        file_path = os.path.join(csv_file_path, csv_filename)
        
        if file_path:
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                
                fieldnames = ["Particle Number","Pixel IDs","Area um2", "Area", "Equivalent spherical diameter (um)", "Centroid", "Max Intensity", "Min Intensity", "Mean Intensity", "Major Axis Length (um)", "Minor Axis Length (um)", "Perimeter (um)", "Volume (ul)", "Euler Number",  "Orientation", "Solidity", "Form Factor", "Aspect Ratio", "Sphericity", "Roundness", "Extent", "2D Fractal Dimension", "3D Fractal Dimension"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for i, prop in enumerate(stats):
                    particle_data = {
                        "Particle Number": i,
                        "Pixel IDs": prop.get("coords", "N/A"),
                        "Area um2": prop.get("area_um2", "N/A"),
                        "Area": prop.get("area", "N/A"),
                        "Equivalent spherical diameter (um)": prop.get("equivalent_diameter_um", "N/A"),
                        "Centroid": prop.get("centroid", "N/A"),
                        "Max Intensity": prop.get("max_intensity", "N/A"),
                        "Min Intensity": prop.get("min_intensity", "N/A"),
                        "Mean Intensity": prop.get("mean_intensity", "N/A"),
                        "Major Axis Length (um)": prop.get("major_axis_length_um", "N/A"),
                        "Minor Axis Length (um)": prop.get("minor_axis_length_um", "N/A"),
                        "Perimeter (um)": prop.get("perimeter_um", "N/A"),
                        "Volume (ul)": prop.get("volume_ul", "N/A"),
                        "Euler Number": prop.get("euler_number", "N/A"),
                        "Orientation": prop.get("orientation", "N/A"),
                        "Solidity": prop.get("solidity", "N/A"),
                        "Form Factor": prop.get("form_factor", "N/A"),
                        "Aspect Ratio": prop.get("aspect_ratio", "N/A"),
                        "Sphericity": prop.get("sphericity", "N/A"),
                        "Roundness": prop.get("roundness", "N/A"),
                        "Extent": prop.get("extent", "N/A"),
                        "2D Fractal Dimension": prop.get("fractal_dimension_2D", "N/A"), 
                        "3D Fractal Dimension": prop.get("fractal_dimension_3D", "N/A")
                    }
                    writer.writerow(particle_data)

    else:
        app_instance.log_message('error', "Error: No particle statistics to save")  
        
# Graphs

def save_single_image_PSD_figure(csv_file_path, app_instance):
    """
    Saves the PSD graph in the 'statistics' output directory.
    """  
    if csv_file_path:
        try:
            csv_file_path = csv_file_path.replace("\\", "/")
            imported_image_path = IMG.image_paths[0]
            imported_image_base_name = os.path.basename(imported_image_path)
            imported_image_name, _ = os.path.splitext(imported_image_base_name)
            csv_path = (os.path.join(csv_file_path, f"{imported_image_name}_image_statistics.csv"))
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
               
            csv_particles_path = (os.path.join(csv_file_path, f"{imported_image_name}_particles_statistics.csv"))
            csv_particles_path = csv_particles_path.replace("\\", "/")
            final_df = pd.read_csv(csv_particles_path)
            
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
            number_of_particles = len(final_df['Equivalent spherical diameter (um)'])
            
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
                f"N = {number_of_particles} particles"
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
            
            jpg_path = os.path.join(csv_file_path, f"{imported_image_name}_particle_size_distribution.jpg")
            fig.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            app_instance.log_message('success', 'PSD figure successfully exported')
            
        except Exception as e:
            app_instance.log_message('error', f'Error during the PSD figure export: {e}') 
    
def save_single_image_spiderchart_figure(csv_file_path, app_instance):
    """
    Saves the spider graph in the 'statistics' output directory.
    """  
    if csv_file_path:
        try:
            csv_file_path = csv_file_path.replace("\\", "/")
            imported_image_path = IMG.image_paths[0]
            imported_image_base_name = os.path.basename(imported_image_path)
            imported_image_name, _ = os.path.splitext(imported_image_base_name)
            csv_path = (os.path.join(csv_file_path, f"{imported_image_name}_image_statistics.csv"))
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
        
                jpg_path = os.path.join(csv_file_path, f"{imported_image_name}_mean_shape_indicators.jpg")
                fig.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor='white')
                plt.close(fig)
                
                app_instance.log_message('success', 'Shape indicators figure successfully exported')
        
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise  
                
        except Exception as e:
            app_instance.log_message('error', f'Error during the shape indicators figure export: {e}') 
        
###############################################################################
# Gravels
###############################################################################

def save_gravels_csv(stats, image_paths, app_instance):
    """
    Creates the CSV file containing the statistics of all the individual gravels extracted in one image.
    """
    if stats:
        
        # Define the default file name using the image name
        imported_image_path = image_paths[0]
        imported_image_base_name = os.path.basename(imported_image_path)
        imported_image_name, _ = os.path.splitext(imported_image_base_name)
        default_filename = f"{imported_image_name}_gravels_statistics"
        
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_filename,  filetypes=[("CSV files", "*.csv")])
        
        if file_path:
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["Stone Number","Pixel IDs", "Area (pix)", "Area (cm2)", "Perimeter (cm)", "Equivalent Spherical Diameter (cm)", "Centroid", "Major Axis Length (cm)", "Minor Axis Length (cm)", "Solidity", "Form Factor", "Aspect Ratio", "Extent", "Roundness", "Sphericity", "Type"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for i, prop in enumerate(stats):
                    #convexity_value = str(prop.convexity).strip('[]')
                    particle_data = {
                        "Stone Number": i,
                        "Pixel IDs": prop.coords,
                        "Area (pix)": prop.area,
                        "Area (cm2)": prop.area_cm2,
                        "Perimeter (cm)": prop.perimeter_cm,
                        "Equivalent Spherical Diameter (cm)": prop.equivalent_diameter_cm,
                        "Centroid": prop.centroid,
                        "Major Axis Length (cm)": prop.major_axis_length_cm,
                        "Minor Axis Length (cm)": prop.minor_axis_length_cm,
                        "Solidity": prop.solidity,
                        "Form Factor": prop.form_factor,
                        "Aspect Ratio": prop.aspect_ratio,
                        "Extent": prop.extent,
                        "Roundness": prop.roundness,
                        "Sphericity": prop.sphericity,
                        "Type": prop.type
                    }
                    writer.writerow(particle_data)
                app_instance.log_message('success', 'CSV file containing the detailed gravels measurements successfully exported')
                
    else:
        app_instance.log_message('error', "Error: No gravel statistics to save")

def save_sample_csv(stats, app_instance):     
    """
    Creates the CSV file containing the mean statistics and PSD of one image containing gravels. It also classifies gravels based on the GRADISTAT classification.
    """
    if stats:
        
        imported_image_path = IMG.image_paths[0]
        imported_image_base_name = os.path.basename(imported_image_path)
        imported_image_name, _ = os.path.splitext(imported_image_base_name)
        default_filename = f"{imported_image_name}_sample_statistics"
        
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_filename,  filetypes=[("CSV files", "*.csv")])
            
        if file_path:
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                
                fieldnames = ["Image Name", "Datetime", "Number of Stones", "Mean Area (cm2)", "Mean Perimeter (cm)", "Mean Equivalent Spherical Diameter (cm)", "Mean Major Axis Length (cm)", "Mean Minor Axis Length (cm)", "Mean Solidity", "Mean Aspect Ratio", "Mean Form Factor", "Mean Sphericity", "Mean Roundness", "Mean Extent", "Sorting", "Skewness", "Kurtosis"
           ]
                
                class_labels = [
    "sands", "very fine gravels", "fine gravels", "medium gravels", "coarse gravels",
    "very coarse gravels", "very small boulders", "small boulders", "medium boulders", "large boulders"
]
                fieldnames.extend(class_labels)

                bin_edges = np.arange(0.1, 51.3, 0.1)
                for size_class in bin_edges:
                    fieldnames.append(f"Major_{size_class:.1f} cm")
                    fieldnames.append(f"Minor_{size_class:.1f} cm")
        
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                image_data = {
                    "Image Name": IMG.image_name,
                    "Datetime": IMG.date_time,
                    "Number of Stones": len(IMG.stats),
                    "Mean Area (cm2)": IMG.mean_area,
                    "Mean Perimeter (cm)": IMG.mean_perimeter,
                    "Mean Equivalent Spherical Diameter (cm)": IMG.mean_equivalent_diameter_cm,
                    "Mean Major Axis Length (cm)": IMG.mean_major_axis_length,
                    "Mean Minor Axis Length (cm)": IMG.mean_minor_axis_length,
                    "Mean Solidity": IMG.mean_solidity,
                    "Mean Aspect Ratio": IMG.mean_aspect_ratio,
                    "Mean Form Factor": IMG.mean_form_factor,
                    "Mean Sphericity": IMG.mean_sphericity,
                    "Mean Roundness": IMG.mean_roundness,
                    "Mean Extent": IMG.mean_extent,
                    "Sorting": IMG.sorting,
                    "Skewness": IMG.skewness,
                    "Kurtosis": IMG.kurtosis
                }
                
                class_counts = {label: 0 for label in class_labels}
                
                classification = [
                    ("sands", 0, 0.2),
                    ("very fine gravels", 0.2, 0.4),
                    ("fine gravels", 0.4, 0.8),
                    ("medium gravels", 0.8, 1.6),
                    ("coarse gravels", 1.6, 3.2),
                    ("very coarse gravels", 3.2, 6.4),
                    ("very small boulders", 6.4, 12.8),
                    ("small boulders", 12.8, 25.6),
                    ("medium boulders", 25.6, 51.2),
                    ("large boulders", 51.2, 100)
                ]
                
                # Count gravels per class
                for prop in IMG.stats:
                    diameter = prop.equivalent_diameter_cm
                    category = next(
                        (cls for cls, lower, upper in classification if lower <= diameter < upper),
                        "unclassified"  
                    )
                    class_counts[category] += 1
                    
                image_data.update(class_counts)

                for size_class in bin_edges:
                    key_major = f"Major_{size_class:.1f} cm"
                    key_minor = f"Minor_{size_class:.1f} cm"

                    idx = int(size_class * 10)
                    
                    if idx < len(IMG.major_axis_count):
                        image_data[key_major] = int(IMG.major_axis_count[idx])
                    
                    if idx < len(IMG.minor_axis_count):
                        image_data[key_minor] = int(IMG.minor_axis_count[idx])
                
                writer.writerow(image_data)
                
            app_instance.log_message('success', 'CSV file containing the mean sample statistics successfully exported')
            
            save_gradistat_figure(file_path, imported_image_name)
    else:
        app_instance.log_message('error', "Error: No gravel statistics to save")
        
def save_gradistat_figure(csv_file_path, image_name):
    """
    Creates the output figures for the gravel extraction.
    """

    csv_file_path = csv_file_path.replace("\\", "/")
    df = pd.read_csv(csv_file_path)
    
    directory = os.path.dirname(csv_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Save the figure in JPG in the same folder as the CSV file
    gravel_csv_path = os.path.join(directory, f"{image_name}_gravels_statistics.csv")
    df2 = pd.read_csv(gravel_csv_path)
    
    
    # Define sediment classes and their colors
    sediment_classes = [
        "sand", "very fine gravel", "fine gravel", "medium gravel", "coarse gravel",
        "very coarse gravel", "very small boulder", "small boulder", "medium boulder", "large boulder"
    ]
    
    sediment_colors = {
        "sand": "navajowhite",               
        "very fine gravel": "burlywood",  
        "fine gravel": "#B1916E",        
        "medium gravel": "#E5CC77",      
        "coarse gravel": "#DAA520",      
        "very coarse gravel": "#D2691E", 
        "very small boulder": "#8B4513", 
        "small boulder": "#A52A2A",      
        "medium boulder": "#4B0101",     
        "large boulder": "#280137"       
    }
       
    class_counts = {
        "sand": df["sands"].sum(),
        "very fine gravel": df["very fine gravels"].sum(),
        "fine gravel": df["fine gravels"].sum(),
        "medium gravel": df["medium gravels"].sum(),
        "coarse gravel": df["coarse gravels"].sum(),
        "very coarse gravel": df["very coarse gravels"].sum(),
        "very small boulder": df["very small boulders"].sum(),
        "small boulder": df["small boulders"].sum(),
        "medium boulder": df["medium boulders"].sum(),
        "large boulder": df["large boulders"].sum()
    }
    
    class_counts = {cls: class_counts.get(cls, 0) for cls in sediment_classes}
    
    total_count = sum(class_counts.values())
    if total_count == 0:
        print("No sediment data available to plot.")
        return
    
    percentages = {cls: (count / total_count) * 100 for cls, count in class_counts.items()}
    
    # Stack figure
    
    fig, ax = plt.subplots(figsize=(5, 5), dpi=300)
    
    bottom = 0 
    legend_labels = [] 
    for cls in sediment_classes:
        plt.bar("Sediment distribution", percentages[cls], bottom=bottom, color=sediment_colors[cls], label=cls)
        bottom += percentages[cls]
        legend_labels.append(f"{cls} ({percentages[cls]:.1f}%)")
    
    plt.ylabel("Percentage of total stones (%)")
    plt.title("")
    plt.ylim(0, 100)  
    handles, labels = ax.get_legend_handles_labels()
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], legend_labels[::-1], title="GRADISTAT classification", bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
    plt.xticks([])  
    ax.set_aspect('auto') 
    ax.margins(0, 0) 
    ax.yaxis.set_major_locator(plt.MultipleLocator(10)) 
    ax.yaxis.set_minor_locator(plt.MultipleLocator(2))   
    ax.grid(True, which='major', linestyle='-', linewidth=0.8, alpha=0.7)  
    ax.grid(True, which='minor', linestyle='--', linewidth=0.5, alpha=0.5)  
    plt.tight_layout()
    
    directory = os.path.dirname(csv_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    jpg_path = os.path.join(directory, f"{image_name}_gravel_type_classification.jpg")
    jpg_path = jpg_path.replace("\\", "/")
    fig.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    # PSD figure
    
    def plot_sediment_classes(ax, classification, sediment_colors):
        x_min, x_max = ax.get_xlim()
        y_top = ax.get_ylim()[1]    
        for label, min_size, max_size in classification:
            ax.hlines(y=y_top, xmin=min_size, xmax=max_size, 
                      colors=sediment_colors[label], linewidth=8, alpha=1)
            if label == "large boulder":
                continue
            multiline_label = "\n".join(label.split())
            label_x = (min_size + max_size) / 2  
            label_y = y_top + 0.5 
            ax.text(label_x, label_y, multiline_label, fontsize=6, ha='center', va='bottom',
                    bbox=dict(facecolor='white', edgecolor='none', alpha=1))
            
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
    ("large boulder", 51.2, 60)
]

    major_columns = [col for col in df.columns if 'Major_' in col]
    minor_columns = [col for col in df.columns if 'Minor_' in col]
    
    modified_major_columns = [col.replace('Major_', '').replace(' cm', '') for col in major_columns]
    modified_minor_columns = [col.replace('Minor_', '').replace(' cm', '') for col in minor_columns]
    
    major_data = df[major_columns].copy()
    minor_data = df[minor_columns].copy()
    
    major_data.columns = pd.to_numeric(modified_major_columns, errors='coerce')
    minor_data.columns = pd.to_numeric(modified_minor_columns, errors='coerce')
    
    major_axis_distribution = major_data.div(df['Number of Stones'], axis=0) * 100  
    minor_axis_distribution = minor_data.div(df['Number of Stones'], axis=0) * 100  
    
    station_major = major_axis_distribution.sum().sort_index()
    station_minor = minor_axis_distribution.sum().sort_index()
    
    station_major.index = station_major.index.astype(float)
    station_minor.index = station_minor.index.astype(float)
    station_minor = station_minor.rename(index={0.15: 0.2})
    
    bin_edges = np.arange(0, df2["Equivalent Spherical Diameter (cm)"].max() + 0.1, 0.1)
    binned_data = pd.cut(df2["Equivalent Spherical Diameter (cm)"], bins=bin_edges, right=False)
    
    # Count the occurrences in each bin
    binned_counts = binned_data.value_counts().sort_index()
    
    # Calculate total number of stones
    total_stones = len(df2)
    
    # Convert the bin counts to percentages
    binned_percentages = (binned_counts / total_stones) * 100
    
    # Extract the midpoints of each bin
    bin_midpoints = [interval.mid for interval in binned_counts.index]
    

    fig, ax = plt.subplots(figsize=(6, 4), dpi=300)

    ax.set_xscale("log")

    ax.fill_between(bin_midpoints, binned_percentages.values, color='steelblue', alpha=1, label="Equivalent spherical diameter")
    ax.plot(station_major.index, station_major.values, color='darkblue', linewidth=0.5, linestyle='-', label="Major axis")
    ax.plot(station_minor.index, station_minor.values, color='darkblue', linestyle='--', linewidth=0.3, label="Minor axis")

    ax.set_xticks([0.1, 0.2, 0.3, 0.5, 1, 2, 5, 10, 20, 50])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter()) 

    ax.set_xlabel('Length (cm)', fontsize=11)
    ax.set_ylabel('Percentage of total stones (%)', fontsize=11)
    ax.set_xlim(0, 60)
    ax.set_ylim(0, max(station_minor.values.max(), station_major.values.max())+1)

    ax.legend(loc='upper right', frameon=False, fontsize=8, title="")

    ax.grid(True, which='major', linestyle='--', color='lightgrey', alpha=0.7)
    ax.minorticks_on()
    ax.grid(True, which='minor', linestyle=':', color='lightgrey', alpha=0.5)
    
    plot_sediment_classes(ax, classification, sediment_colors)

    plt.tight_layout()

    jpg_path = os.path.join(directory, f"{image_name}_size_distribution.jpg")
    jpg_path = jpg_path.replace("\\", "/")
    fig.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    # Shape indicators figure
    
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
    
    jpg_path = os.path.join(directory, f"{image_name}_shape_indicators.jpg").replace("\\", "/")
    fig.savefig(jpg_path, format='jpg', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)