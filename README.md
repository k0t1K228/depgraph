# depgraph

Инструмент визуализации графа зависимостей для пакетов Maven (вариант 21).
Написан на Python 3. Для получения зависимостей не используются
менеджеры пакетов и сторонние библиотеки: pom.xml скачивается и
разбирается стандартными средствами языка. Диаграммы строятся на языке D2.

## Текущее состояние

Реализованы все этапы:

1. Чтение параметров из конфигурационного файла CSV, их проверка.
2. Получение прямых зависимостей пакета Maven по URL репозитория.
3. Граф зависимостей с учётом транзитивности (обход в ширину),
   фильтрация пакетов, обработка циклов, тестовый режим.
4. Режим вывода порядка загрузки зависимостей (флаг `--load-order`).
5. Визуализация: диаграмма D2, PNG, ASCII-дерево (флаг `--visualize`).

## Конфигурационный файл

Файл в формате CSV с заголовком `parameter,value`. Каждая строка задаёт
один параметр, все параметры обязательны.

| Параметр | Описание |
|----------|----------|
| package_name | Имя пакета в виде `группа:артефакт`. В тестовом режиме: заглавные латинские буквы (A, B, AB) |
| repository | URL репозитория (http или https) или путь к файлу тестового репозитория |
| test_mode | Режим работы с тестовым репозиторием: `true` или `false` |
| version | Версия пакета, например `3.14.0` (в тестовом режиме не используется) |
| output_file | Имя файла с изображением графа, должно заканчиваться на `.png`, каталог должен существовать |
| ascii_tree | Вывод зависимостей в виде ASCII-дерева: `true` или `false` |
| filter_substring | Подстрока для фильтрации пакетов, может быть пустой |

## Как строится граф

1. Из `package_name` и `version` строится URL файла pom.xml в репозитории
   Maven: `<repository>/<группа с / вместо точек>/<артефакт>/<версия>/`
   `<артефакт>-<версия>.pom`.
2. pom.xml скачивается модулем `urllib` и разбирается как XML. Для
   родительских pom (`parent`) цепочка загружается до корня. Подставляются
   свойства `${имя}` (в том числе `project.*` и `pom.*`) и версии из
   `dependencyManagement`.
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
  Версии зависимостей, заданные только в BOM, выводятся как `?`
  (например, `junit-jupiter` и `log4j-api` у commons-configuration2).
- Не учитываются профили Maven, исключения (`exclusions`) и диапазоны
  версий.
- Для PNG нужна установленная утилита `d2`.

## Обработка ошибок

При ошибке конфигурации, недоступности репозитория, отсутствии пакета,
некорректном pom.xml, файле тестового репозитория или отсутствии утилиты
`d2` программа печатает сообщение в stderr и завершается с кодом 1.

## Запуск

    python3 -m src.main config.csv                 граф зависимостей
    python3 -m src.main config.csv --load-order    порядок загрузки
    python3 -m src.main config.csv --visualize     диаграмма D2 и PNG

Для запуска с конфигурацией `config.csv` в корне репозитория:

    make run

## Тесты

    make test

Тесты используют подмену сетевых запросов и утилиты d2, интернет для них
не нужен.

## Граф зависимостей (этап 3)

Тестовый репозиторий `examples/repo_basic.txt`
(`python3 -m src.main examples/test_config.csv`):

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

Петля, возврат к корню и неописанный пакет (`examples/repo_complex.txt`):

    Граф зависимостей (BFS), вершин: 5
    A -> B, C
    B -> B, D
    C -> A
    D -> X
    X -> (нет)

Фильтрация (`repo_basic.txt` с `filter_substring,D`): пакет D и его
зависимости не анализируются:

    Граф зависимостей (BFS), вершин: 4
    A -> B, C
    B -> (нет)
    C -> E
    E -> (нет)

## Порядок загрузки зависимостей (этап 4)

Флаг `--load-order` включает режим, в котором вместо графа выводится
порядок загрузки: каждый пакет стоит после всех своих зависимостей, а
корневой пакет последний. Порядок вычисляется обходом в глубину без
рекурсии, независимые зависимости идут в порядке объявления. Ребро,
замыкающее цикл, пропускается и выводится отдельным списком.

