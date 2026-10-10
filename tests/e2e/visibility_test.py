from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from labelme._app import MainWindow

from ..conftest import close_or_pause
from .conftest import MainWinFactory
from .conftest import show_window_and_wait_for_imagedata


@pytest.mark.gui
def test_toggle_all_shapes(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    canvas = annotated_win._canvas_widgets.canvas
    label_list = annotated_win._docks.label_list

    assert len(canvas.shapes) == 5
    for shape in canvas.shapes:
        assert shape.visible

    annotated_win.toggle_shape_visibility(value=False)
    qtbot.wait(50)

    for item in label_list:
        assert item.checkState() == Qt.CheckState.Unchecked
    for shape in canvas.shapes:
        assert not shape.visible

    annotated_win.toggle_shape_visibility(value=True)
    qtbot.wait(50)

    for item in label_list:
        assert item.checkState() == Qt.CheckState.Checked
    for shape in canvas.shapes:
        assert shape.visible

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


@pytest.mark.gui
def test_toggle_individual_shape(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    canvas = annotated_win._canvas_widgets.canvas
    label_list = annotated_win._docks.label_list

    assert len(canvas.shapes) == 5

    first_item = label_list[0]
    first_shape = first_item.shape()
    assert first_shape is not None
    assert first_shape.visible

    first_item.setCheckState(Qt.CheckState.Unchecked)
    qtbot.wait(50)
    assert not first_shape.visible

    first_item.setCheckState(Qt.CheckState.Checked)
    qtbot.wait(50)
    assert first_shape.visible

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


@pytest.mark.gui
def test_visibility_preserved_when_undoing_unrelated_edit(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    canvas = annotated_win._canvas_widgets.canvas
    label_list = annotated_win._docks.label_list

    assert len(canvas.shapes) == 5

    hidden_index = 1
    label_list[hidden_index].setCheckState(Qt.CheckState.Unchecked)
    qtbot.wait(50)
    assert not canvas.shapes[hidden_index].visible

    canvas.shapes[0].points[0] += [5.0, 5.0]
    canvas.backup_shapes()

    annotated_win.undo_shape_edit()
    qtbot.wait(50)

    assert len(canvas.shapes) == 5
    for i, shape in enumerate(canvas.shapes):
        expected_visible = i != hidden_index
        assert shape.visible is expected_visible
        expected_state = (
            Qt.CheckState.Checked if expected_visible else Qt.CheckState.Unchecked
        )
        assert label_list[i].checkState() == expected_state

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


@pytest.mark.gui
def test_undo_recovers_accidental_hide(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    canvas = annotated_win._canvas_widgets.canvas
    label_list = annotated_win._docks.label_list

    assert len(canvas.shapes) == 5
    hidden_index = 1

    label_list[hidden_index].setCheckState(Qt.CheckState.Unchecked)
    qtbot.wait(50)
    assert not canvas.shapes[hidden_index].visible
    assert annotated_win._actions.undo.isEnabled()

    annotated_win._actions.undo.trigger()
    qtbot.wait(50)

    assert len(canvas.shapes) == 5
    for i, shape in enumerate(canvas.shapes):
        assert shape.visible
        assert label_list[i].checkState() == Qt.CheckState.Checked

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


@pytest.mark.gui
def test_multi_select_toggle_propagates(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    canvas = annotated_win._canvas_widgets.canvas
    label_list = annotated_win._docks.label_list

    assert len(canvas.shapes) == 5
    selected_indices = (0, 1, 3)

    label_list.clearSelection()
    for i in selected_indices:
        label_list.select_item(item=label_list[i])
    qtbot.wait(50)
    assert {item for item in label_list.selected_items()} == {
        label_list[i] for i in selected_indices
    }

    label_list[selected_indices[1]].setCheckState(Qt.CheckState.Unchecked)
    qtbot.wait(50)

    for i in range(len(canvas.shapes)):
        if i in selected_indices:
            assert not canvas.shapes[i].visible
            assert label_list[i].checkState() == Qt.CheckState.Unchecked
        else:
            assert canvas.shapes[i].visible
            assert label_list[i].checkState() == Qt.CheckState.Checked

    annotated_win._actions.undo.trigger()
    qtbot.wait(50)

    for i in range(len(canvas.shapes)):
        assert canvas.shapes[i].visible
        assert label_list[i].checkState() == Qt.CheckState.Checked

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


@pytest.mark.gui
def test_multi_select_preserves_selection_after_checkbox_click(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    canvas = annotated_win._canvas_widgets.canvas
    label_list = annotated_win._docks.label_list

    assert len(canvas.shapes) == 5
    selected_indices = (0, 1, 3)

    label_list.clearSelection()
    for i in selected_indices:
        label_list.select_item(item=label_list[i])
    qtbot.wait(50)

    target_index = label_list._model.indexFromItem(label_list[selected_indices[1]])
    rect = label_list.visualRect(target_index)
    checkbox_pos = QPoint(rect.left() + 5, rect.center().y())
    qtbot.mouseClick(label_list.viewport(), Qt.MouseButton.LeftButton, pos=checkbox_pos)
    qtbot.wait(50)

    assert {item for item in label_list.selected_items()} == {
        label_list[i] for i in selected_indices
    }
    for i in selected_indices:
        assert label_list[i].checkState() == Qt.CheckState.Unchecked
        assert not canvas.shapes[i].visible

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


@pytest.mark.gui
def test_multi_select_collapses_on_row_body_click(
    *,
    qtbot: QtBot,
    annotated_win: MainWindow,
    pause: bool,
) -> None:
    label_list = annotated_win._docks.label_list

    selected_indices = (0, 1, 3)
    clicked_index = 2

    label_list.clearSelection()
    for i in selected_indices:
        label_list.select_item(item=label_list[i])
    qtbot.wait(50)

    target_index = label_list._model.indexFromItem(label_list[clicked_index])
    rect = label_list.visualRect(target_index)
    row_body_pos = QPoint(rect.center().x(), rect.center().y())
    qtbot.mouseClick(label_list.viewport(), Qt.MouseButton.LeftButton, pos=row_body_pos)
    qtbot.wait(50)

    assert {item for item in label_list.selected_items()} == {label_list[clicked_index]}

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)


def _annotated_win_with_config(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    config_overrides: dict,
) -> MainWindow:
    win = main_win(
        file_or_dir=str(data_path / "annotated/2011_000003.json"),
        output_dir=str(tmp_path),
        config_overrides=config_overrides,
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    return win


@pytest.mark.gui
def test_checked_labels_limit_visible_shapes_on_open(
    *,
    qtbot: QtBot,
    main_win: MainWinFactory,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    checked = {"blue_block", "red_triangle"}
    win = _annotated_win_with_config(
        main_win=main_win,
        qtbot=qtbot,
        data_path=data_path,
        tmp_path=tmp_path,
        config_overrides={"checked_labels": sorted(checked)},
    )

    assert len(win._canvas_widgets.canvas.shapes) == 5
    for item in win._docks.label_list:
        shape = item.shape()
        assert shape is not None
        expected_visible = shape.label in checked
        assert shape.visible is expected_visible
        assert item.checkState() == (
            Qt.CheckState.Checked if expected_visible else Qt.CheckState.Unchecked
        )

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_toggle_labels_limit_toggle_all_shapes(
    *,
    qtbot: QtBot,
    main_win: MainWinFactory,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    toggled = {"amber_kite", "green_hexagon"}
    win = _annotated_win_with_config(
        main_win=main_win,
        qtbot=qtbot,
        data_path=data_path,
        tmp_path=tmp_path,
        config_overrides={"toggle_labels": sorted(toggled)},
    )
    canvas = win._canvas_widgets.canvas

    win.toggle_shape_visibility(value=None)
    qtbot.wait(50)
    for shape in canvas.shapes:
        assert shape.visible is (shape.label not in toggled)

    win.toggle_shape_visibility(value=True)
    qtbot.wait(50)
    for shape in canvas.shapes:
        assert shape.visible

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_visibility_label_lists_from_cli(
    *,
    qtbot: QtBot,
    main_win: MainWinFactory,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    toggle_labels_file = tmp_path / "toggle_labels.txt"
    toggle_labels_file.write_text("amber_kite\n\nblue_block\n")
    win = main_win(
        file_or_dir=str(data_path / "annotated/2011_000003.json"),
        output_dir=str(tmp_path),
        extra_args=[
            "--checked-labels",
            "amber_kite,red_triangle",
            "--toggle-labels",
            str(toggle_labels_file),
        ],
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)

    assert win._config["checked_labels"] == ["amber_kite", "red_triangle"]
    assert win._config["toggle_labels"] == ["amber_kite", "blue_block"]

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)
