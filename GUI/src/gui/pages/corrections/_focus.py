import typing

import numpy as np

from ... import utils
from ..._base import ShortCorrectionPage, images, microscope
from .... import validation


class AutoFocus(ShortCorrectionPage):

    def __init__(self, failure_action: typing.Callable[[Exception], None], mic: microscope.Microscope,
                 scanner: microscope.Scanner):
        super().__init__(mic)
        self._scanner = scanner
        self._image: typing.Optional[images.GreyImage] = None

        self._focus_scans = utils.Spinbox(10, 1, validation.examples.focus)
        self._scans = utils.Counter(self._focus_scans, "Number of scans since last routine", start=0)
        # self._scans.needsReset.connect(self.conditionHit.emit)
        self._amount = utils.LabelledWidget("Images", utils.Spinbox(10, 10, validation.examples.focus_runs),
                                            utils.LabelOrder.SUFFIX)
        self._df = utils.LabelledWidget("Unit Change",
                                        utils.Spinbox(5, 1, validation.examples.focus_bits,
                                                      display=(lambda f: f"{f:04X}", lambda s: int(s, 16))),
                                        utils.LabelOrder.SUFFIX)
        self._df.focus.dataPassed.connect(lambda v: self.settingChanged.emit("focus_change", v))
        self._df.focus.dataFailed.connect(failure_action)
        self._amount.focus.dataPassed.connect(lambda v: self.settingChanged.emit("num_images", v))
        self._amount.focus.dataFailed.connect(failure_action)
        self._scans.limitChanged.connect(lambda v: self.settingChanged.emit("focus_scans", v))
        self._scans.limitFailure.connect(failure_action)
        self._regular.addWidget(self._scans)
        self._regular.addWidget(self._amount)
        self._regular.addWidget(self._df)

        self._focus_change = self._df
        self._num_images = self._amount

        self.setLayout(self._layout)

    def scans_increased(self):
        self._scans.increase()

    def query(self):
        self._scans.check()

    def run(self):
        if not self.isEnabled():
            return
        self.runStart.emit()
        if microscope.ONLINE:
            num_images = self._amount.focus.get_data()
            variances, defocuses = [], []
            link = self._link.subsystems["Lenses"]
            with link.switch_lens(microscope.Lens.OL_FINE):
                focus = link.value
                df = self._df.focus.get_data()
                for i in range(num_images):
                    self._image = self._scanner.scan()
                    if self._image.image().mean() == 0:
                        continue
                    variances.append(self._get_variance())
                    defocuses.append(focus)
                    if i:
                        delta = variances[i] - variances[i - 1]
                        if delta < 0:
                            if i > 1:
                                break
                        df *= -1
                    focus += df
                    link.value = focus
            if variances:
                max_i = np.argmax(variances)
                link.value = defocuses[max_i]  # set OLf based on defocuses[max_i]
                print(max_i)
        self.runEnd.emit()

    def _get_variance(self) -> float:
        array = self._image.image()
        return array.var() / (array.mean() ** 2)

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("focus_change", "num_images", "focus_scans")

    def help(self) -> str:
        s = f"""This correction is meant to combat the OLf value of the microscope no longer being optimal.
        As this is not a live correction (i.e. the value is not constantly being suboptimal);
        this is dependant on the number of scans being run.
        
        It is a blocking correction, and will halt the execution of other functions until it is finished.
        
        Settings
        --------
        Scan Amount
            {validation.examples.focus}
            
            The number of scans to perform prior to this correction being run;
            this will cause the counter to reset when reached.
        Images:
            {validation.examples.focus_runs}
            
            The number of images to take when this correction is being run.
            More images takes longer but yields more accurate results.
        Unit Change:
            {validation.examples.focus_bits}
            
            The value to change the OLf value by. It is a hexadecimal value."""
        return s