Обычный граф (`examples/repo_basic.txt`):

    Порядок загрузки зависимостей (пакетов: 5):
    1. D
    2. B
    3. E
    4. C
    5. A

Граф с циклом (`examples/repo_cycle.txt`):

    Порядок загрузки зависимостей (пакетов: 4):
    1. D
    2. C
    3. B
    4. A
    Циклические зависимости (ребро пропущено):
      C -> A

Петля, возврат к корню и неописанный пакет (`examples/repo_complex.txt`):

    Порядок загрузки зависимостей (пакетов: 5):
    1. X
    2. D
    3. B
    4. C
    5. A
    Циклические зависимости (ребро пропущено):
      B -> B
      C -> A

Фильтрация (`repo_basic.txt` с `filter_substring,D`):

    Порядок загрузки зависимостей (пакетов: 4):
    1. B
    2. E
    3. C
    4. A

Реальный репозиторий, `com.google.guava:guava:32.1.3-jre`
(`examples/guava.csv`):

    Порядок загрузки зависимостей (пакетов: 7):
    1. com.google.guava:failureaccess:1.0.1
    2. com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
    3. com.google.code.findbugs:jsr305:3.0.2
    4. org.checkerframework:checker-qual:3.37.0
    5. com.google.errorprone:error_prone_annotations:2.21.1
    6. com.google.j2objc:j2objc-annotations:2.8
    7. com.google.guava:guava:32.1.3-jre

### Сравнение порядка с Apache Maven

Для сравнения создавались проверочные проекты, зависящие от
анализируемого пакета. Порядок Maven получен командой
`mvn dependency:build-classpath`, состав зависимостей командой
`mvn dependency:tree`. Результаты приведены в последнем разделе.

Для guava состав пакетов совпал полностью (7 пакетов), для guice версии
всех общих пакетов совпали с Maven (guava 30.1-jre, checker-qual 3.5.0,
error_prone_annotations 2.3.4 и другие).

Расхождения и их причины:

1. Порядок. Maven перечисляет пакет раньше его зависимостей (порядок
   обхода дерева зависимостей), а наш порядок топологический:
   зависимости стоят раньше потребителей, анализируемый пакет последний.
   Для независимых зависимостей порядок объявления сохраняется.
2. Состав для guice: у нас 21 пакет, у Maven 10. Лишние 11 пакетов
   происходят от зависимостей самого guice, которые Maven не наследует:
   asm (область `optional`), javax.inject-tck, guava-testlib, bnd,
   org.apache.felix.framework и truth (область `test`), а также от их
   транзитивных зависимостей (junit, hamcrest-core, diffutils,
   auto-value-annotations, checker-compat-qual). Наш инструмент
   рассматривает анализируемый пакет как собственный проект и учитывает
   все области видимости его зависимостей, а в проверочном проекте Maven
   эти зависимости пакета не наследуются.
3. Не поддерживаются BOM-импорт, `exclusions` и диапазоны версий, из-за
   чего набор пакетов у некоторых артефактов может отличаться.

## Визуализация (этап 5)

Параметр `ascii_tree,true` в конфигурации включает вывод зависимостей
в виде ASCII-дерева. Узел раскрывается там, где он встречается ближе
всего к корню (как в дереве разрешённых зависимостей Maven), остальные
вхождения помечаются `(*)` и не раскрываются. Узел, замыкающий цикл,
помечается `(цикл)`. Дерево строится обходом в глубину без рекурсии.

Флаг `--visualize` сохраняет граф на языке диаграмм D2 в файл `.d2` (рядом
с изображением, имя берётся из параметра `output_file`) и отрисовывает
PNG утилитой `d2`:

    python3 -m src.main examples/guava.csv --visualize

