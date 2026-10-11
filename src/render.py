"""Сохранение диаграммы D2 и отрисовка PNG утилитой d2."""

import os
import shutil
import subprocess

D2_BINARY = "d2"
D2_SUFFIX = ".d2"
SUCCESS_CODE = 0
RENDER_TIMEOUT_SECONDS = 300


class RenderError(Exception):
    """Ошибка сохранения диаграммы или отрисовки изображения."""


def d2_path_for(image_path):
    """Вернуть путь к файлу D2, лежащему рядом с изображением."""
    return os.path.splitext(image_path)[0] + D2_SUFFIX


def save_text(path, lines):
    """Записать строки в текстовый файл."""
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")
    except OSError as error:
        raise RenderError(f"не удалось записать {path}: {error}") from error


def render_png(d2_path, image_path):
    """Отрисовать файл D2 в PNG с помощью утилиты d2."""
    binary = shutil.which(D2_BINARY)
    if binary is None:
        raise RenderError("утилита d2 не найдена, установите её: d2lang.com")
    try:
        result = subprocess.run(
            [binary, d2_path, image_path],
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RenderError(f"не удалось запустить d2: {error}") from error
    if result.returncode != SUCCESS_CODE:
        raise RenderError(f"d2 завершилась с ошибкой: {result.stderr.strip()}")


def save_diagram(d2_lines, image_path):
    """Сохранить текст D2 рядом с изображением и отрисовать PNG.

    Возвращает путь к созданному файлу D2.
    """
    d2_path = d2_path_for(image_path)
    save_text(d2_path, d2_lines)
    render_png(d2_path, image_path)
    return d2_path
