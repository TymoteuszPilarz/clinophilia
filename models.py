from pydantic import BaseModel, Field, model_validator

from typing import Annotated, Callable, Optional, Union, Any, overload


class ElementArea(BaseModel):
    """
    Represents an area in a 2D space with a top-left corner at (x, y) and a width and height of 'w' and 'h' respectively.
    The class is immutable.

    constructor can take floats, converting them to integers using the 'to_int_func' function.
    """

    x: Annotated[int, Field(ge=0)]
    y: Annotated[int, Field(ge=0)]
    w: int
    h: int
    to_int_func: Annotated[
        Optional[Callable[[int | float], int]], Field(repr=False, exclude=True)
    ] = int

    @overload
    def multiplied_by(
        self, multiplier: float, *, center: bool = True
    ) -> "ElementArea": ...

    @overload
    def multiplied_by(
        self, multiplier: tuple[float, float], *, center: bool = True
    ) -> "ElementArea": ...

    def multiplied_by(
        self, multiplier: Union[float, tuple[float, float]], *, center: bool = True
    ) -> "ElementArea":
        if isinstance(multiplier, tuple):
            multiplier_x, multiplier_y = multiplier
        else:
            multiplier_x = multiplier_y = multiplier
        w = self.w * multiplier_x
        h = self.h * multiplier_y
        w_diff = abs(w - self.w)
        h_diff = abs(h - self.h)
        x = self.x - (w_diff / 2 if center else 0)
        y = self.y - (h_diff / 2 if center else 0)
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0

        return ElementArea(x=x, y=y, w=w, h=h)

    # model_config: ConfigDict = {'frozen': True}
    class Config:
        frozen: True

    @model_validator(mode="before")
    @classmethod
    def to_int(cls, data: Any) -> Any:
        if isinstance(data, dict):
            def_to_int_func = cls.model_fields["to_int_func"].default
            to_int_func = data.get("to_int_func", def_to_int_func)
            data["x"] = to_int_func(data["x"])
            data["y"] = to_int_func(data["y"])
            data["w"] = to_int_func(data["w"])
            data["h"] = to_int_func(data["h"])
        return data


class MatchedElementArea(ElementArea):
    """
    Inherits from 'ElementArea' and adds a 'scale' field representing the scale at which the element's template was matched.
    """

    scale: float


class MatchedTextElementArea(ElementArea):
    """
    Inherits from 'ElementArea' and adds a 'text' field representing the found text.
    """

    text: str
