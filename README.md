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
### Сравнение с Apache Maven

Для сравнения создавались проверочные проекты, зависящие от
анализируемого пакета (guava 32.1.3-jre и guice 5.1.0). Порядок
классов Maven получен командой `mvn dependency:build-classpath`, состав
и структура зависимостей командой `mvn dependency:tree`.

Результаты:

- Для guava состав пакетов совпал с Maven полностью (7 пакетов),
  различается только порядок.
- Версии всех общих пакетов у guice совпали с Maven (guava 30.1-jre,
  checker-qual 3.5.0, error_prone_annotations 2.3.4 и другие), то есть
  разрешение свойств, родительских pom и конфликтов версий работает так
  же, как в Maven.
- Для guice у нас 21 пакет, у Maven 10. Расхождения объяснены ниже.

Расхождения и их причины:

1. Порядок. Maven перечисляет пакет раньше его зависимостей (порядок
   обхода дерева зависимостей), а наш порядок топологический:
   зависимости стоят раньше потребителей, анализируемый пакет последний.
   Для независимых зависимостей порядок объявления сохраняется.
2. Состав для guice. Лишние 11 пакетов происходят от зависимостей самого
   guice, которые Maven не наследует: asm (область `optional`),
   javax.inject-tck, guava-testlib, bnd, org.apache.felix.framework и
   truth (область `test`), а также от их транзитивных зависимостей
   (junit, hamcrest-core, diffutils, auto-value-annotations,
   checker-compat-qual). Наш инструмент рассматривает анализируемый пакет
   как собственный проект и учитывает все области видимости его
   зависимостей, а в проверочном проекте Maven эти зависимости пакета не
   наследуются.
3. Не поддерживаются BOM-импорт, `exclusions` и диапазоны версий, из-за
   чего набор пакетов у некоторых артефактов может отличаться.

Результаты Maven и нашего инструмента для сравнения.

Maven (`build-classpath`), пакет com.google.guava:guava:32.1.3-jre:

    guava-32.1.3-jre.jar
    failureaccess-1.0.1.jar
    listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar
    jsr305-3.0.2.jar
    checker-qual-3.37.0.jar
    error_prone_annotations-2.21.1.jar
    j2objc-annotations-2.8.jar

Maven (`dependency:tree`), тот же пакет:

    check:check:jar:1.0
    \- com.google.guava:guava:jar:32.1.3-jre:compile
       +- com.google.guava:failureaccess:jar:1.0.1:compile
       +- com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
       +- com.google.code.findbugs:jsr305:jar:3.0.2:compile
       +- org.checkerframework:checker-qual:jar:3.37.0:compile
       +- com.google.errorprone:error_prone_annotations:jar:2.21.1:compile
       \- com.google.j2objc:j2objc-annotations:jar:2.8:compile

Наш инструмент, пакет com.google.inject:guice:5.1.0 (`examples/guice.csv`):

    Порядок загрузки зависимостей (пакетов: 21):
    1. org.hamcrest:hamcrest-core:1.3
    2. junit:junit:4.13
    3. javax.inject:javax.inject:1
    4. aopalliance:aopalliance:1.0
    5. com.google.guava:failureaccess:1.0.1
    6. com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
    7. com.google.code.findbugs:jsr305:3.0.2
    8. org.checkerframework:checker-qual:3.5.0
    9. com.google.errorprone:error_prone_annotations:2.3.4
    10. com.google.j2objc:j2objc-annotations:1.3
    11. com.google.guava:guava:30.1-jre
    12. org.ow2.asm:asm:9.2
    13. javax.inject:javax.inject-tck:1
    14. com.google.guava:guava-testlib:30.1-jre
    15. biz.aQute:bnd:0.0.384
    16. org.apache.felix:org.apache.felix.framework:3.0.5
    17. org.checkerframework:checker-compat-qual:2.5.5
    18. com.googlecode.java-diff-utils:diffutils:1.3.0
    19. com.google.auto.value:auto-value-annotations:1.6.3
    20. com.google.truth:truth:0.45
    21. com.google.inject:guice:5.1.0

Maven (`build-classpath`), пакет com.google.inject:guice:5.1.0:

    guice-5.1.0.jar
    javax.inject-1.jar
    aopalliance-1.0.jar
    guava-30.1-jre.jar
    failureaccess-1.0.1.jar
    listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar
    jsr305-3.0.2.jar
    checker-qual-3.5.0.jar
    error_prone_annotations-2.3.4.jar
    j2objc-annotations-1.3.jar

Maven (`dependency:tree`), тот же пакет:

    check:check:jar:1.0
    \- com.google.inject:guice:jar:5.1.0:compile
       +- javax.inject:javax.inject:jar:1:compile
       +- aopalliance:aopalliance:jar:1.0:compile
       \- com.google.guava:guava:jar:30.1-jre:compile
          +- com.google.guava:failureaccess:jar:1.0.1:compile
          +- com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
          +- com.google.code.findbugs:jsr305:jar:3.0.2:compile
          +- org.checkerframework:checker-qual:jar:3.5.0:compile
          +- com.google.errorprone:error_prone_annotations:jar:2.3.4:compile
          \- com.google.j2objc:j2objc-annotations:jar:1.3:compile
