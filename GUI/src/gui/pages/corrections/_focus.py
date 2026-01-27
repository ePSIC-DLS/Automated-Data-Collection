import typing
from typing import Tuple as _tuple

import numpy as np
import matplotlib.pyplot as plt
import time
try:
    from IPython.display import display, clear_output
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

from ... import utils
from ..._base import images, microscope, ShortCorrectionPage
from .... import load_settings, validation
from ..._errors import *

default_settings = load_settings("assets/config.json",
                                 focus_scans=validation.examples.focus,
                                 focus_change=validation.examples.focus_change,
                                 change_decay=validation.examples.focus_decay,
                                 focus_tolerance=validation.examples.lens_value,
                                 focus_limit=validation.examples.focus_limit_hex,
                                 )


class AutoFocus(ShortCorrectionPage):
    """
    Correction page for an autofocus routine. This is an OLF lens correction.

    Attributes
    ----------
    _scanner: Scanner
        The scanner to perform a scan.
    _scan: Callable[[ScanType, bool], GreyImage]
        The function capable of producing a scanned image.
    _region: FullScan
        The scan region to scan on - note that this is the full survey image.
    _focus_scans: Spinbox
        The number of scans performed prior to the correction being run.
    _scans: Counter
        The number of scans performed since the last correction.
    _decay: LabelledWidget[Spinbox]
        The rate of decay for the unit change to take in a run.
    _df: LabelledWidget[Spinbox]
        The unit change in the OLF lens.
    _tolerance: LabelledWidget[Spinbox]
        The lowest allowed value for the unit change to be before the focus correction is complete.
    _limit: LabelledWidget[Spinbox]
        The maximum number defocus to check for. This is the absolute defocus measured in nm.
    _plot: Canvas
        The current image being scanned.
    """

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner, survey_size: _tuple[int, int],
                 scan_func: typing.Callable[[microscope.ScanType, bool], images.GreyImage]):
        super().__init__(mic)
        self._scanner = scanner
        self._scan = scan_func
        self._region = microscope.FullScan(survey_size)

        self._focus_scans = utils.Spinbox(default_settings["focus_scans"], 1, validation.examples.focus)
        self._scans = utils.Counter(self._focus_scans, "Number of scans since last routine", start=0)
        self._scans.needsReset.connect(self.conditionHit.emit)
        
        # Note: Decay and Tolerance are kept for UI compatibility but unused in new alg
        self._decay = utils.LabelledWidget("Decay (Unused)", utils.PercentageBox(int(default_settings["change_decay"] * 100),
                                                                        validation.examples.focus_decay),
                                           utils.LabelOrder.SUFFIX)
        
        self._df = utils.LabelledWidget("Fine Step",
                                        utils.Spinbox(default_settings["focus_change"], 1,
                                                      validation.examples.focus_bits,
                                                      display=(lambda f: f"{f:04X}", lambda s: int(s, 16))),
                                        utils.LabelOrder.SUFFIX)
        
        focus_tolerance = validation.examples.any_int + validation.Pipeline(
            validation.Step(validation.RangeValidator(validation.LowerBoundValidator(1),
                                                      validation.DynamicUpperBoundValidator(
                                                          lambda: self._df.focus.get_data(),
                                                          inclusive=False))),
            in_type=int, out_type=int
        )
        self._tolerance = utils.LabelledWidget("Lowest Change",
                                               utils.Spinbox(default_settings["focus_tolerance"], 1, focus_tolerance,
                                                             display=(lambda f: f"{f:04X}", lambda s: int(s, 16))),
                                               utils.LabelOrder.SUFFIX)
        
        self._limit = utils.LabelledWidget("Coarse Range (+/-)",
                                           utils.Spinbox(default_settings["focus_limit"] * 0.76, 20,
                                                         validation.examples.focus_limit,
                                                         display=(lambda f: f"{int(f / 0.76):04X}",
                                                                  lambda s: float(int(s, 16) * 0.76))),
                                           utils.LabelOrder.SUFFIX)

        # Signal connections
        self._df.focus.dataPassed.connect(lambda v: self.settingChanged.emit("focus_change", v))
        self._df.focus.dataFailed.connect(failure_action)
        self._decay.focus.dataPassed.connect(lambda v: self.settingChanged.emit("change_decay", v))
        self._decay.focus.dataFailed.connect(failure_action)
        self._scans.limitChanged.connect(lambda v: self.settingChanged.emit("focus_scans", v))
        self._scans.limitFailure.connect(failure_action)
        self._tolerance.focus.dataPassed.connect(lambda v: self.settingChanged.emit("focus_tolerance", v))
        self._tolerance.focus.dataFailed.connect(failure_action)
        self._limit.focus.dataPassed.connect(lambda v: self.settingChanged.emit("focus_limit", v))
        self._limit.focus.dataFailed.connect(failure_action)
        
        self._regular.addWidget(self._scans)
        self._regular.addWidget(self._limit)
        self._regular.addWidget(self._df)
        # self._regular.addWidget(self._decay) # Hidden to reduce clutter
        # self._regular.addWidget(self._tolerance)

        self._plot = utils.Canvas(survey_size)

        self._focus_change = self._df
        self._change_decay = self._decay
        self._focus_tolerance = self._tolerance
        self._focus_limit = self._limit

        self.setLayout(self._layout)

    def scans_increased(self):
        """Method to increase the number of scans by 1."""
        self._scans.increase()

    def query(self):
        self._scans.check()

    def start(self):
        ShortCorrectionPage.start(self)
        self._display_popup(self._plot)

    def stop(self):
        ShortCorrectionPage.stop(self)
        self._plot.close()

    def run(self):
        """
        Performs the autofocus routine using a Robust Multiresolution optimization.
        Includes Parabolic Fitting and Safety Rollback.
        """
        if not self.isEnabled():
            return
        self.runStart.emit()

        if microscope.ONLINE:
            link = self._link.subsystems["Lenses"]

            # --- Helper Functions ---
            def _norm_var(img_data: np.ndarray) -> float:
                """Calculates normalized variance: (std / mean)^2."""
                mean = np.mean(img_data)
                std = np.std(img_data)
                return (std ** 2) / (mean ** 2) if mean != 0 else 0

            def _scan_and_measure(val: int) -> typing.Tuple[float, np.ndarray]:
                """Sets lens, scans, updates GUI canvas, returns (variance, image_data)."""
                link.value = int(val)
                grey_img = self._scan(self._region, True)
                self._plot.draw(grey_img.norm().dynamic().promote())
                data = grey_img.data().astype(np.float64)
                return _norm_var(data), data

            def _parabolic_fit(x_points, y_points):
                """Fits a parabola to 3 points and returns the vertex (x_max, y_max)."""
                if len(x_points) < 3:
                    return x_points[np.argmax(y_points)], np.max(y_points)
                
                # Fit y = ax^2 + bx + c
                coeffs = np.polyfit(x_points, y_points, 2)
                a, b, c = coeffs
                
                # Check if it's a peak (a < 0) or valley (a > 0)
                if a >= 0: 
                    # If it convex (valley) or flat, return max data point
                    idx = np.argmax(y_points)
                    return x_points[idx], y_points[idx]
                
                # Vertex x = -b / 2a
                vertex_x = -b / (2 * a)
                vertex_y = a * vertex_x**2 + b * vertex_x + c
                return vertex_x, vertex_y

            # --- Optimization Logic ---
            def optimize_robust(coarse_range, fine_step, fine_window):
                base_OLf = link.value
                
                # Setup Plot
                plt.ioff()
                fig, (ax_plot, ax_img) = plt.subplots(1, 2, figsize=(12, 6))
                
                ax_plot.set_title("Autofocus Metric")
                ax_plot.set_xlabel("Defocus (OLf)")
                ax_plot.set_ylabel("Normalized Variance")
                line, = ax_plot.plot([], [], 'b-o', label='Scan Data', alpha=0.6)
                
                ax_img.set_title("Live Scan")
                ax_img.axis('off')
                img_display = None 
                
                all_ds = []
                all_vs = []
                
                def update_visuals(val, score, img_data):
                    all_ds.append(val)
                    all_vs.append(score)
                    
                    line.set_data(all_ds, all_vs)
                    ax_plot.relim()
                    ax_plot.autoscale_view()
                    
                    nonlocal img_display
                    if img_display is None:
                        img_display = ax_img.imshow(img_data, cmap='gray')
                    else:
                        img_display.set_data(img_data)
                        
                    if IPYTHON_AVAILABLE:
                        clear_output(wait=True)
                        display(fig)
                    else:
                        fig.canvas.draw()
                        fig.canvas.flush_events()
                        plt.pause(0.01)

                # --- 0. Baseline Measurement ---
                print("Measuring baseline...")
                #scan twice for first measurement for some reason!!
                start_var, start_img = _scan_and_measure(base_OLf)
                #time.sleep(0.5)
                start_var, start_img = _scan_and_measure(base_OLf)
                update_visuals(base_OLf, start_var, start_img)
                ax_plot.axhline(y=start_var, color='k', linestyle='--', label='Start Baseline')
                ax_plot.legend()

                # --- 1. Coarse Scan ---
                print("Starting coarse scan...")
                coarse_vs = []
                coarse_ds = []
                
                for offset in coarse_range:
                    current_val = int(base_OLf + offset)
                    # Skip if we just measured it (0 offset)
                    if current_val == base_OLf:
                        norm_var = start_var
                        img_data = start_img
                    else:
                        norm_var, img_data = _scan_and_measure(current_val)
                        update_visuals(current_val, norm_var, img_data)
                    
                    coarse_ds.append(current_val)
                    coarse_vs.append(norm_var)
                    print(f"Coarse OLf: {current_val:04X}, Var: {norm_var:.5f}")

                # Find Best Coarse Region
                best_coarse_idx = np.argmax(coarse_vs)
                best_coarse_OLf = coarse_ds[best_coarse_idx]
                ax_plot.plot(best_coarse_OLf, coarse_vs[best_coarse_idx], 'rx', markersize=10, label='Best Coarse')
                ax_plot.legend()
                
                print(f"Best coarse OLf: {best_coarse_OLf:04X}")

                # --- 2. Fine Scan ---
                print("Starting fine scan...")
                start_fine = -fine_window // 2
                stop_fine = fine_window // 2 + 1
                fine_range = range(start_fine, stop_fine, fine_step)
                
                fine_vs = []
                fine_ds = []
                
                for offset in fine_range:
                    current_val = int(best_coarse_OLf + offset)
                    # Optimization: skip if already measured in coarse scan
                    if current_val in all_ds:
                        # Find previous value
                        idx = all_ds.index(current_val)
                        norm_var = all_vs[idx]
                        # Don't scan, just add to fine lists
                    else:
                        norm_var, img_data = _scan_and_measure(current_val)
                        update_visuals(current_val, norm_var, img_data)
                    
                    fine_ds.append(current_val)
                    fine_vs.append(norm_var)
                    print(f"Fine OLf: {current_val:04X}, Var: {norm_var:.5f}")

                if not fine_vs:
                    print("Fine scan failed.")
                    link.value = base_OLf
                    return

                # --- 3. Parabolic Refinement ---
                # Get indices of top 3 points
                sorted_indices = np.argsort(fine_vs)[-3:]
                top_x = np.array(fine_ds)[sorted_indices]
                top_y = np.array(fine_vs)[sorted_indices]
                
                ideal_OLf_float, ideal_var = _parabolic_fit(top_x, top_y)
                ideal_OLf = int(ideal_OLf_float)
                
                print(f"Calculated Vertex: {ideal_OLf:04X} (Float: {ideal_OLf_float:.2f})")
                
                # --- 4. Validation & Rollback ---
                # Compare max found variance vs baseline
                # We require the new peak to be at least as good as start.
                
                # If fitting went wild (out of scan range), clamp it to discrete max
                best_discrete_idx = np.argmax(fine_vs)
                discrete_best_OLf = fine_ds[best_discrete_idx]
                discrete_best_var = fine_vs[best_discrete_idx]
                
                # Sanity check: if parabola vertex is way outside our scan range, trust discrete max
                if abs(ideal_OLf - discrete_best_OLf) > fine_window:
                    print("Parabolic fit unstable, using discrete maximum.")
                    ideal_OLf = discrete_best_OLf
                    ideal_var = discrete_best_var

                ax_plot.plot(ideal_OLf, ideal_var, 'g*', markersize=15, label='Calculated Peak')
                
                # ROLLBACK CHECK
                if ideal_var < start_var * 1.01: # Threshold: must be > 1% better than start to move
                    print(f"WARNING: Improvement negligible (New: {ideal_var:.5f} vs Start: {start_var:.5f}).")
                    print("ROLLING BACK to starting position.")
                    ideal_OLf = base_OLf
                    ax_plot.text(0.05, 0.95, "ROLLBACK ACTIVATED", transform=ax_plot.transAxes, color='red', fontsize=12, fontweight='bold')
                else:
                    print(f"Confirmed Improvement. Moving lens to {ideal_OLf:04X}")

                ax_plot.legend()
                if IPYTHON_AVAILABLE:
                    clear_output(wait=True)
                    display(fig)
                else:
                    plt.show() # Final show
                
                # Final move
                link.value = ideal_OLf

            # --- Execution ---
            with link.switch_lens(microscope.Lens.OL_FINE):
                limit_val = int(self._limit.focus.get_data())
                fine_step = int(self._df.focus.get_data())
                
                # Dynamic coarse step: ensure we get ~8-10 points across the range
                coarse_step = max(fine_step * 2, int(limit_val / 4))
                
                coarse_range = range(-limit_val, limit_val + 1, coarse_step)
                # Fine window is the size of 2 coarse steps to ensure overlap
                fine_window = coarse_step * 2

                optimize_robust(coarse_range, fine_step, fine_window)

        self.runEnd.emit()

    @staticmethod
    def _get_variance(image: images.GreyImage) -> float:
        array = image.convert(np.float64)
        return array.var() / (array.mean() ** 2)

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("focus_change", "change_decay", "focus_scans", "focus_tolerance", "focus_limit")

    def help(self) -> str:
        s = f"""This correction is meant to combat the OLf value of the microscope no longer being optimal.
        
        The routine performs a Robust Multiresolution Scan:
        1. Measures current focus score (Variance).
        2. Coarse Scan: Scans range +/- Defocus Limit.
        3. Fine Scan: Scans closely around the best coarse point.
        4. Parabolic Fit: Calculates sub-step peak.
        5. Safety Check: If new focus is not better than start, it reverts changes.
        
        Settings
        --------
        Scan Amount:
            {validation.examples.focus}
            
            The number of scans to perform prior to this correction being run.
        Fine Step:
            {validation.examples.focus_bits}
            
            The step size for the 'Fine' scan phase.
        Coarse Range (+/-):
            {validation.examples.focus_limit}
            
            The +/- range (in nm) to perform the 'Coarse' scan over.
        """
        return s
