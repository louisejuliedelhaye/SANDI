# -*- coding: utf-8 -*-
"""
File: main file
Version: SANDI v1.0.0-alpha
Created on Mon Aug 19 14:37:38 2024
Author: Louise Delhaye, Royal Belgian Institute of Natural Sciences
Description: Main application file for the SANDI software. This file initializes the GUI, 
             sets up the window, and manages the navigation between different 
             processing pages: homepage, single image processing, batch processing, 
             and single gravel processing.
"""

###############################################################################
# Import packages
###############################################################################

import tkinter as tk
import os
import sys
import win32gui
import win32con
import ctypes
from tkinter import ttk
import importlib.resources

###############################################################################
# Import local packages
###############################################################################

from sandi.pages.homepage import Homepage
from sandi.pages.singleimageprocessingpage import SingleImageProcessing
from sandi.pages.batchprocessingpage import BatchProcessing
from sandi.pages.singlestoneprocessingpage import SingleStoneProcessing

###############################################################################
# Software setup
###############################################################################

class App:
    
    def __init__(self, root):
        """
        Initializes the application with the main Tkinter window.
        """
        self.root = root
        self._initialize_window()
        self.show_homepage() 

    def _initialize_window(self):
        """
        Initializes the main application window and its style.
        """
        self.root.title("SANDI")
        window_width = 1474
        window_height = 786
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(background="#2c3e50")
        self.root.resizable(False, False)
        
        if getattr(sys, 'frozen', False):
            print('running in a PyInstaller bundle')
            icon_path = os.path.join(sys._MEIPASS, 'logo.png')
            self.root.iconphoto(False, tk.PhotoImage(file=icon_path))
        else:
            print('Running in a normal Python process')
            logo_res = importlib.resources.files("sandi.images").joinpath("logo.png")
            with importlib.resources.as_file(logo_res) as icon_path:
                self.root.iconphoto(False, tk.PhotoImage(file=icon_path))

        #hicon = ctypes.windll.user32.LoadImageW(0, str(icon_path), win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE)
        #hwnd = self.root.winfo_id()
        #win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)
            
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', 
                             background='#4CAF50',
                             foreground='white',
                             font=('Segoe UI', 10),
                             padding=6)
        self.style.map('TButton', 
                       background=[('active', '#45A049'), ('pressed', '#388E3C')],
                       foreground=[('active', 'white'), ('pressed', 'white')])
        self.style.configure('TLabel', 
                             background='#2c3e50',
                             foreground='white',
                             font=('Segoe UI', 12))

    def show_homepage(self):
        """
        Displays the homepage of the application, which serves as the starting 
point where the user can navigate to other pages.
        """
        self.homepage = Homepage(self.root, self._show_single_image_processing, self._show_single_stone_processing, self._show_batch_processing)

    def _show_single_image_processing(self):
        """
        Switches to the single SPM image processing window.
        """
        self.homepage.destroy()
        self.single_image_processing = SingleImageProcessing(self.root, self.show_homepage)
        
    def _show_batch_processing(self):
        """
        Switches to the batch SPM image processing window.
        """
        self.homepage.destroy()
        self.batch_processing = BatchProcessing(self.root, self.show_homepage)
        
    def _show_single_stone_processing(self):
        """
        Switches to the single gravels image processing window.
        """
        self.homepage.destroy()
        self.single_stone_processing = SingleStoneProcessing(self.root, self.show_homepage)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()