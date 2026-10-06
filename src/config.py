"""Чтение и проверка конфигурационного файла в формате CSV."""

import csv
import os
import re
from dataclasses import dataclass

KEY_COLUMN = "parameter"
VALUE_COLUMN = "value"
BOOL_TRUE = "true"
BOOL_FALSE = "false"
IMAGE_SUFFIX = ".png"
URL_PREFIXES = ("http://", "https://")
PACKAGE_PATTERN = re.compile(r"^[\w.\-]+:[\w.\-]+$")
TEST_PACKAGE_PATTERN = re.compile(r"^[A-Z]+$")
VERSION_PATTERN = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._\-]*$")
PARAMETERS = (
    "package_name",
    "repository",
    "test_mode",
    "version",
    "output_file",
    "ascii_tree",
    "filter_substring",
)

class ConfigError(Exception):
    """Ошибка чтения или проверки конфигурации."""

@dataclass
class Config:
    """Параметры, заданные пользователем."""

    package_name: str
    repository: str
    test_mode: bool
    version: str
    output_file: str
    ascii_tree: bool
    filter_substring: str

def parse_rows(reader):
    """Преобразовать строки CSV в словарь «параметр -> значение»."""
    if reader.fieldnames != [KEY_COLUMN, VALUE_COLUMN]:
        raise ConfigError(
            f"заголовок должен быть: {KEY_COLUMN},{VALUE_COLUMN}"
        )
    values = {}
    for row in reader:
        key = (row[KEY_COLUMN] or "").strip()
        if key in values:
            raise ConfigError(f"параметр задан повторно: {key}")
        values[key] = (row[VALUE_COLUMN] or "").strip()
    return values

def read_raw(path):
    """Прочитать CSV-файл и вернуть словарь параметров."""
    try:
        with open(path, newline="", encoding="utf-8") as file:
            return parse_rows(csv.DictReader(file))
    except FileNotFoundError as error:
        raise ConfigError(f"файл конфигурации не найден: {path}") from error
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise ConfigError(f"не удалось прочитать {path}: {error}") from error

def check_keys(values):
    """Проверить, что заданы все параметры и нет лишних."""
    unknown = [key for key in values if key not in PARAMETERS]
    if unknown:
        raise ConfigError("неизвестные параметры: " + ", ".join(unknown))
    missing = [key for key in PARAMETERS if key not in values]
    if missing:
        raise ConfigError("не заданы параметры: " + ", ".join(missing))

def parse_bool(name, text):
    """Преобразовать строку true/false в логическое значение."""
    lowered = text.lower()
    if lowered == BOOL_TRUE:
        return True
    if lowered == BOOL_FALSE:
        return False
    raise ConfigError(f"{name}: ожидается true или false, получено '{text}'")

def check_package(name, test_mode):
    """Проверить имя пакета: group:artifact или заглавные буквы."""
    if test_mode:
        pattern = TEST_PACKAGE_PATTERN
        expected = "заглавные латинские буквы, например A"
    else:
        pattern = PACKAGE_PATTERN
        expected = "группа:артефакт, например org.example:lib"
    if not pattern.match(name):
        raise ConfigError(f"package_name: ожидается {expected}, получено "
                          f"'{name}'")

def check_repository(repository, test_mode):
    """Проверить URL репозитория или путь к файлу тестового репозитория."""
    if not repository:
        raise ConfigError("repository: значение не задано")
    if test_mode:
        if not os.path.isfile(repository):
            raise ConfigError(f"repository: файл не найден: {repository}")
    elif not repository.startswith(URL_PREFIXES):
        raise ConfigError("repository: URL должен начинаться с http:// "
                          f"или https://, получено '{repository}'")

def check_version(version):
    """Проверить формат версии пакета."""
    if not VERSION_PATTERN.match(version):
        raise ConfigError(f"version: недопустимая версия '{version}'")

def check_output_file(output_file):
    """Проверить имя файла изображения: расширение и каталог."""
    lowered = output_file.lower()
    if not lowered.endswith(IMAGE_SUFFIX) or len(lowered) <= len(IMAGE_SUFFIX):
        raise ConfigError("output_file: имя должно заканчиваться на "
                          f"{IMAGE_SUFFIX}, получено '{output_file}'")
    directory = os.path.dirname(output_file)
    if directory and not os.path.isdir(directory):
        raise ConfigError(f"output_file: каталог не существует: {directory}")

def load_config(path):
    """Загрузить конфигурацию из CSV-файла и проверить все параметры."""
    values = read_raw(path)
    check_keys(values)
    test_mode = parse_bool("test_mode", values["test_mode"])
    ascii_tree = parse_bool("ascii_tree", values["ascii_tree"])
    check_package(values["package_name"], test_mode)
    check_repository(values["repository"], test_mode)
    check_version(values["version"])
    check_output_file(values["output_file"])
    return Config(
        package_name=values["package_name"],
        repository=values["repository"],
        test_mode=test_mode,
        version=values["version"],
        output_file=values["output_file"],
        ascii_tree=ascii_tree,
        filter_substring=values["filter_substring"],
    )
