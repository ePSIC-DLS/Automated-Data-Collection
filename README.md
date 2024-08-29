# Automatic Data Aquisition and Collection

This project will automate the alignment of an ARM200F electron microscope via the PyJEM library in python and an ANN pipeline.

It will also provide a GUI to perform automatic 4D data collection by choosing an initial (survey) image, preprocessing this into segments, then performing overlapping full-resolution scans across the segment.

To automate this GUI, a small Domain Specific Language (DSL) called 'PAL' has been designed. This language uses '.GUIAS' files to automate control of the microscope and GUI.

The GUI features documentation for all PAL and GUI features, removing the need to externally look it up.


## Core project features:
### Alignment automation:
  * Use of imaging processing techniques to format cross grating images such that the pitch size and internal angle is discernable.
  * Use of paramter-sweeping pipeline to automatically change alignment settings (such as solid angle rotation) and determine the alignment of the result.
  * Fast and accurate execution.
### Collection automation:
  * Use of a QT GUI to neatly wrap complex aquisitions into a user-friendly medium.
  * Integration of microscope control, such that emission refreshing, beam-blanking, focus-correction and drift-correction are built-in.
  * Important settings are easy to change, and advanced settings are hidden (but still modifiable) for regular users.
  * 20+ internal variables to allow advanced users to change most aspects of execution.
  * Pause and resume scans at any point.
### PAL features:
  * High-level syntax.
  * Simple grammar.
  * Full microscope and GUI control.
  * Creation of .GUIAS templates from the GUI.