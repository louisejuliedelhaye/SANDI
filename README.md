# <img src="https://github.com/user-attachments/assets/b1fa9c0e-d914-40fc-b6b8-83716b975e52" width="23">  SANDI     
SANDI is a free, open-access software designed for oceanography and sedimentology. It can be used for two purposes: 1. to extract suspended particles from high-resolution underwater images (on a single image or on a batch) and 2. to extract gravels (> 1 mm) from a laboratory image, in order to measure their size and shape and to derive some statistics. Users can choose to download the full code and run the ‘main’ file, or they can download the latest release of the software as an executable, which is self-contained.

***Disclaimer**: This is a beta version of the software, and it may therefore still contain a few errors or malfunctions. We welcome any feedback and suggestions for improvement.*

![Capture](https://github.com/user-attachments/assets/a501f956-dc38-4597-9cda-cd86c29b0be2)

## 1. Suspended particles
Description yet to be inserted.

### 1.1. Input image

### 1.2. Background correction
#### 1.2.1. Denoising
#### 1.2.2. Histogram stretching
#### 1.2.3. Background illumination
#### 1.2.4. Image reconstruction
#### 1.2.5. Resampling

### 1.3. Particle extraction

### 1.4. Statistics computation

### 1.5. Outputs

## 2. Gravel analysis
This section presents a fast and easy way to measure the size and shape of rocks by detecting their contours from an image taken in a laboratory. The beta version of this section is still under construction. Although it already is operational, it still has potential for improvement. Please bear this in mind when using it.  

### 2.1. Input image
The input image should contain the rocks displayed on a white or green background (see two options later), together with a ruler and a label. The image should be shot from above in order to have a good overall vision of the samples and to avoid measurement inaccuracies due to changes in the image geometry. We recommand using a green background for rocks with a light or a wide range of colors, and a white background for darker gravels. The contour detection is very sensitive to lighting and shadows, we therefore recommand to photograph the samples with sufficient, homogenous natural light, that generates as little shadow as possible. If the details of the rocks extracted are important, we recommend using a camera specially designed for macro shots, that will highly improve the quality of the vignettes.

<div align="center">
  <img src="https://github.com/user-attachments/assets/81823110-4d1f-46a8-8414-772492b99f6f" width="400"> <img src="https://github.com/user-attachments/assets/37c1304a-6572-428c-921a-cb3a95807a3b" width="400">
  
  *Figure x. Examples of input images on a green and on white background.*
</div>

### 2.2. Scale measurement
When the images in jpg are imported in the software, the user is invited to draw a line representing one centimeter on the ruler displayed on the picture, enabling the software to calculate the scale of the image. The accuracy of this measurement is essential for the reliability of the results that are calculated based on the measured pixel size, so we recommend drawing the line several times in order to see the variability and compare the different pixel sizes obtained each time. A value can be considered correct when it is measured several times. For better accuracy, we recommend that the ruler is aligned parallel to the edge of the image.

<div align="center">
  <img src="https://github.com/user-attachments/assets/d306ce67-8df9-47b3-bc10-bf0bc241e78b" width="600">
  
  *Figure x. Demonstration of the scale definition.*
</div>

### 2.3. Background correction: white background image
In the case of an image with a white background, defining a threshold can be complicated, particularly if the samples photographed contain stones of different colours, including light colours that are easily mistaken for the background. In such cases, different processes for enhancing the original image can be applied to obtain better results. The different enhancement methods can be found in the frame "Option 1" in the software, see green rectangle on the image below.

<div align="center">
  <img src="https://github.com/user-attachments/assets/341b0c7b-8e7c-4fc2-8e94-a6eb94d145d1" width="600">
  
  *Figure x. Localisation of the options to enhance the image on a white background in the software (see frame highlighted in green).*
</div>

#### 2.3.1. Denoising
The denoise function is designed to reduce noise in a grayscale image using the Non-Local Means Denoising method from OpenCV. The strength of the denoising filter can be adjusted manually by the user but is set to 15 by default, which after trial and errors showed to be the best fit for our test images. Performing this operation is essential to obtain representative shape indicators as noise on the image incorrectly increases the complexity of the edges of detected objects (see Figure x). 

<div align="center">
  <img src="https://github.com/user-attachments/assets/3c7eb310-317e-4200-9b4e-33510972de06" width="600">
  
  *Figure x. Impact of different values of the denoising filter strength (A: 0; B: 15; C: 30).*
</div>

#### 2.3.2. Histogram stretching
The histogram stretching operation is used on the greyscale image to clip the pixel intensity values within a specified range and then stretch the resulting values to cover the full 8-bit range (0–255). It allows to enhance the contrasts on the image. 

<div align="center">
  <img src="https://github.com/user-attachments/assets/9044c428-a442-4338-a129-25aac870ad97" width="400"> <img src="https://github.com/user-attachments/assets/e4d8bc81-0a09-4f42-9147-f227188c0e12" width="400">
  
  *Figure x. Impact of the histogram stretching (left: no histogram stretching; right: histogram stretched between 0 and 200).*
</div>

#### 2.3.3. Image reconstruction
The image reconstruction operation helps keeping important objects on the image while removing unwanted ones. It works bu using two versions of the image: the *mask* and the *marker*. While the *mask* consists of the original image, the *marker* is the original image in which each pixel's intensity is reduced by a certain value - which is decided by the user. In that new image, all the pixels which intensities become lower than the threshold are set to 0. Through the reconstruction process, the *marker* image is gradually increased by a method called "dilation" so that no pixel in the new image has an intensity higher than its intensity in the *mask* image. This technique is useful for making objects clearer, improving their shapes and removing unwanted noise from the image.

<div align="center">
  <img src="https://github.com/user-attachments/assets/7437284e-0519-4257-9941-83be68a5a044" width="400"> <img src="https://github.com/user-attachments/assets/afecbb7a-c976-47c3-b4d5-70f97a15cebf" width="400">
  <img src="https://github.com/user-attachments/assets/034d72e9-dc8e-4f3e-bc81-cd680fb97d2c" width="400"> <img src="https://github.com/user-attachments/assets/fa4c3325-bf1a-448b-a746-244c88911e5e" width="400">
  
  *Figure x. Impact of the value used in the reconstruction (upper left: no image reconstruction; upper right: image reconstruction with a difference of 10; lower left: image reconstruction with a difference of 30; lower right: image reconstruction with a difference of 50).*
</div>

#### 2.3.4. Shadow correction
The gamma correction allows to adjust the brightness and contrast of the image. Instead of changing all pixels equally, it applies a special curve that makes dark areas (shadows) brighter (with gamma value < 1) or bright areas darker (with a gamma value > 1).

<div align="center">
  <img src="https://github.com/user-attachments/assets/13e746d8-075a-4762-8525-53cf3a311bde" width="400"> <img src="https://github.com/user-attachments/assets/d7b94363-2d04-4061-9cc0-a43a3b6bb5d1" width="400">
  
  *Figure x. Impact of the gamma correction (left: no gamma correction ; right: gamma correction at 0.9).*
</div>

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

