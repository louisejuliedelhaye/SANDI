This file lists all the improvements planned for future versions of the software. 
- [ ] indicates changes not implemented yet
- [x] indicates changes implemented in the online code, but not yet in the latest executable release.

# To-do list - for SANDI v0.1.6

## Layout
- [x] Add a progress bar for the batch processing
- [x] Improve vignette design
- [ ] Put vignettes in color

## Image processing options
- [x] Add option to insert pixel size directly
- [x] Add option to work with other formats than jpg
- [x] Add option to automatically detect whether the background is black or white
- [x] Adapt background illumination and particle extraction to images on white background
- [x] Add option to shrink contours by a few pixels
- [x] Add option to remove holes inside particles

## Particle measurements
- [x] Modify 2D and 3D Fractal Dimension measurements calculations
- [x] Add kurtosis, skewness and mean pixel intensity inside the particle
- [x] Add particle color
- [x] Add Feret diameter

## Bug corrections
- [ ] Correct requirements file
- [ ] Make sure the user input width, height and depth are correctly adapted
- [ ] Correct time estimation in log print of batch processing completion

# To-do list - for future versions

- [ ] Update Documentation (format & content)

## Code structure
- [ ] Isolate all constants
      
## Layout
- [ ] Make layout adaptable to different screen sizes and resolutions
- [ ] Add option to zoom in the image when particles are extracted
- [ ] Add description of each function when hovering over

## Bug corrections
- [ ] Make it available for Linux and Mac: font adaptation

## Image processing options
- [ ] Add region merging option
- [ ] Add option to choose the thresholding algorithm
- [ ] Add option to convert video to images
