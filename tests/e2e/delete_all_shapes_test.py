from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from labelme._app import MainWindow

from ..conftest import close_or_pause


@pytest.mark.gui
def test_delete_all_removes_visible_shapes_in_one_undo_step(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    canvas = annotated_win._canvas_widgets.canvas
    label_list = annotated_win._docks.label_list
    assert len(canvas.shapes) == 5
    assert annotated_win._actions.delete_all.isEnabled()

    hidden_item = label_list[1]
    hidden_shape = hidden_item.shape()
    assert hidden_shape is not None
    hidden_item.setCheckState(Qt.CheckState.Unchecked)
    qtbot.wait(50)
    assert not hidden_shape.visible

    annotated_win._actions.delete_all.trigger()
    qtbot.wait(50)

    assert canvas.shapes == [hidden_shape]
    assert [item.shape() for item in label_list] == [hidden_shape]

    # auto_save включён по умолчанию: удаление сразу попадает в файл разметки.
    label_path = Path(annotated_win.current_label_file_path())

    def saved_with_hidden_shape_only() -> None:
        shapes = json.loads(label_path.read_text())["shapes"]
        assert [shape["label"] for shape in shapes] == [hidden_shape.label]

    qtbot.waitUntil(saved_with_hidden_shape_only)

    annotated_win._actions.undo.trigger()
    qtbot.wait(50)

    assert len(canvas.shapes) == 5
    assert len(list(label_list)) == 5

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


@pytest.mark.gui
def test_delete_all_disabled_without_shapes(
    *,
    qtbot: QtBot,
    raw_win: MainWindow,
    pause: bool,
) -> None:
    assert raw_win._canvas_widgets.canvas.shapes == []
    assert not raw_win._actions.delete_all.isEnabled()

    close_or_pause(qtbot=qtbot, widget=raw_win, pause=pause)
