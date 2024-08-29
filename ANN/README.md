# Artifical Neural Network for automating microscpe alignment

The ANN is a python script that when run, opens a small GUI for aligning the microscope.

The idea is that you specify an image path and some parameters, then it runs an iterative parameter sweep over these settings, finding the best-fitting grid.

Once it has, you can apply corrections (currently unfinished) to the scan coil values and re-load the image file.

## Changes Required to Finish:
- Get corrections fully implemented
- Get the GUI to *scan* an image rather than loading an image file.
- Turn off displaying every image, and instead let the sweep run by only yielding the best result.
- Possibly display an estimated time remaining view on the progress bar (based on how many runs it can do in 30 seconds)