Установка утилиты d2 (https://d2lang.com):

    curl -fsSL https://d2lang.com/install.sh | sh -s --

Файлы PNG в репозиторий не добавляются (это бинарные файлы, они
перечислены в `.gitignore`), в репозитории хранятся только текстовые
файлы `.d2`: `examples/guava.d2`, `examples/guice.d2`,
`examples/commons.d2`.

В D2-диаграмме вершины получают короткие идентификаторы n0, n1, ...,
а полное имя пакета записывается в метку, так как символы `.` и `:` в
ключах D2 имеют особый смысл. Корневой пакет выделяется цветом.

### Примеры на тестовом репозитории

`examples/repo_cycle.txt` с `ascii_tree,true`:

    A
    └── B
        └── C
            ├── A (цикл)
            └── D

`examples/repo_basic.txt` с `ascii_tree,true`:

    A
    ├── B
    │   └── D
    └── C
        ├── D (*)
        └── E

D2-представление графа `examples/repo_cycle.txt`:

    direction: right

    n0: 'A'
    n1: 'B'
    n2: 'C'
    n3: 'D'
    n0.style.fill: "#cfe8ff"

    n0 -> n1
    n1 -> n2
    n2 -> n0
    n2 -> n3

### Сравнение с Apache Maven

В качестве штатного инструмента использовалась команда
`mvn dependency:tree` для проверочных проектов, зависящих от трёх
пакетов: guava 32.1.3-jre, guice 5.1.0 и commons-configuration2 2.9.0.
Результаты приведены в последнем разделе.

Для commons-configuration2 зависимости области `compile` (commons-lang3,
commons-text, commons-logging) совпали с Maven и идут в том же порядке.

Расхождения и их причины:

1. Повторы и циклы. Maven выводит каждый артефакт один раз и не
   показывает повторные вхождения, а наш инструмент оставляет их с
   пометкой `(*)` и помечает циклы, поэтому наше дерево длиннее (например,
   у commons-text зависимость commons-lang3 у нас присутствует с `(*)`,
   а у Maven её под commons-text нет).
2. Формат строк. Maven выводит `группа:артефакт:тип:версия:область`,
   наш инструмент `группа:артефакт:версия`. Символы ветвей различаются.
3. Корень. В выводе Maven первым стоит проверочный проект, а у нас корнем
   является сам анализируемый пакет, поэтому дерево Maven на уровень
   глубже.
4. Область видимости. Анализируемый пакет рассматривается как собственный
   проект, поэтому учитываются зависимости корня с областями `test` и
   `optional`, которые Maven у зависимости не наследует. У
   commons-configuration2 Maven показывает 3 зависимости, а наш
   инструмент ещё и десятки необязательных и тестовых.
5. Не поддерживаются BOM-импорт, `exclusions` и диапазоны версий:
   версии, заданные в BOM, выводятся как `?`.

## Результаты сравнения с Apache Maven

Выводы получены на реальном репозитории Maven Central. Для каждого пакета
приведены вывод нашего инструмента и вывод Maven.

### com.google.guava:guava:32.1.3-jre

Порядок загрузки, наш инструмент (`--load-order`):

    Порядок загрузки зависимостей (пакетов: 7):
    1. com.google.guava:failureaccess:1.0.1
    2. com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
    3. com.google.code.findbugs:jsr305:3.0.2
    4. org.checkerframework:checker-qual:3.37.0
    5. com.google.errorprone:error_prone_annotations:2.21.1
    6. com.google.j2objc:j2objc-annotations:2.8
    7. com.google.guava:guava:32.1.3-jre

Порядок загрузки, Maven (`build-classpath`):

    guava-32.1.3-jre.jar
    failureaccess-1.0.1.jar
    listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar
    jsr305-3.0.2.jar
    checker-qual-3.37.0.jar
    error_prone_annotations-2.21.1.jar
    j2objc-annotations-2.8.jar

Дерево зависимостей, наш инструмент (`ascii_tree,true`):

    com.google.guava:guava:32.1.3-jre
    ├── com.google.guava:failureaccess:1.0.1
    ├── com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
    ├── com.google.code.findbugs:jsr305:3.0.2
    ├── org.checkerframework:checker-qual:3.37.0
    ├── com.google.errorprone:error_prone_annotations:2.21.1
    └── com.google.j2objc:j2objc-annotations:2.8

Дерево зависимостей, Maven (`dependency:tree`):

    check:check:jar:1.0
    \- com.google.guava:guava:jar:32.1.3-jre:compile
       +- com.google.guava:failureaccess:jar:1.0.1:compile
       +- com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
       +- com.google.code.findbugs:jsr305:jar:3.0.2:compile
       +- org.checkerframework:checker-qual:jar:3.37.0:compile
       +- com.google.errorprone:error_prone_annotations:jar:2.21.1:compile
       \- com.google.j2objc:j2objc-annotations:jar:2.8:compile

### com.google.inject:guice:5.1.0

Порядок загрузки, наш инструмент (`--load-order`):

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

Порядок загрузки, Maven (`build-classpath`):

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

Дерево зависимостей, наш инструмент (`ascii_tree,true`):

    com.google.inject:guice:5.1.0
    ├── junit:junit:4.13
    │   └── org.hamcrest:hamcrest-core:1.3
    ├── javax.inject:javax.inject:1
    ├── aopalliance:aopalliance:1.0
    ├── com.google.guava:guava:30.1-jre
    │   ├── com.google.guava:failureaccess:1.0.1
    │   ├── com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
    │   ├── com.google.code.findbugs:jsr305:3.0.2
    │   ├── org.checkerframework:checker-qual:3.5.0
    │   ├── com.google.errorprone:error_prone_annotations:2.3.4
    │   └── com.google.j2objc:j2objc-annotations:1.3
    ├── org.ow2.asm:asm:9.2
    ├── javax.inject:javax.inject-tck:1
    │   ├── javax.inject:javax.inject:1 (*)
    │   └── junit:junit:4.13 (*)
    ├── com.google.guava:guava-testlib:30.1-jre
    │   ├── com.google.code.findbugs:jsr305:3.0.2 (*)
    │   ├── org.checkerframework:checker-qual:3.5.0 (*)
    │   ├── com.google.errorprone:error_prone_annotations:2.3.4 (*)
    │   ├── com.google.j2objc:j2objc-annotations:1.3 (*)
    │   ├── com.google.guava:guava:30.1-jre (*)
    │   └── junit:junit:4.13 (*)
    ├── biz.aQute:bnd:0.0.384
    ├── org.apache.felix:org.apache.felix.framework:3.0.5
    └── com.google.truth:truth:0.45
        ├── com.google.guava:guava:30.1-jre (*)
        ├── org.checkerframework:checker-compat-qual:2.5.5
        ├── junit:junit:4.13 (*)
        ├── com.googlecode.java-diff-utils:diffutils:1.3.0
        ├── com.google.auto.value:auto-value-annotations:1.6.3
        └── com.google.errorprone:error_prone_annotations:2.3.4 (*)

Дерево зависимостей, Maven (`dependency:tree`):

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

### org.apache.commons:commons-configuration2:2.9.0

Дерево зависимостей, наш инструмент (`ascii_tree,true`):

    org.apache.commons:commons-configuration2:2.9.0
    ├── org.apache.commons:commons-lang3:3.12.0
    ├── org.apache.commons:commons-text:1.10.0
    │   └── org.apache.commons:commons-lang3:3.12.0 (*)
    ├── commons-logging:commons-logging:1.2
    ├── commons-beanutils:commons-beanutils:1.9.4
    │   ├── commons-logging:commons-logging:1.2 (*)
    │   └── commons-collections:commons-collections:3.2.2
    ├── commons-codec:commons-codec:1.15
    ├── org.apache.commons:commons-jexl:2.1.1
    │   └── commons-logging:commons-logging:1.2 (*)
    ├── org.apache.commons:commons-vfs2:2.9.0
    │   ├── commons-logging:commons-logging:1.2 (*)
    │   ├── org.apache.hadoop:hadoop-hdfs-client:3.3.1
    │   │   ├── com.squareup.okhttp:okhttp:2.7.5
    │   │   │   └── com.squareup.okio:okio:1.6.0
    │   │   ├── com.fasterxml.jackson.core:jackson-annotations:2.14.2 (*)
    │   │   └── com.fasterxml.jackson.core:jackson-databind:2.14.2 (*)
    │   └── org.apache.commons:commons-lang3:3.12.0 (*)
    ├── commons-jxpath:commons-jxpath:1.3
    ├── xml-resolver:xml-resolver:1.2
    ├── org.springframework:spring-core:5.3.26
    │   └── org.springframework:spring-jcl:5.3.26
    ├── org.springframework:spring-beans:5.3.26
    │   └── org.springframework:spring-core:5.3.26 (*)
    ├── org.springframework:spring-context:5.3.26
    │   ├── org.springframework:spring-aop:5.3.26
    │   │   ├── org.springframework:spring-beans:5.3.26 (*)
    │   │   └── org.springframework:spring-core:5.3.26 (*)
    │   ├── org.springframework:spring-beans:5.3.26 (*)
    │   ├── org.springframework:spring-core:5.3.26 (*)
    │   └── org.springframework:spring-expression:5.3.26
    │       └── org.springframework:spring-core:5.3.26 (*)
    ├── org.springframework:spring-test:5.3.26
    │   └── org.springframework:spring-core:5.3.26 (*)
    ├── javax.servlet:servlet-api:2.5
    ├── org.yaml:snakeyaml:2.0
    ├── com.fasterxml.jackson.core:jackson-databind:2.14.2
    │   ├── com.fasterxml.jackson.core:jackson-annotations:2.14.2
    │   └── com.fasterxml.jackson.core:jackson-core:2.14.2
    ├── org.apache.commons:commons-dbcp2:2.9.0
    │   ├── org.apache.commons:commons-pool2:2.11.1 (*)
    │   └── commons-logging:commons-logging:1.2 (*)
    ├── commons-io:commons-io:2.11.0
    ├── org.apache.commons:commons-pool2:2.11.1
    ├── org.hsqldb:hsqldb:2.5.2
    ├── org.dbunit:dbunit:2.7.3
    │   ├── org.slf4j:slf4j-api:2.0.7 (*)
    │   ├── com.h2database:h2:1.1.118
    │   ├── hsqldb:hsqldb:1.8.0.1
    │   └── org.postgresql:postgresql:42.3.1
    │       └── org.checkerframework:checker-qual:3.5.0
    ├── org.junit.jupiter:junit-jupiter:?
    ├── org.hamcrest:hamcrest:2.2
    ├── org.mockito:mockito-core:4.11.0
    │   ├── net.bytebuddy:byte-buddy:1.12.19
    │   ├── net.bytebuddy:byte-buddy-agent:1.12.19
    │   └── org.objenesis:objenesis:3.3
    ├── com.sun.mail:mailapi:2.0.1
    │   └── com.sun.activation:jakarta.activation:2.0.1
    ├── org.apache.logging.log4j:log4j-1.2-api:2.20.0
    │   └── org.apache.logging.log4j:log4j-api:?
    ├── org.apache.logging.log4j:log4j-core:2.20.0
    │   └── org.apache.logging.log4j:log4j-api:? (*)
    ├── org.slf4j:slf4j-api:2.0.7
    ├── org.slf4j:slf4j-ext:2.0.7
    │   └── org.slf4j:slf4j-api:2.0.7 (*)
    ├── org.slf4j:slf4j-log4j12:2.0.7
    └── org.slf4j:slf4j-nop:2.0.7
        └── org.slf4j:slf4j-api:2.0.7 (*)

Дерево зависимостей, Maven (`dependency:tree`):

    check:check:jar:1.0
    \- org.apache.commons:commons-configuration2:jar:2.9.0:compile
       +- org.apache.commons:commons-lang3:jar:3.12.0:compile
       +- org.apache.commons:commons-text:jar:1.10.0:compile
       \- commons-logging:commons-logging:jar:1.2:compile

### Диаграмма D2 для guava (`examples/guava.d2`)

    direction: right
    
    n0: 'com.google.guava:guava:32.1.3-jre'
    n1: 'com.google.guava:failureaccess:1.0.1'
    n2: 'com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava'
    n3: 'com.google.code.findbugs:jsr305:3.0.2'
    n4: 'org.checkerframework:checker-qual:3.37.0'
    n5: 'com.google.errorprone:error_prone_annotations:2.21.1'
    n6: 'com.google.j2objc:j2objc-annotations:2.8'
    n0.style.fill: "#cfe8ff"
    
    n0 -> n1
    n0 -> n2
    n0 -> n3
    n0 -> n4
    n0 -> n5
    n0 -> n6
