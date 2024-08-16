import functools
import typing
from typing import Dict as _dict, List as _list

from ._01_survey import SurveyImage
from ... import utils
from ..._base import CanvasPage, images, SettingsPage
from ..._errors import *
from .... import validation, load_settings
from ....language import vals


class OrderDict(utils.SettingsDict):
    """
    Typed dictionary representing the processing pipeline that the survey image undergoes.

    For the keys, see the advanced help of the processing pipeline - as that describes the parameters for each function.
    """
    order: utils.OrderedGroup[utils.PALFunction]

    blur_Height: utils.Spinbox
    blur_Width: utils.Spinbox

    gss_blur_Height: utils.Spinbox
    gss_blur_Width: utils.Spinbox
    gss_blur_Sigma_X: utils.Spinbox
    gss_blur_Sigma_Y: utils.Spinbox

    sharpen_Size: utils.Spinbox
    sharpen_Scale: utils.Spinbox
    sharpen_Delta: utils.Spinbox

    median_Size: utils.Spinbox

    edge_Size: utils.Spinbox

    open_Height: utils.Spinbox
    open_Width: utils.Spinbox
    open_Shape: utils.Enum
    open_Multiplier: utils.Spinbox
    open_Repeats: utils.Spinbox

    close_Height: utils.Spinbox
    close_Width: utils.Spinbox
    close_Shape: utils.Enum
    close_Multiplier: utils.Spinbox
    close_Repeats: utils.Spinbox

    gradient_Height: utils.Spinbox
    gradient_Width: utils.Spinbox
    gradient_Shape: utils.Enum
    gradient_Multiplier: utils.Spinbox
    gradient_Repeats: utils.Spinbox

    gradient_Height: utils.Spinbox
    gradient_Width: utils.Spinbox
    gradient_Shape: utils.Enum
    gradient_Multiplier: utils.Spinbox
    gradient_Repeats: utils.Spinbox

    i_gradient_Height: utils.Spinbox
    i_gradient_Width: utils.Spinbox
    i_gradient_Shape: utils.Enum
    i_gradient_Multiplier: utils.Spinbox
    i_gradient_Repeats: utils.Spinbox

    e_gradient_Height: utils.Spinbox
    e_gradient_Width: utils.Spinbox
    e_gradient_Shape: utils.Enum
    e_gradient_Multiplier: utils.Spinbox
    e_gradient_Repeats: utils.Spinbox


default_settings = load_settings("assets/config.json",
                                 blur_call=validation.examples.blur_call,
                                 gss_blur_call=validation.examples.gss_blur_call,
                                 sharpen_call=validation.examples.sharpen_call,
                                 median_call=validation.examples.one_element_call,
                                 edge_call=validation.examples.one_element_call,
                                 open_call=validation.examples.morphology_call,
                                 close_call=validation.examples.morphology_call,
                                 gradient_call=validation.examples.morphology_call,
                                 i_gradient_call=validation.examples.morphology_call,
                                 e_gradient_call=validation.examples.morphology_call,
                                 blur_order=validation.examples.call_order,
                                 gss_blur_order=validation.examples.call_order,
                                 sharpen_order=validation.examples.call_order,
                                 median_order=validation.examples.call_order,
                                 edge_order=validation.examples.call_order,
                                 threshold_order=validation.examples.call_order,
                                 open_order=validation.examples.call_order,
                                 close_order=validation.examples.call_order,
                                 gradient_order=validation.examples.call_order,
                                 i_gradient_order=validation.examples.call_order,
                                 e_gradient_order=validation.examples.call_order,
                                 minima=validation.examples.hist_colours,
                                 maxima=validation.examples.hist_colours,
                                 threshold_inversion=validation.examples.any_bool
                                 )


