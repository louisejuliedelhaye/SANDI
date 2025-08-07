[![PyPI version](https://img.shields.io/pypi/v/sandi.svg?color=#FFBC42)](https://pypi.org/project/sandi/)
# <img src="https://github.com/user-attachments/assets/b1fa9c0e-d914-40fc-b6b8-83716b975e52" width="23">  SANDI     
SANDI is a free, open-source software designed for oceanography and sedimentology. It can be used to extract particles from high-resolution underwater images (on a single image or on a batch) and to extract gravels (> 1 mm) from a laboratory image, in order to measure their size and shape and to compute some statistics. 

***Disclaimer**: This software is under development, and it may therefore still contain some errors or malfunctions. In the TODO document, you can see the improvements planned for future versions, but any additional feedback or suggestion is welcome and appreciated, as we hope to make it a collaboratively improving tool.*

<div align="center">
  <img src="https://github.com/user-attachments/assets/85809bf2-9c02-4b09-a56f-da2c8763f558">

  *Homepage of SANDI v0.1.8. Artwork is from [Sophie Delhaye](https://sophiedelhaye.com).*
</div>

## About SANDI
Check out the [full documentation here](https://github.com/louisejuliedelhaye/SANDI/wiki).

## How to install SANDI
There are three ways to install and use SANDI, we recommend using option 3:
1. *Users can choose to download the full code and run the ‘main’ file from GitHub*. This is the most up-to-date version, but it might still contain several bugs and errors and hasn't been approved for release yet.
2. *Users can download the executable in the 'tags' section of the repository.* This is a self-contained software, the easiest option for users with no experience in coding but is only compatible with Windows systems and is the least frequently updated of the three options. To run it, you then only need to run the exe file and can ignore the rest of this document.
3. *Users can choose to work with the sandi package referenced in PyPI*. This is the **easiest and most reliable option**, it contains the latest approved updates of the software and can simply be installed with the few following steps (provided that Anaconda or Miniconda is already installed on the user's computer) :
- download the environment_user.yml file
- open the miniconda/anaconda prompt and type the following lines **to install the package**:
<pre lang="markdown"> 
  # Navigate to the folder where your .yml file is located 
  cd directory/of/your/yml-file 
  # Create the environment 
  conda env create -f environment_user.yml 
</pre> 

## How to run SANDI
- open the miniconda/anaconda prompt and type the following lines **to run the package after installation**:

<pre lang="markdown"> 
  # Activate the environment
  conda activate sandi_env 
  # Run the package 
  python -m sandi 
</pre>

## How to update SANDI
- open the miniconda/anaconda prompt and type the following lines **to update the package after installation** in order to have the latest available version:

<pre lang="markdown"> 
  # Activate the environment
  conda activate sandi_env 
  # Check the version of the package that is installed
  pip show sandi
  # Upgrade if necessary
  python -m pip install --upgrade sandi
</pre>

If you encounter any problem with the installation and/or use of SANDI on your computer, please make an issue on the repository so we can help you resolve it.
