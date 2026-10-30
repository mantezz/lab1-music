"""Хранение данных музыкального сервиса в JSON и XML"""

import json
import xml.etree.ElementTree as ET
from dataclasses import fields
from pathlib import Path

from exceptions import StorageError
from models import MODELS

Data = dict[str, list[dict]]

class JsonStorage:
    """Читает и записывает JSON. Проверка объектов выполняется сервисом"""

    def save(self, data: Data, path: str) -> None:
        try:
            text = json.dumps(data, ensure_ascii=False, indent=4)
            Path(path).write_text(text, encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise StorageError(f"Не удалось записать JSON: {error}") from error

    def load(self, path: str) -> Data:
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise StorageError(f"Ошибка чтения JSON: {error}") from error
        if not isinstance(raw, dict):
            raise StorageError("Корень JSON должен быть объектом.")
        return raw


class XmlStorage:
    """Читает и записывает XML с корневым элементом music_service"""

    def save(self, data: Data, path: str) -> None:
        root = ET.Element("music_service")
        for kind, rows in data.items():
            collection = ET.SubElement(root, kind)
            for values in rows:
                record = ET.SubElement(collection, "item")
                for name, value in values.items():
                    ET.SubElement(record, name).text = str(value)
        ET.indent(root, space="    ")
        try:
            ET.ElementTree(root).write(
                path, encoding="utf-8", xml_declaration=True
            )
        except (OSError, UnicodeError) as error:
            raise StorageError(f"Не удалось записать XML: {error}") from error

    def load(self, path: str) -> Data:
        try:
            root = ET.parse(path).getroot()
            return self._read_root(root)
        except (OSError, ValueError, ET.ParseError) as error:
            raise StorageError(f"Не удалось прочитать XML: {error}") from error

    @staticmethod
    def _read_root(root: ET.Element) -> Data:
        names = [node.tag for node in root]
        if (root.tag != "music_service" or len(names) != len(MODELS)
                or set(names) != set(MODELS)):
            raise StorageError("Неверная структура XML.")
        raw = {}
        for collection in root:
            kind = collection.tag
            types = {f.name: f.type for f in fields(MODELS[kind])}
            raw[kind] = []
            for record in collection:
                tags = [node.tag for node in record]
                if (record.tag != "item" or set(tags) != set(types)
                        or len(tags) != len(types)
                        or any(len(node) for node in record)):
                    raise StorageError(f"Неверные поля XML в {kind}.")
                values = {
                    node.tag: types[node.tag](node.text or "")
                    for node in record
                }
                raw[kind].append(values)
        return raw
