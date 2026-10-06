 depgraph

Инструмент визуализации графа зависимостей для пакетов Maven (вариант 21).
Написан на Python 3, сторонние библиотеки не используются.

## Текущее состояние

Реализован этап 1: чтение параметров из конфигурационного файла CSV,
их проверка и вывод в формате «ключ: значение».

## Конфигурационный файл

Файл в формате CSV с заголовком `parameter,value`. Каждая строка задаёт
один параметр, все параметры обязательны.

| Параметр | Описание |
|----------|----------|
| package_name | Имя пакета в виде `группа:артефакт`. В тестовом режиме: заглавные латинские буквы (A, B, AB) |
| repository | URL репозитория (http или https) или путь к файлу тестового репозитория |
| test_mode | Режим работы с тестовым репозиторием: `true` или `false` |
| version | Версия пакета, например `3.14.0` |
| output_file | Имя файла с изображением графа, должно заканчиваться на `.png` |
| ascii_tree | Вывод зависимостей в виде ASCII-дерева: `true` или `false` |
| filter_substring | Подстрока для фильтрации пакетов, может быть пустой |

При ошибке в конфигурации программа печатает сообщение в stderr и
завершается с кодом 1.

## Запуск

    make run

или с произвольным файлом конфигурации:

    python3 -m src.main путь/к/config.csv

## Тесты

    make test

## Пример использования

Файл `config.csv`:

    parameter,value
    package_name,org.apache.commons:commons-lang3
    repository,https://repo.maven.apache.org/maven2
    test_mode,false
    version,3.14.0
    output_file,graph.png
    ascii_tree,true
    filter_substring,test

Результат `make run`:

    package_name: org.apache.commons:commons-lang3
    repository: https://repo.maven.apache.org/maven2
    test_mode: false
    version: 3.14.0
    output_file: graph.png
    ascii_tree: true
    filter_substring: test
