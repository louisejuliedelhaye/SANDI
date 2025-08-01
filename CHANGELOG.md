# Changelog

All notable changes to this project will be documented in this file.


The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.7 - Unreleased]

### Added

### Changed

### Removed

## [0.1.6] - 2025-08-01

### Added
* Added progress bar in batch processing page.
* Added option to erode particles by selected number of pixels in batch and single image processing pages.
* Added option to fill holes inside particles in batch and single image processing pages.
* Added Feret diameter and particle color detection in batch and single image processing pages.

### Changed
* Updated image canvas in single image processing page to center smaller images.
* Improved vignettes layout to make it adjust automatically to particle size, and to make sure it retains the colors of the originally imported image.
* Adjusted the requirements file.

### Removed
* Removed possibility to add image height and width in um manually, but is instead automatically calculated from the pixel size.

## [0.1.5] - 2025-06-24