class Order(utils.SettingsPopup):
    """
    Concrete popup representing the order and operations in the full processing pipeline.

    Attributes
    ----------
    _blur: PALFunction
        The basic blurring operation. See `GreyImage.transform.blur.basic` for details.
    _gss_blur: PALFunction
        The Gaussian blurring operation. See `GreyImage.transform.blur.gaussian` for details.
    _sharpen: PALFunction
        The sharpening operation. See `GreyImage.transform.sharpen` for details.
    _median: PALFunction
        The median blurring operation. See `GreyImage.transform.blur.median` for details.
    _edge: PALFunction
        The edge detection operation. See `GreyImage.grey_transform.threshold.edge_detection` for details.
    _threshold: PALFunction
        The intensity thresholding operation. See `GreyImage.grey_transform.threshold.region` for details.
    _open: PALFunction
        The morphological opening operation. See `GreyImage.grey_transform.open` for details.
    _close: PALFunction
        The morphological closing operation. See `GreyImage.grey_transform.close` for details.
    _gradient: PALFunction
        The morphological gradient operation. See `GreyImage.grey_transform.gradient` for details.
    _i_gradient: PALFunction
        The morphological internal gradient operation. See `GreyImage.grey_transform.whitehat` for details.
    _e_gradient: PALFunction
        The morphological external gradient operation. See `GreyImage.grey_transform.blackhat` for details.
    _group: OrderedGroup[PALFunction]
        The actual pipeline to use. Note that as it's an *ordered* group, many pipelines can be created with the same
        operations.
    """

    def __init__(self, failure_action: typing.Callable[[Exception], None]):
        super().__init__()

        def _transform(start: images.MorphologicalShape) -> utils.Enum:
            return utils.Enum(images.MorphologicalShape, start)

        def _num(init: int, pipe: validation.Pipeline = validation.examples.kernel, step=2) -> utils.Spinbox:
            return utils.Spinbox(init, step, pipe)

        def _morph(name: str) -> utils.PALFunction:
            call = default_settings[f"{name}_call"]
            return utils.PALFunction(name, failure_action, default_settings[f"{name}_order"][1],
                                     Height=_num(call[0]),
                                     Width=_num(call[1]),
                                     Shape=_transform(images.MorphologicalShape[call[2]]),
                                     Multiplier=_num(call[3], validation.examples.morph, 1),
                                     Repeats=_num(call[4], validation.examples.morph, 1),
                                     )

        self._blur = utils.PALFunction("blur", failure_action, default_settings["blur_order"][1],
                                       Height=_num(default_settings["blur_call"][0]),
                                       Width=_num(default_settings["blur_call"][1])
                                       )
        self._gss_blur = utils.PALFunction("gss_blur", failure_action, default_settings["gss_blur_order"][1],
                                           Height=_num(default_settings["gss_blur_call"][0]),
                                           Width=_num(default_settings["gss_blur_call"][1]),
                                           Sigma_X=_num(default_settings["gss_blur_call"][2], validation.examples.sigma,
                                                        1),
                                           Sigma_Y=_num(default_settings["gss_blur_call"][3], validation.examples.sigma,
                                                        1)
                                           )
        self._sharpen = utils.PALFunction("sharpen", failure_action, default_settings["sharpen_order"][1],
                                          Size=_num(default_settings["sharpen_call"][0]),
                                          Scale=_num(default_settings["sharpen_call"][1], validation.examples.sigma, 1),
                                          Delta=_num(default_settings["sharpen_call"][2], validation.examples.sigma, 1)
                                          )
        self._median = utils.PALFunction("median", failure_action, default_settings["median_order"][1],
                                         Size=_num(default_settings["median_call"][0])
                                         )
        self._edge = utils.PALFunction("edge", failure_action, default_settings["edge_order"][1],
                                       Size=_num(default_settings["edge_call"][0])
                                       )
        self._threshold = utils.PALFunction("threshold", failure_action, default_settings["threshold_order"][1])
        self._open = _morph("open")
        self._close = _morph("close")
        self._gradient = _morph("gradient")
        self._i_gradient = _morph("i_gradient")
        self._e_gradient = _morph("e_gradient")
        fns = (
            self._blur, self._gss_blur, self._sharpen, self._median, self._edge, self._threshold, self._open,
            self._close, self._gradient, self._i_gradient, self._e_gradient
        )
        order = [
            fns[i - 1] for i, _ in map(default_settings.get, ("blur_order", "gss_blur_order", "sharpen_order",
                                                              "median_order", "edge_order", "threshold_order",
                                                              "open_order", "close_order", "gradient_order",
                                                              "i_gradient_order", "e_gradient_order"))
        ]
        self._group = utils.OrderedGroup(*order)
        self._group.orderChanged.connect(lambda _, __: self.settingChanged.emit("order", self._group.get_members()))
        for func in self._group.get_members():
            func.parameterChanged.connect(self.settingChanged.emit)
            func.toggled.connect(lambda s: self.settingChanged.emit(func.name(), s))
        self._layout.addWidget(self._group)

    def widgets(self) -> OrderDict:
        # noinspection PyTypeChecker
        return {
            "order": self._group,
            **self._blur.to_dict(),
            **self._gss_blur.to_dict(),
            **self._sharpen.to_dict(),
            **self._median.to_dict(),
            **self._edge.to_dict(),
            **self._threshold.to_dict(),
            **self._open.to_dict(),
            **self._close.to_dict(),
            **self._gradient.to_dict(),
            **self._i_gradient.to_dict(),
            **self._e_gradient.to_dict()
        }


