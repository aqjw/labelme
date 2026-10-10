from __future__ import annotations

from pathlib import Path

import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import QTimer
from pytestqt.qtbot import QtBot

from labelme._app import MainWindow

from ..conftest import close_or_pause
from .conftest import MainWinFactory
from .conftest import show_window_and_wait_for_imagedata


def _open_raw_dir(
    *, main_win: MainWinFactory, qtbot: QtBot, data_path: Path, tmp_path: Path
) -> MainWindow:
    win = main_win(file_or_dir=str(data_path / "raw"), output_dir=str(tmp_path))
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    return win


def _open_row(*, qtbot: QtBot, win: MainWindow, row: int) -> str:
    image_path = win.image_list[row]
    win._docks.file_list.setCurrentRow(row)
    qtbot.waitUntil(lambda: win._file_list_image_path == image_path)
    return image_path


def _bookmarked_rows(*, win: MainWindow) -> list[int]:
    file_list = win._docks.file_list
    rows = []
    for row in range(file_list.count()):
        item = file_list.item(row)
        assert item is not None
        if item.font().bold():
            assert not item.icon().isNull()
            rows.append(row)
        else:
            assert item.icon().isNull()
    return rows


@pytest.mark.gui
def test_bookmark_marks_single_image_and_survives_reopen(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = _open_raw_dir(
        main_win=main_win, qtbot=qtbot, data_path=data_path, tmp_path=tmp_path
    )
    assert _bookmarked_rows(win=win) == []

    _open_row(qtbot=qtbot, win=win, row=1)
    win._actions.toggle_bookmark.trigger()
    assert _bookmarked_rows(win=win) == [1]
    assert win._actions.toggle_bookmark.isChecked()

    # Закладка одна: новая заменяет прежнюю.
    bookmarked = _open_row(qtbot=qtbot, win=win, row=2)
    win._actions.toggle_bookmark.trigger()
    assert _bookmarked_rows(win=win) == [2]
    win.close()

    reopened = _open_raw_dir(
        main_win=main_win, qtbot=qtbot, data_path=data_path, tmp_path=tmp_path
    )
    assert reopened._file_list_image_path == bookmarked
    assert _bookmarked_rows(win=reopened) == [2]

    close_or_pause(qtbot=qtbot, widget=reopened, pause=pause)


@pytest.mark.gui
def test_go_to_bookmark_and_remove_it(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = _open_raw_dir(
        main_win=main_win, qtbot=qtbot, data_path=data_path, tmp_path=tmp_path
    )
    assert not win._actions.go_to_bookmark.isEnabled()

    bookmarked = _open_row(qtbot=qtbot, win=win, row=1)
    win._actions.toggle_bookmark.trigger()
    assert not win._actions.go_to_bookmark.isEnabled()

    _open_row(qtbot=qtbot, win=win, row=0)
    assert not win._actions.toggle_bookmark.isChecked()
    assert win._actions.go_to_bookmark.isEnabled()
    win._actions.go_to_bookmark.trigger()
    qtbot.waitUntil(lambda: win._file_list_image_path == bookmarked)

    win._actions.toggle_bookmark.trigger()
    assert _bookmarked_rows(win=win) == []
    assert not win._actions.toggle_bookmark.isChecked()

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_file_list_menu_toggles_bookmark_without_opening_image(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = _open_raw_dir(
        main_win=main_win, qtbot=qtbot, data_path=data_path, tmp_path=tmp_path
    )
    opened = win._file_list_image_path
    file_list = win._docks.file_list
    item = file_list.item(2)
    assert item is not None
    pos = file_list.visualItemRect(item).center()

    def _trigger_menu_action(*, text: str) -> None:
        def _click() -> None:
            menu = QtWidgets.QApplication.activePopupWidget()
            if not isinstance(menu, QtWidgets.QMenu):
                QTimer.singleShot(20, _click)
                return
            (action,) = menu.actions()
            assert action.text() == text
            action.trigger()
            menu.close()

        QTimer.singleShot(0, _click)
        win._show_file_list_menu(pos)

    _trigger_menu_action(text=win.tr("Set Bookmark"))
    assert _bookmarked_rows(win=win) == [2]
    assert win._file_list_image_path == opened

    _trigger_menu_action(text=win.tr("Remove Bookmark"))
    assert _bookmarked_rows(win=win) == []

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_bookmark_unavailable_for_label_file(
    *,
    annotated_win: MainWindow,
    qtbot: QtBot,
    pause: bool,
) -> None:
    assert not annotated_win._actions.toggle_bookmark.isEnabled()
    assert not annotated_win._actions.go_to_bookmark.isEnabled()

    close_or_pause(qtbot=qtbot, widget=annotated_win, pause=pause)
