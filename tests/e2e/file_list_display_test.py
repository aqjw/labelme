from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from labelme._app import file_list_item_image_path

from ..conftest import close_or_pause
from .conftest import MainWinFactory
from .conftest import show_window_and_wait_for_imagedata


@pytest.mark.gui
def test_file_list_shows_paths_relative_to_opened_dir(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    root = tmp_path / "dataset"
    (root / "chapter_2").mkdir(parents=True)
    shutil.copy(data_path / "raw/2011_000003.jpg", root / "001.jpg")
    shutil.copy(data_path / "raw/2011_000006.jpg", root / "chapter_2/001.jpg")

    win = main_win(file_or_dir=str(root), output_dir=str(tmp_path / "out"))
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    file_list = win._docks.file_list

    items = [file_list.item(row) for row in range(file_list.count())]
    assert all(item is not None for item in items)
    shown = {item.text(): file_list_item_image_path(item) for item in items if item}
    assert set(shown) == {"001.jpg", str(Path("chapter_2/001.jpg"))}
    for text, image_path in shown.items():
        assert Path(image_path).resolve() == (root / text).resolve()
    for item in items:
        assert item is not None
        assert item.toolTip() == file_list_item_image_path(item)

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_file_list_bookmark_icon_fits_text_row(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = main_win(file_or_dir=str(data_path / "raw"), output_dir=str(tmp_path))
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    file_list = win._docks.file_list

    assert file_list.iconSize().height() <= file_list.fontMetrics().height()

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)
