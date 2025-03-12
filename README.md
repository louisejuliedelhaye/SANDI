# <img src="https://github.com/user-attachments/assets/b1fa9c0e-d914-40fc-b6b8-83716b975e52" width="23">  SANDI     
SANDI is a free, open-access software designed for oceanography and sedimentology. It can be used for two purposes: 1. to extract suspended particles from high-resolution underwater images (on a single image or on a batch) and 2. to extract gravels (> 1 mm) from a laboratory image, in order to measure their size and shape and to derive some statistics. Users can choose to download the full code and run the ‘main’ file, or they can download the latest release of the software as an executable, which is self-contained.

***Disclaimer**: This is a beta version of the software, and it may therefore still contain a few errors or malfunctions. We welcome any suggestions for improvement.*

![Capture](https://github.com/user-attachments/assets/a501f956-dc38-4597-9cda-cd86c29b0be2)

## 1. Suspended particles
Description yet to be inserted.

## 2. Gravel analysis
This section presents a fast and easy way to measure the size and shape of rocks by detecting their contours from an image taken in a laboratory. 

### 2.1. Input image
The input image should contain the rocks displayed on a white or green background (see two options later), together with a scale and a label. The image should be shot from above in order to have a good overall vision of the samples. We recommand using a green background for rocks with a light or a wide range of colors, and a white background for darker gravels.

<div align="center">
  <img src="https://github.com/user-attachments/assets/81823110-4d1f-46a8-8414-772492b99f6f" width="400"> <img src="https://github.com/user-attachments/assets/37c1304a-6572-428c-921a-cb3a95807a3b" width="400">
  
  *Figure x. Example of input images on a green and on white background*
</div>

### 2.2. Scale measurement
When the images in jpg are imported in the software, the user is invited to draw a line representing one centimeter on the scale shown on the picture, enabling the software to calculate the scale of the image. The accuracy of this measurement is essential for the reliability of the results that are calculated based on the measured pixel size, so we recommend drawing the line several times in order to see the variability and compare the different pixel sizes obtained. A value can be considered correct when it is measured several times.

### 2.3. Background correction: white background image

### 2.4. Contours detection
#### 2.4.1. For an image with a white background
#### 2.4.2. For an image with a green background

### 2.5. Gravel filtration
### 2.6. Statistics computation
### 2.7. Outputs

<div align="center">
  <img src="https://github.com/user-attachments/assets/819ddeaa-168d-446d-a835-012eb69935df" width="500">   <img src="https://github.com/user-attachments/assets/dbc545f0-8693-451b-b8a4-d7b2e8741821" width="325" style="vertical-align: middle;">
  
  *Figure x. Example of output gravel size distribution*
</div>

<div align="center">
  <img src="https://github.com/user-attachments/assets/0f187742-e9ff-4440-8dff-cadd8c3ed752" width="450">
</div>

*Figure x. Example of output classification of the gravels and mean shape indicators figure*

