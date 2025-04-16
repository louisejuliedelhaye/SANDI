# -*- coding: utf-8 -*-
"""
File: PCam3_characteristics class
Version: SANDI v1.0.0-beta
Created on Mon Aug 19 14:47:12 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: This file defines the PCam3_characteristics class, which stores default attributes (real-life height, width and depth) of the PCam3. 
"""

###############################################################################
# Import packages
###############################################################################

import tkinter as tk
from tkinter import *

###############################################################################
# Create PCam3_characteristics class
###############################################################################

class PCam3_characteristics:
    
    def __init__(self):
        """
        Class to store image real-life measurements (default values are from the PCam3 from Herbst Environmental Science).
        """
        self.image_height = StringVar(value="14.9")
        self.image_width = StringVar(value="22.3")
        self.image_depth = StringVar(value="0.405")
