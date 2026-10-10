from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Final

import pytest
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from labelme._app import MainWindow

from ..conftest import close_or_pause
from .conftest import MainWinFactory
from .conftest import show_window_and_wait_for_imagedata

_UNCHECKED: Final = "2011_000003"
_MANUAL: Final = "2011_000006"
_UNCHECKED_LAST: Final = "2011_000025"


@pytest.fixture()
def pages_dir(*, data_path: Path, tmp_path: Path) -> Path:
    # Имитация предразметки: флаг страницы checked=false и нет поля version.
    # Страница без ключа checked — ручная разметка.
    pages = tmp_path / "pages"
    shutil.copytree(data_path / "annotated", pages)
    for stem, flags in (
        (_UNCHECKED, {"checked": False}),
        (_MANUAL, {}),
        (_UNCHECKED_LAST, {"checked": False}),
    ):
        label_path = pages / f"{stem}.json"
        data = json.loads(label_path.read_text())
        data.pop("version")
        data["flags"] = flags
        label_path.write_text(json.dumps(data))
    return pages


def _read_label(*, pages_dir: Path, stem: str) -> dict:
    return json.loads((pages_dir / f"{stem}.json").read_text())


def _open_pages(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    pages_dir: Path,
    config_overrides: dict | None,
) -> MainWindow:
    win = main_win(file_or_dir=str(pages_dir), config_overrides=config_overrides)
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    assert Path(win._image_path or "").stem == _UNCHECKED
    return win


def _go_next(*, qtbot: QtBot, win: MainWindow) -> None:
    before = win._image_path
    win._actions.open_next_img.trigger()
    qtbot.waitUntil(lambda: win._image_path != before)


def _set_checked_flag(*, win: MainWindow, state: Qt.CheckState) -> None:
    flag_list = win._docks.flag_list
    items = flag_list.findItems("checked", Qt.MatchFlag.MatchExactly)
    assert len(items) == 1
    items[0].setCheckState(state)


@pytest.mark.gui
@pytest.mark.parametrize("auto_save", [True, False], ids=["auto_save", "manual_save"])
def test_leaving_unchecked_page_marks_it_checked_and_saves(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    pages_dir: Path,
    pause: bool,
    auto_save: bool,
) -> None:
    win = _open_pages(
        main_win=main_win,
        qtbot=qtbot,
        pages_dir=pages_dir,
        config_overrides={"auto_save": auto_save},
    )
    original_shapes = _read_label(pages_dir=pages_dir, stem=_UNCHECKED)["shapes"]

    _go_next(qtbot=qtbot, win=win)

    saved = _read_label(pages_dir=pages_dir, stem=_UNCHECKED)
    assert saved["flags"] == {"checked": True}
    assert "version" in saved
    assert saved["shapes"] == original_shapes
    assert not win._is_changed

    # Ручная разметка без ключа checked не трогается при уходе с неё.
    _go_next(qtbot=qtbot, win=win)
    manual = _read_label(pages_dir=pages_dir, stem=_MANUAL)
    assert manual["flags"] == {}
    assert "version" not in manual

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_manually_unchecked_page_stays_unchecked(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    pages_dir: Path,
    pause: bool,
) -> None:
    win = _open_pages(
        main_win=main_win, qtbot=qtbot, pages_dir=pages_dir, config_overrides=None
    )

    _set_checked_flag(win=win, state=Qt.CheckState.Checked)
    _set_checked_flag(win=win, state=Qt.CheckState.Unchecked)
    _go_next(qtbot=qtbot, win=win)

    assert _read_label(pages_dir=pages_dir, stem=_UNCHECKED)["flags"] == {
        "checked": False
    }

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_closing_or_reopening_folder_does_not_mark_page(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    pages_dir: Path,
    pause: bool,
) -> None:
    untouched = (pages_dir / f"{_UNCHECKED}.json").read_text()
    win = _open_pages(
        main_win=main_win, qtbot=qtbot, pages_dir=pages_dir, config_overrides=None
    )

    win._load_from_file_or_dir(file_or_dir=str(pages_dir))
    qtbot.waitUntil(lambda: Path(win._image_path or "").stem == _UNCHECKED)
    win.close_file()
    win.close()

    assert (pages_dir / f"{_UNCHECKED}.json").read_text() == untouched

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_page_that_failed_to_load_is_not_marked(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    pages_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    pause: bool,
) -> None:
    win = _open_pages(
        main_win=main_win, qtbot=qtbot, pages_dir=pages_dir, config_overrides=None
    )
    _go_next(qtbot=qtbot, win=win)
    assert Path(win._image_path or "").stem == _MANUAL

    corrupt = "{not json"
    (pages_dir / f"{_UNCHECKED_LAST}.json").write_text(corrupt)
    monkeypatch.setattr(win, "_show_file_open_error", lambda **_kwargs: None)

    # Страница с битой разметкой не загружается: остаёмся на прежней, а уход
    # с неё не трогает файл.
    win._actions.open_next_img.trigger()
    qtbot.wait(50)
    assert Path(win._image_path or "").stem == _MANUAL
    win._actions.open_prev_img.trigger()
    qtbot.waitUntil(lambda: Path(win._image_path or "").stem == _UNCHECKED)

    assert (pages_dir / f"{_UNCHECKED_LAST}.json").read_text() == corrupt

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)
