from pyscanengine import ScanEngine
from pyscanengine.data.frame_monitor import FrameMonitor
import numpy as np
import matplotlib.pyplot as plt
from PyJEM.TEM3 import Lens3
import itertools
import typing
import scipy.ndimage as imgs
import time
#this is working!
# 0x0001 = 0.76nm

engine = ScanEngine(1)
engine.pixel_time = 15e-6
engine.set_flyback_time(1e-3)
engine.set_image_size(512, 512)
engine.set_image_area(512, 512, 0, 512, 0, 512)
engine.set_enabled_inputs([3])  # add proper support for inputs
monitor = FrameMonitor(513, 513, inputs=[6], max_queue_size=1)
monitor.register(engine)

cnt = Lens3()


def _scan() -> np.ndarray:
    engine.stop_imaging(True)
    engine.start_imaging(0)
    engine.stop_imaging()
    monitor.wait_for_image()
    return monitor.pop().get_input_data(6)

images = []
images.append(_scan())


offset = 50,80
print('1')
#engine.close()

engine = ScanEngine(1)
print('2')
engine.pixel_time = 15e-6
print('3')
engine.set_flyback_time(1e-3)
print('4')
engine.set_image_size(1024, 1024)
print('5')
engine.set_image_area(512, 512, 0, 512, 0, 512)
engine.set_image_area(512, 512, int(0+offset[0]), int(512+offset[0]),int(0+offset[1]), int(512+offset[1]))
print('6')
engine.set_enabled_inputs([3])  # add proper support for inputs
print('7')
monitor = FrameMonitor(513, 513, inputs=[6], max_queue_size=1)
print('8')
monitor.register(engine)
print('9')
time.sleep(1)

test = _scan()
print(type(test))
images.append(test)
print('10')
#time.sleep(5)
fig, axs = plt.subplots(1,2)
axs[0].imshow(images[0], cmap = 'gray')
axs[1].imshow(images[1], cmap = 'gray')
print('11')
axs[0].plot(256,256, 'rx')
axs[1].plot(256,256, 'rx')
# def _var() -> float:
#     #also try normalised variance (divide by mean square)
#     an_img = _scan()
#     plt.figure()
#     plt.imshow(an_img, cmap = 'gray')
#     var = (np.std(an_img.astype(np.float64)))**2
#     print(var)
#     return var

# def _norm_var() -> float:
#     return ((np.std(_scan().astype(np.float64)))**2) / ((np.mean(_scan().astype(np.float64)))**2)


# ds = []
# vs = []
# vs_n = []

# # 0X7F2D -> 0X7F8D
# max_itterator= 5
# delta_d = 256
# tol = 1
# lim = 300
# decay = 0.8


# def _populate(*, backtrack: typing.Callable[[], None] = None):
#     ds.append(cnt.GetOLf())
#     if backtrack is not None:
#         backtrack()
#         ds.pop()
#     else:
#         vs.append(_var())
# #        vs_n.append(_norm_var())


# def _advance():
#     cnt.SetOLf(ds[-1] + delta_d)


# def _print_ds() -> str:
#     middle = ", ".join(map(format, ds, itertools.repeat("04X")))
#     return f"[{middle}]"


# _populate()
# cnt.SetOLf(ds[0] + delta_d)
# _populate()
# if vs[0] > vs[1]:
#     delta_d = -delta_d
#     _advance()  # back to zero
#     _populate(backtrack=_advance)  # advance again to get back on track
# print(f"Starting out: variances = {vs}, defocuses = {_print_ds()}, delta = {delta_d}")
# i = 1
# minima, maxima = ds[0] - lim, ds[0] + lim

# an_itterator = 0
# while an_itterator<max_itterator:#abs(delta_d) > tol and minima <= ds[-1] <= maxima:
#     i += 1
#     _populate()
#     print(f"d_{i} = {ds[-1]:04X} ({minima:04X} <= d_{i} <= {maxima:04X}), delta = {delta_d}")
#     if vs[-2] > vs[-1]:
#         print(f"Direction reversed (image is better at {ds[-2]:04X} than d_{i})")
#         delta_d = -int(delta_d * decay)
#     _advance()
#     an_itterator+=1

# max_var = max(vs)
# ideal_delta = ds[vs.index(max_var)]
# cnt.SetOLf(ideal_delta)
# if abs(delta_d) <= tol:
#     print(f"Found ideal: {ideal_delta:04X}")
# else:
#     print(f"Defocus larger than maximum trial of {lim}nm ")


# figure, ax = plt.subplots()
# for i, point in enumerate(ds):
#     ax.scatter(point, vs[i], c="b", marker="o")
#     ax.text(point, vs[i], i+1)
# #ax.scatter(ds, vs_n, c="k", marker="o")
# ax.scatter(ideal_delta, max_var, c="g", marker="o")
