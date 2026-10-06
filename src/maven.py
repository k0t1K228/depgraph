"""Получение прямых зависимостей Maven-пакета из репозитория."""

import re
import urllib.error
import urllib.request
from dataclasses import replace

from src.pom import Coordinates, MavenError, parse_pom

TIMEOUT_SECONDS = 15
HTTP_NOT_FOUND = 404
MAX_PARENT_DEPTH = 10
MAX_SUBSTITUTIONS = 10
PLACEHOLDER = re.compile(r"\$\{([^}]+)\}")

def make_coordinates(package_name, version):
    """Создать координаты из имени «группа:артефакт» и версии."""
    group, artifact = package_name.split(":")
    return Coordinates(group, artifact, version)

def pom_url(repository, coords):
    """Построить URL файла pom.xml в репозитории Maven."""
    group_path = coords.group.replace(".", "/")
    name = f"{coords.artifact}-{coords.version}.pom"
    parts = [repository.rstrip("/"), group_path, coords.artifact,
             coords.version, name]
    return "/".join(parts)

def fetch_bytes(url):
    """Скачать файл по URL и вернуть его содержимое."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as reply:
            return reply.read()
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise MavenError(f"файл не найден в репозитории: {url}") from error
        raise MavenError(f"ошибка HTTP {error.code}: {url}") from error
    except OSError as error:
        raise MavenError(f"не удалось подключиться к {url}: {error}") from error

def load_chain(repository, coords):
    """Загрузить pom.xml пакета и всех его родителей (от потомка к предку)."""
    chain = []
    current = coords
    while current is not None:
        if len(chain) >= MAX_PARENT_DEPTH:
            raise MavenError("слишком длинная цепочка родительских pom")
        pom = parse_pom(fetch_bytes(pom_url(repository, current)))
        chain.append(pom)
        current = pom.parent
    return chain

def merge_properties(chain):
    """Собрать свойства всей цепочки: значения потомка важнее родителя."""
    merged = {}
    for pom in reversed(chain):
        merged.update(pom.properties)
    own = chain[0].coordinates
    merged["project.version"] = own.version
    merged["project.groupId"] = own.group
    merged["project.artifactId"] = own.artifact
    return merged

def merge_managed(chain):
    """Собрать dependencyManagement всей цепочки."""
    merged = {}
    for pom in reversed(chain):
        merged.update(pom.managed)
    return merged

def collect_dependencies(chain):
    """Собрать зависимости цепочки: унаследованные и собственные."""
    collected = {}
    for pom in reversed(chain):
        for dependency in pom.dependencies:
            collected[(dependency.group, dependency.artifact)] = dependency
    return list(collected.values())

def substitute(text, properties):
    """Подставить значения свойств вместо ${имя}, в том числе вложенных."""

    def replace_one(match):
        return properties.get(match.group(1), match.group(0))

    for _ in range(MAX_SUBSTITUTIONS):
        replaced = PLACEHOLDER.sub(replace_one, text)
        if replaced == text:
            break
        text = replaced
    return text

def resolve_dependency(dependency, properties, managed):
    """Подставить свойства и версию из dependencyManagement."""
    group = substitute(dependency.group, properties)
    artifact = substitute(dependency.artifact, properties)
    version = dependency.version or managed.get((group, artifact), "")
    return replace(
        dependency,
        group=group,
        artifact=artifact,
        version=substitute(version, properties),
    )

def get_direct_dependencies(repository, coords):
    """Получить прямые зависимости пакета по URL репозитория."""
    chain = load_chain(repository, coords)
    properties = merge_properties(chain)
    managed = merge_managed(chain)
    return [
        resolve_dependency(dependency, properties, managed)
        for dependency in collect_dependencies(chain)
    ]
