import hyperspy.api as hs
import matplotlib.pyplot as plt
import numpy as np


path = r"X:\data\2024\cm37231-4\processing\focal_series"

for mag, values in zip((1, 2.5, 10), (range(79, 86), range(86, 93), range(93, 100))):
    fig, axes = plt.subplots(3, 3)
    for i, img in enumerate(values):
        signal = hs.load(f"{path}/{mag}MX__HAADF_{img:04}")
        array = signal.data
        axes[np.unravel_index(i, axes.shape)].imshow(array, cmap="gray")
