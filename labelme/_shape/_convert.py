from __future__ import annotations

from typing import Final

import numpy as np

from ._model import ORIENTED_RECTANGLE_POINT_COUNT
from ._model import RECTANGLE_POINT_COUNT
from ._model import Shape
from ._model import ShapeType


def can_convert_to_polygon(shape: Shape, /) -> bool:
    CONVERTIBLE_POINT_COUNTS: Final[dict[ShapeType, int]] = {
        "rectangle": RECTANGLE_POINT_COUNT,
        "oriented_rectangle": ORIENTED_RECTANGLE_POINT_COUNT,
    }
    return CONVERTIBLE_POINT_COUNTS.get(shape.shape_type) == len(shape.points)


def convert_to_polygon(shape: Shape, /) -> Shape:
    # Прямоугольник хранит два противоположных угла — разворачиваем их в четыре
    # вершины по обходу; у повёрнутого прямоугольника углы уже идут по обходу.
    if not can_convert_to_polygon(shape):
        raise ValueError(
            f"Cannot convert to polygon: shape_type={shape.shape_type!r}, "
            f"len(points)={len(shape.points)}"
        )
    if shape.shape_type == "rectangle":
        (x1, y1), (x2, y2) = shape.points
        points = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.float64)
    else:
        points = shape.points.copy()
    polygon = shape.copy()
    polygon.shape_type = "polygon"
    polygon.points = points
    polygon.point_labels = np.ones(len(points), dtype=np.int_)
    polygon.closed = True
    return polygon
