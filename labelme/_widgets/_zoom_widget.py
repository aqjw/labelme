from __future__ import annotations

from PySide6 import QtWidgets


class ZoomWidget(QtWidgets.QDoubleSpinBox):
    def __init__(self, *, max_zoom: int) -> None:
        super().__init__()
        self.setDecimals(1)
        self.setRange(1, max_zoom)
        self.setSuffix(" %")
        self.setValue(100)

    @property
    def scale(self) -> float:
        return 0.01 * self.value()
