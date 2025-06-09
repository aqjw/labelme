# -*- encoding: utf-8 -*-

import pytest

from labelme.widgets import ZoomWidget


@pytest.mark.gui
def test_ZoomWidget_max_zoom(qtbot):
    """Test ZoomWidget with custom max_zoom parameter"""
    # Test default max_zoom
    widget_default = ZoomWidget()
    qtbot.addWidget(widget_default)
    assert widget_default.maximum() == 1000
    assert widget_default.minimum() == 1

    # Test custom max_zoom
    widget_custom = ZoomWidget(max_zoom=2500)
    qtbot.addWidget(widget_custom)
    assert widget_custom.maximum() == 2500
    assert widget_custom.minimum() == 1

    # Test setting values within range
    widget_custom.setValue(1500)
    assert widget_custom.value() == 1500


@pytest.mark.gui
def test_ZoomWidget_display(qtbot):
    """Test ZoomWidget display and format"""
    widget = ZoomWidget(value=150, max_zoom=2000)
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Check initial value and format
    assert widget.value() == 150
    assert " %" in widget.suffix()