class ProcessingPipeline(CanvasPage, SettingsPage[Order]):
    """
    Concrete page representing the pre-processing the survey image undergoes.

    The binarisation makes it easier to identify clusters by removing intermediate intensities of noise.

    Attributes
    ----------
    _prev: SurveyImage
        The previous stage in the pipeline, used to check whether a survey image has been captured.
    _minima_pipe: Pipeline[Any, int]
        The pipeline describing how the minima value can change.
    _maxima_pipe: Pipeline[Any, int]
        The pipeline describing how the maxima value can change.
    _minima: LabelledWidget[Spinbox]
        The widget controlling the minima value.
    _maxima: LabelledWidget[Spinbox]
        The widget controlling the maxima value.
    _invert: LabelledWidget[Checkbox]
        The widget deciding whether the resulting binary image should be inverted.
    _threshold_inversion: LabelledWidget[Checkbox]
        An alias for _invert, used to make the attached DSL's variable names clearer.
    """
    settingChanged = SettingsPage.settingChanged

    def __init__(self, size: int, previous: SurveyImage, failure_action: typing.Callable[[Exception], None]):
        CanvasPage.__init__(self, size)
        SettingsPage.__init__(self, utils.SettingsDepth.REGULAR | utils.SettingsDepth.ADVANCED,
                              advanced=functools.partial(Order, failure_action))
        self._prev = previous

        def _minima() -> int:
            return int(self._minima.focus.get_data())

        def _maxima() -> int:
            return int(self._maxima.focus.get_data())

        min_val = validation.RangeValidator(validation.LowerBoundValidator(0),
                                            validation.DynamicUpperBoundValidator(_maxima, inclusive=False))
        max_val = validation.RangeValidator(validation.DynamicLowerBoundValidator(_minima, inclusive=False),
                                            validation.UpperBoundValidator(255))

        minima = validation.Pipeline(validation.Step(min_val,
                                                     desc="ensures the integer is between 0 and the `maxima` value"),
                                     in_type=int, out_type=int)
        maxima = validation.Pipeline(validation.Step(max_val,
                                                     desc="ensures the integer is between the `minima` value and 255"),
                                     in_type=int, out_type=int)
        self._minima_pipe = validation.examples.any_int + minima
        self._maxima_pipe = validation.examples.any_int + maxima
        self._minima = utils.LabelledWidget("Minima", utils.Spinbox(default_settings["minima"], 1, self._minima_pipe),
                                            utils.LabelOrder.SUFFIX)
        self._maxima = utils.LabelledWidget("Maxima:", utils.Spinbox(default_settings["maxima"], 1, self._maxima_pipe),
                                            utils.LabelOrder.SUFFIX)
        self._invert = utils.LabelledWidget("Threshold Inversion",
                                            utils.CheckBox("&I", default_settings["threshold_inversion"]),
                                            utils.LabelOrder.SUFFIX)

        self._regular.addWidget(self._minima)
        self._regular.addWidget(self._maxima)
        self._regular.addWidget(self._invert)

        self._minima.focus.dataPassed.connect(lambda v: self.settingChanged.emit("minima", v))
        self._minima.focus.dataFailed.connect(failure_action)
        self._maxima.focus.dataPassed.connect(lambda v: self.settingChanged.emit("maxima", v))
        self._maxima.focus.dataFailed.connect(failure_action)
        self._invert.focus.stateChanged.connect(lambda v: self.settingChanged.emit("threshold_inversion", v))
        self._invert.focus.dataFailed.connect(failure_action)

        self._threshold_inversion = self._invert  # alias for get_control

        self.setLayout(self._layout)

        self.settingChanged.connect(lambda _, __: self.run() if self._prev.modified is not None else None)
        self._popup.settingChanged.connect(lambda _, __: self.run() if self._prev.modified is not None else None)

    def compile(self) -> str:
        order = self._popup.widgets()["order"]
        build = []
        for fn in order.get_members():
            if not fn.get_enabled():
                continue
            build.append(f"{fn.name()}({fn.params(SettingsPage.getter)})")
        return "\n".join(build)

    @utils.Tracked
    def run(self):
        if self._state != utils.StoppableStatus.ACTIVE:
            return
        self.runStart.emit()
        self._modified_image = None
        order = self._popup.widgets()["order"]
        for fn in order.get_members():
            if not fn.get_enabled():
                continue
            getattr(self, f"_{fn.name()}")()
        self.runEnd.emit()

    def start(self):
        SettingsPage.start(self)
        CanvasPage.start(self)

    def stop(self):
        SettingsPage.stop(self)
        CanvasPage.stop(self)

    def single_stage(self, name: str) -> typing.Callable[[vals.Number, _list[vals.Value]], vals.Value]:
        """
        Perform a single processing step.

        Parameters
        ----------
        name: str
            The function name to perform. This must match a known step.

        Returns
        -------
        Callable[[Number, list[Value]], Value]
            A native function for the DSL to use to perform the processing step.
        """
        fn = getattr(self, f"_{name}")

        def _inner(argc: vals.Number, argv: _list[vals.Value]) -> vals.Value:
            args = [True, *map(lambda x: x.raw, argv)]
            if any(not isinstance(arg, (vals.Number,)) for arg in argv):
                raise TypeError("Expected all numerical parameters")
            fn(*args)
            return vals.Nil()

        return _inner

    def _make_modified(self):
        if self._prev.modified is None:
            raise StagingError("any preprocessing", "scanning survey image")
        if self._modified_image is not None:
            return
        self._modified_image = self._prev.original.copy()
        self._original_image = self._modified_image.copy()
        self._canvas.draw(self._modified_image)

    def _blur(self, use_params=False, width: int = None, height: int = None):
        self._transform(lambda img, *args: img.transform.blur.basic.reference(*args),
                        lambda kwargs: ((kwargs["height"], kwargs["width"]),),
                        "blur", use_params, width=width, height=height)

    def _gss_blur(self, use_params=False, width: int = None, height: int = None, sigma_x: int = None,
                  sigma_y: int = None):
        self._transform(lambda img, *args: img.transform.blur.gaussian.reference(*args),
                        lambda kwargs: ((kwargs["height"], kwargs["width"]), (kwargs["sigma_x"], kwargs["sigma_y"])),
                        "gss_blur", use_params, width=width, height=height, sigma_x=sigma_x, sigma_y=sigma_y)

    def _sharpen(self, use_params=False, size: int = None, scale: int = None, delta: int = None):
        self._transform(lambda img, *args: img.transform.sharpen.reference(*args),
                        lambda kwargs: (kwargs["size"], kwargs["scale"], kwargs["delta"]),
                        "sharpen", use_params, size=size, scale=scale, delta=delta)

    def _median(self, use_params=False, size: int = None):
        self._transform(lambda img, *args: img.transform.blur.median.reference(*args),
                        lambda kwargs: (kwargs["size"],),
                        "median", use_params, size=size)

    def _edge(self, use_params=False, size: int = None):
        def _edge(img: images.GreyImage, k_size: int):
            img.grey_transform.threshold.edge_detection.reference(int(self._minima.focus.get_data()),
                                                                  int(self._maxima.focus.get_data()), k_size)
            if self._invert.focus.get_data():
                img.data()[:] = ~img.data()

        self._transform(_edge,
                        lambda kwargs: (kwargs["size"],),
                        "edge", use_params, size=size)

    def _threshold(self, use_params=False):
        def _threshold(img: images.GreyImage):
            mi, ma = 0, 255
            if self._invert.focus.get_data():
                mi, ma = ma, mi
            img.grey_transform.threshold.region.reference(
                images.External(int(self._minima.focus.get_data()), mi),
                images.External(int(self._maxima.focus.get_data()), ma)
            )

        self._transform(_threshold,
                        lambda kwargs: (),
                        "threshold", use_params)

    def _open(self, use_params=False, height: int = None, width: int = None, shape: int = None, multiplier: int = None,
              repeats: int = None):
        self._transform(
            lambda img, *args: img.grey_transform.open.reference(*args),
            lambda kwargs: (
                (kwargs["height"], kwargs["width"]), kwargs["shape"], kwargs["multiplier"], kwargs["repeats"]),
            "open", use_params, height=height, width=width, shape=shape, multiplier=multiplier, repeats=repeats
        )

    def _close(self, use_params=False, height: int = None, width: int = None, shape: int = None, multiplier: int = None,
               repeats: int = None):
        self._transform(
            lambda img, *args: img.grey_transform.close.reference(*args),
            lambda kwargs: (
                (kwargs["height"], kwargs["width"]), kwargs["shape"], kwargs["multiplier"], kwargs["repeats"]),
            "close", use_params, height=height, width=width, shape=shape, multiplier=multiplier, repeats=repeats
        )

    def _gradient(self, use_params=False, height: int = None, width: int = None, shape: int = None,
                  multiplier: int = None, repeats: int = None):
        self._transform(
            lambda img, *args: img.grey_transform.gradient.reference(*args),
            lambda kwargs: (
                (kwargs["height"], kwargs["width"]), kwargs["shape"], kwargs["multiplier"], kwargs["repeats"]),
            "gradient", use_params, height=height, width=width, shape=shape, multiplier=multiplier, repeats=repeats
        )

    def _i_gradient(self, use_params=False, height: int = None, width: int = None, shape: int = None,
                    multiplier: int = None, repeats: int = None):
        self._transform(
            lambda img, *args: img.grey_transform.whitehat.reference(*args),
            lambda kwargs: (
                (kwargs["height"], kwargs["width"]), kwargs["shape"], kwargs["multiplier"], kwargs["repeats"]),
            "i_gradient", use_params, height=height, width=width, shape=shape, multiplier=multiplier, repeats=repeats
        )

    def _e_gradient(self, use_params=False, height: int = None, width: int = None, shape: int = None,
                    multiplier: int = None, repeats: int = None):
        self._transform(
            lambda img, *args: img.grey_transform.blackhat.reference(*args),
            lambda kwargs: (
                (kwargs["height"], kwargs["width"]), kwargs["shape"], kwargs["multiplier"], kwargs["repeats"]),
            "e_gradient", use_params, height=height, width=width, shape=shape, multiplier=multiplier, repeats=repeats
        )

    def _transform(self, fn: typing.Callable[..., None],
                   kwarg_arg_map: typing.Callable[[_dict[str, object]], typing.Iterable[object]], name: str,
                   use_params=False, **kwargs):
        if use_params:
            if any(v is None for v in kwargs.values()):
                raise ValueError(f"Expected {name} to have {', '.join(kwargs)}")
            old = {(key := f"{name}_{k.title()}"): self.get_setting(key) for k in kwargs}

            def _post():
                for k, v in old.items():
                    self.set_setting(k, v)

            for k, v in kwargs.items():
                self.set_setting(f"{name}_{k.title()}", v)
        else:
            def _post():
                pass
        self._make_modified()
        img = self._modified_image.demote().norm().dynamic()
        try:
            fn(img, *kwarg_arg_map({k: self.get_setting(f"{name}_{k.title()}") for k in kwargs}))
        finally:
            _post()
        self._modified_image = img.promote()
        self._canvas.draw(self._modified_image)

    def all_settings(self) -> typing.Iterator[str]:
        yield from ("minima", "maxima", "threshold_inversion")

    def help(self) -> str:
        s = f"""This page allows for processing the survey image.
        Several pre and post thresholding operations are available, and the image updates after each operation.
        
        For more information on the operations available, see the help page.

        Settings
        --------
        Minima:
            {self._minima_pipe}
            
            The minimum value that is allowed when thresholding. In the case of edge detection;
            it is the minima parameter. 
        Maxima:
            {self._maxima_pipe}
            
            The maximum value that is allowed when thresholding. In the case of edge detection;
            it is the maxima parameter.
        Threshold Inversion:
            {validation.examples.any_bool}
            
            Whether the edge detection or thresholding is inverted. This will invert the image;
            such that white becomes black and black becomes white."""
        return s

    def advanced_help(self) -> str:
        s = f"""blur(Height, Width):
            Blurs an image using 2D convolution.
            
            Parameters
            ----------
            Height:
                {validation.examples.kernel}
                
                The number of rows for the kernel.
            Width:
                {validation.examples.kernel}
                
                The number of columns for the kernel.
        
        gss_blur(Height, Width, Sigma_X, Sigma_Y)
            Blurs an image using a Gaussian Kernel.
            
            Parameters
            ----------
            Height:
                {validation.examples.kernel}
                
                The number of rows for the kernel.
            Width:
                {validation.examples.kernel}
                
                The number of columns for the kernel.
            Sigma_X:
                {validation.examples.sigma}
                
                The horizontal standard deviation. Use 0 to automatically calculate the value.
            Sigma_Y:
                {validation.examples.sigma}
                
                The vertical standard deviation. Use 0 to automatically calculate the value.
        sharpen(Size, Scale, Delta)
            Sharpens an image using Laplacian derivatives.
            
            Parameters
            ----------
            Size:
                {validation.examples.kernel}
                
                The number of rows and columns to use in the square kernel.
            Scale:
                {validation.examples.sigma}
                
                The scaling factor. While 0 is an allowed value, it is discouraged.
            Delta:
                {validation.examples.sigma}
                
                The term added to the kernel.
        median(Size)
            Blurs an image using a median blur kernel.
          
            Parameters
            ----------
            Size: 
                {validation.examples.kernel}
                
                The number of rows and columns to use in the square kernel.  
        
        edge(Size)
            Use the 'Canny' edge detection method to detect edges in the greyscale image.
            
            It uses the `minima` and `maxima` as such:
                Minima is the minimum intensity gradient for an edge to be detected;
                any edges with intensity smaller than this are discarded;
                otherwise are only kept if connected to a 'sure edge'.
                Maxima is the maximum intensity gradient for an edge to be detected;
                any edges with intensity larger than this are classified as a 'sure edge';
                otherwise are considered to be larger than the minimum.
            
            Parameters
            ----------
            Size: 
                {validation.examples.kernel}
                
                The number of rows and columns to use in the square kernel.  
        
        threshold()
            Accepts a valid range (between the `minima` and `maxima`) of greyscale colours and converts these to black;
            leaving any other colours as white.
        
        open(Height, Width, Shape, Multiplier, Repeats)
            Remove noise from the image by thinning the foreground;
            then thickening it back to original size.
            
            Parameters
            ----------
            Height:
                {validation.examples.kernel}
                
                The number of rows for the kernel.
            Width:
                {validation.examples.kernel}
                
                The number of columns for the kernel.
            Shape:
                {self.get_control('open_Shape').validation_pipe()}
                
                The shape of the kernel represents.
            Multiplier:
                {validation.examples.morph}
                
                The scaling factor for the kernel.
            Repeats:
                {validation.examples.morph}
                
                The number of times to repeat the operation.
            
        close(Height, Width, Shape, Multiplier, Repeats)
            Close small foreground holes in the image by thickening the foreground;
            then thinning it back to original size.
            
            Parameters
            ----------
            Height:
                {validation.examples.kernel}
                
                The number of rows for the kernel.
            Width:
                {validation.examples.kernel}
                
                The number of columns for the kernel.
            Shape:
                {self.get_control('open_Shape').validation_pipe()}
                
                The shape of the kernel represents.
            Multiplier:
                {validation.examples.morph}
                
                The scaling factor for the kernel.
            Repeats:
                {validation.examples.morph}
                
                The number of times to repeat the operation.
        
        gradient(Height, Width, Shape, Multiplier, Repeats)
            Find the difference between the thicker and thinner foregrounds.
            
            Parameters
            ----------
            Height:
                {validation.examples.kernel}
                
                The number of rows for the kernel.
            Width:
                {validation.examples.kernel}
                
                The number of columns for the kernel.
            Shape:
                {self.get_control('open_Shape').validation_pipe()}
                
                The shape of the kernel represents.
            Multiplier:
                {validation.examples.morph}
                
                The scaling factor for the kernel.
            Repeats:
                {validation.examples.morph}
                
                The number of times to repeat the operation.
        
        i_gradient(Height, Width, Shape, Multiplier, Repeats)
            Find the difference between the image and the `open` image.
            
            Parameters
            ----------
            Height:
                {validation.examples.kernel}
                
                The number of rows for the kernel.
            Width:
                {validation.examples.kernel}
                
                The number of columns for the kernel.
            Shape:
                {self.get_control('open_Shape').validation_pipe()}
                
                The shape of the kernel represents.
            Multiplier:
                {validation.examples.morph}
                
                The scaling factor for the kernel.
            Repeats:
                {validation.examples.morph}
                
                The number of times to repeat the operation.
        
        e_gradient(Height, Width, Shape, Multiplier, Repeats)
            Find the difference between the `close` image and the image.
            
            Parameters
            ----------
            Height:
                {validation.examples.kernel}
                
                The number of rows for the kernel.
            Width:
                {validation.examples.kernel}
                
                The number of columns for the kernel.
            Shape:
                {self.get_control('open_Shape').validation_pipe()}
                
                The shape of the kernel represents.
            Multiplier:
                {validation.examples.morph}
                
                The scaling factor for the kernel.
            Repeats:
                {validation.examples.morph}
                
                The number of times to repeat the operation.
        """
        return s
