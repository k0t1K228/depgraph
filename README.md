# depgraph

Инструмент визуализации графа зависимостей для пакетов Maven (вариант 21).
Написан на Python 3, сторонние библиотеки и менеджеры пакетов для получения
зависимостей не используются: pom.xml скачивается и разбирается
стандартными средствами языка.

## Текущее состояние

Реализованы этапы:

1. Чтение параметров из конфигурационного файла CSV, их проверка.
2. Получение прямых зависимостей пакета Maven по URL репозитория.
3. Построение графа зависимостей (с учётом транзитивности) обходом в
   ширину, фильтрация пакетов, обработка циклов, тестовый режим.

## Конфигурационный файл

Файл в формате CSV с заголовком `parameter,value`. Каждая строка задаёт
один параметр, все параметры обязательны.

| Параметр | Описание |
|----------|----------|
| package_name | Имя пакета в виде `группа:артефакт`. В тестовом режиме: заглавные латинские буквы (A, B, AB) |
| repository | URL репозитория (http или https) или путь к файлу тестового репозитория |
| test_mode | Режим работы с тестовым репозиторием: `true` или `false` |
| version | Версия пакета, например `3.14.0` (в тестовом режиме не используется) |
| output_file | Имя файла с изображением графа, должно заканчиваться на `.png` |
| ascii_tree | Вывод зависимостей в виде ASCII-дерева: `true` или `false` |
| filter_substring | Подстрока для фильтрации пакетов, может быть пустой |

Параметры `output_file` и `ascii_tree` проверяются уже сейчас, но
используются на этапе 5.

## Как строится граф

1. Из `package_name` и `version` строится URL файла pom.xml в репозитории
   Maven: `<repository>/<группа с / вместо точек>/<артефакт>/<версия>/`
   `<артефакт>-<версия>.pom`.
2. pom.xml скачивается модулем `urllib` и разбирается как XML. Для
   родительских pom (`parent`) цепочка загружается до корня. Подставляются
   свойства `${имя}` и версии из `dependencyManagement`.
3. Граф строится обходом в ширину (BFS) с очередью, без рекурсии.
   Вершина имеет вид `группа:артефакт:версия`.
4. У корневого пакета учитываются зависимости любой области видимости.
   У остальных пакетов только `compile` и `runtime`, без `optional`.
5. Если пакет встречается в разных версиях, выбирается версия,
   ближайшая к корню (как в Maven).
6. Пакеты, чьё имя (`группа:артефакт`) содержит `filter_substring`, не
   анализируются вместе с поддеревом, достижимым только через них.
   Корневой пакет не фильтруется. Пустая подстрока ничего не исключает.
7. Циклические зависимости обрабатываются: каждая вершина разбирается
   один раз, рёбра, замыкающие цикл, остаются в графе.

Если для вершины (кроме корня) не удалось получить pom.xml, в stderr
выводится предупреждение, а вершина считается пакетом без зависимостей.

## Тестовый режим

При `test_mode,true` в `repository` указывается путь к файлу описания
графа. Каждая строка: `ПАКЕТ: ЗАВИСИМОСТЬ1 ЗАВИСИМОСТЬ2`. Имена
состоят из заглавных латинских букв. Пакет без зависимостей:
`D:`. Пакет, упомянутый только как зависимость, считается листом.
Примеры лежат в папке `examples/`.

## Ограничения

- Не поддерживается импорт BOM (`scope import` в `dependencyManagement`).
- Не учитываются профили Maven, исключения (`exclusions`) и диапазоны
  версий.

## Обработка ошибок

При ошибке конфигурации, недоступности репозитория, отсутствии пакета,
некорректном pom.xml или файле тестового репозитория программа печатает
сообщение в stderr и завершается с кодом 1.

## Запуск

    make run

или с произвольным файлом конфигурации:

    python3 -m src.main путь/к/config.csv

## Тесты

    make test

Тесты используют подмену сетевых запросов, интернет для них не нужен.

## Примеры использования

Тестовый режим, `python3 -m src.main examples/test_config.csv`:

    Граф зависимостей (BFS), вершин: 5
    A -> B, C
    B -> D
    C -> D, E
    D -> (нет)
    E -> (нет)

Граф с циклом (`examples/repo_cycle.txt`):

    Граф зависимостей (BFS), вершин: 4
    A -> B
    B -> C
    C -> A, D
    D -> (нет)

Тот же репозиторий `repo_basic.txt` с `filter_substring,D` исключает
пакет D:

    Граф зависимостей (BFS), вершин: 4
    A -> B, C
    B -> (нет)
    C -> E
    E -> (нет)

parameter,value
package_name,com.google.guava:guava
repository,https://repo.maven.apache.org/maven2
test_mode,false
version,32.1.3-jre
output_file,graph.png
ascii_tree,true
filter_substring,

Реальный репозиторий Maven Central, пакет com.google.guava:guava:32.1.3-jre (`examples/guava.csv`):

    Граф зависимостей (BFS), вершин: 7
    com.google.guava:guava:32.1.3-jre -> com.google.guava:failureaccess:1.0.1, com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava, com.google.code.findbugs:jsr305:3.0.2, org.checkerframework:checker-qual:3.37.0, com.google.errorprone:error_prone_annotations:2.21.1, com.google.j2objc:j2objc-annotations:2.8
    com.google.guava:failureaccess:1.0.1 -> (нет)
    com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava -> (нет)
    com.google.code.findbugs:jsr305:3.0.2 -> (нет)
    org.checkerframework:checker-qual:3.37.0 -> (нет)
    com.google.errorprone:error_prone_annotations:2.21.1 -> (нет)
    com.google.j2objc:j2objc-annotations:2.8 -> (нет)

Пакет org.apache.commons:commons-lang3:3.14.0 (`config.csv`):

    Граф зависимостей (BFS), вершин: 15
    org.apache.commons:commons-lang3:3.14.0 -> org.junit.jupiter:junit-jupiter:?, org.junit-pioneer:junit-pioneer:1.9.1, org.hamcrest:hamcrest:2.2, org.easymock:easymock:5.2.0, org.apache.commons:commons-text:1.11.0, org.openjdk.jmh:jmh-core:1.37, org.openjdk.jmh:jmh-generator-annprocess:1.37, com.google.code.findbugs:jsr305:3.0.2
    org.junit.jupiter:junit-jupiter:? -> (нет)
    org.junit-pioneer:junit-pioneer:1.9.1 -> org.junit.jupiter:junit-jupiter-api:?, org.junit.jupiter:junit-jupiter-params:?, org.junit.platform:junit-platform-launcher:?
    org.hamcrest:hamcrest:2.2 -> (нет)
    org.easymock:easymock:5.2.0 -> org.objenesis:objenesis:3.3
    org.apache.commons:commons-text:1.11.0 -> org.apache.commons:commons-lang3:3.14.0
    org.openjdk.jmh:jmh-core:1.37 -> net.sf.jopt-simple:jopt-simple:5.0.4, org.apache.commons:commons-math3:3.6.1
    org.openjdk.jmh:jmh-generator-annprocess:1.37 -> org.openjdk.jmh:jmh-core:1.37
    com.google.code.findbugs:jsr305:3.0.2 -> (нет)
    org.junit.jupiter:junit-jupiter-api:? -> (нет)
    org.junit.jupiter:junit-jupiter-params:? -> (нет)
    org.junit.platform:junit-platform-launcher:? -> (нет)
    org.objenesis:objenesis:3.3 -> (нет)
    net.sf.jopt-simple:jopt-simple:5.0.4 -> (нет)
    org.apache.commons:commons-math3:3.6.1 -> (нет)
