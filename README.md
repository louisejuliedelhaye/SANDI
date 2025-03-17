# <img src="https://github.com/user-attachments/assets/b1fa9c0e-d914-40fc-b6b8-83716b975e52" width="23">  SANDI     
SANDI is a free, open-access software designed for oceanography and sedimentology. It can be used for two purposes: 1. to extract suspended particles from high-resolution underwater images (on a single image or on a batch) and 2. to extract gravels (> 1 mm) from a laboratory image, in order to measure their size and shape and to derive some statistics. Users can choose to download the full code and run the ‘main’ file, or they can download the latest release of the software as an executable, which is self-contained.

***Disclaimer**: This is a beta version of the software, and it may therefore still contain a few errors or malfunctions. We welcome any feedback and suggestions for improvement.*

![Capture](https://github.com/user-attachments/assets/a501f956-dc38-4597-9cda-cd86c29b0be2)

## 1. Suspended particles
Description yet to be inserted.

## 2. Gravel analysis
This section presents a fast and easy way to measure the size and shape of rocks by detecting their contours from an image taken in a laboratory. 

### 2.1. Input image
The input image should contain the rocks displayed on a white or green background (see two options later), together with a scale and a label. The image should be shot from above in order to have a good overall vision of the samples. We recommand using a green background for rocks with a light or a wide range of colors, and a white background for darker gravels. The contour detection is very sensitive to lighting and shadows, we therefore recommand to photograph the samples with sufficient, homogenous natural light, that generates as little shadow as possible. If the details of the rocks extracted are important, we recommend using a camera specially designed for macro shots, that will highly improve the quality of the vignettes.

<div align="center">
  <img src="https://github.com/user-attachments/assets/81823110-4d1f-46a8-8414-772492b99f6f" width="400"> <img src="https://github.com/user-attachments/assets/37c1304a-6572-428c-921a-cb3a95807a3b" width="400">
  
  *Figure x. Examples of input images on a green and on white background.*
</div>

### 2.2. Scale measurement
When the images in jpg are imported in the software, the user is invited to draw a line representing one centimeter on the ruler displayed on the picture, enabling the software to calculate the scale of the image. The accuracy of this measurement is essential for the reliability of the results that are calculated based on the measured pixel size, so we recommend drawing the line several times in order to see the variability and compare the different pixel sizes obtained. A value can be considered correct when it is measured several times. For better accuracy, we recommend that the ruler is aligned parallel to the edge of the image.

<div align="center">
  <img src="https://github.com/user-attachments/assets/d306ce67-8df9-47b3-bc10-bf0bc241e78b" width="600">
  
  *Figure x. Demonstration of the scale definition.*
</div>

### 2.3. Background correction: white background image
In the case of an image with a white background, defining a threshold can be complicated, particularly if the samples photographed contain stones of different colours, including light colours that are easily mistaken for the background. In such cases, different processes for enhancing the original image can be applied to obtain better results. The different enhancement methods can be found in the frame "Option 1" in the software, see image below.

<div align="center">
  <img src="https://github.com/user-attachments/assets/341b0c7b-8e7c-4fc2-8e94-a6eb94d145d1" width="600">
  
  *Figure x. Localisation of the options to enhance the image on a white background in the software (see frame highlighted in green).*
</div>

#### 2.3.1. Denoising
The denoise function is designed to reduce noise in a grayscale image using the Non-Local Means Denoising method from OpenCV. This technique works by comparing pixel intensities in different small windows across the image and averaging similar ones to replace the value of a specific pixel. Compared to blurring methods, it allows preserving as much image details as possible while removing unnecessary noise. The strength of the denoising filter can be adjusted manually by the user but is set to 15 by default, which after trial and errors showed to be the best fit for our test images. Performing this operation is essential to obtain representative shape indicators as noise on the image incorrectly increases the complexity of the edges of detected objects (see Figure x). 

<div align="center">
  <img src="https://github.com/user-attachments/assets/3c7eb310-317e-4200-9b4e-33510972de06" width="600">
  
  *Figure x. Impact of different values of the denoising filter strength (A: 0; B: 15; C: 30).*
</div>

#### 2.3.2. Histogram stretching
The histogram stretching operation is used on the greyscale image to clip the pixel intensity values within a specified range and then stretch the resulting values to cover the full 8-bit range (0–255), effectively enhancing contrasts. 



#### 2.3.3. Image reconstruction
#### 2.3.4. Shadow correction

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

### 2.8. Examples of shape indicators

<div align="center">
  <img src="https://github.com/user-attachments/assets/759c4ca0-1559-4c64-a512-47814be87fd0" width="300">   <img src="https://github.com/user-attachments/assets/02aada08-dd55-4876-b0ed-30dfc3379613" width="400" style="vertical-align: middle;">

  *Figure x. Example of angular stone.*

<div align="center">
  <img src="https://github.com/user-attachments/assets/17c4dfea-e9da-45d0-9fd3-d6e573e3ea1d" width="300">   <img src="https://github.com/user-attachments/assets/d1149d54-cc86-4964-b783-381de25281b5" width="400" style="vertical-align: middle;">

  *Figure x. Example of rounded stone.*

