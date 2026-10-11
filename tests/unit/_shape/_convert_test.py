from __future__ import annotations

import numpy as np
import pytest

from labelme._shape import Shape
from labelme._shape import can_convert_to_polygon
from labelme._shape import convert_to_polygon


def test_rectangle_corners_unfold_into_polygon_loop() -> None:
    rectangle = Shape(
        label="cat",
        group_id=3,
        shape_type="rectangle",
        flags={"occluded": True},
        description="note",
        points=np.array([[10.0, 20.0], [40.0, 50.0]]),
        other_data={"score": 0.9},
        closed=True,
    )

    polygon = convert_to_polygon(rectangle)

    assert polygon.shape_type == "polygon"
    assert polygon.points.tolist() == [[10, 20], [40, 20], [40, 50], [10, 50]]
    assert polygon.point_labels.tolist() == [1, 1, 1, 1]
    assert polygon.closed
    assert (polygon.label, polygon.group_id, polygon.description) == (
        "cat",
        3,
        "note",
    )
    assert polygon.flags == {"occluded": True}
    assert polygon.other_data == {"score": 0.9}
    assert polygon.flags is not rectangle.flags
    assert rectangle.shape_type == "rectangle"
    assert rectangle.points.tolist() == [[10, 20], [40, 50]]


def test_oriented_rectangle_keeps_its_corners() -> None:
    corners = [[0.0, 5.0], [5.0, 0.0], [10.0, 5.0], [5.0, 10.0]]
    oriented = Shape(shape_type="oriented_rectangle", points=np.array(corners))

    polygon = convert_to_polygon(oriented)

    assert polygon.shape_type == "polygon"
    assert polygon.points.tolist() == corners


@pytest.mark.parametrize(
    ("shape_type", "points"),
    [
        ("polygon", [[0, 0], [1, 0], [1, 1]]),
        ("circle", [[0, 0], [1, 1]]),
        ("mask", [[0, 0], [1, 1]]),
        ("rectangle", [[0, 0]]),
        ("oriented_rectangle", [[0, 0], [1, 0]]),
    ],
    ids=[
        "polygon",
        "circle",
        "mask",
        "unfinished_rectangle",
        "unfinished_oriented_rectangle",
    ],
)
def test_non_rectangle_is_not_convertible(
    *, shape_type: str, points: list[list[float]]
) -> None:
    shape = Shape(shape_type=shape_type, points=np.array(points))  # ty: ignore[invalid-argument-type]

    assert not can_convert_to_polygon(shape)
    with pytest.raises(ValueError, match="Cannot convert to polygon"):
        convert_to_polygon(shape)
