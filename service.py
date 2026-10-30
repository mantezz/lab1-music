"""Хранение объектов, операции CRUD и проверка связей"""

from dataclasses import asdict, fields, replace
from datetime import date, datetime

from exceptions import ServiceError
from models import MODELS, Record

REFERENCES = {
    "artist_id": "artists",
    "album_id": "albums",
    "genre_id": "genres",
    "user_id": "users",
    "playlist_id": "playlists",
    "track_id": "tracks",
    "plan_id": "plans",
}

UNIQUE = {
    "users": ("email",),
    "playlist_items": ("playlist_id", "position"),
    "subscriptions": ("user_id",),
    "favorites": ("user_id", "track_id"),
}

class MusicService:
    """Хранит объекты; все изменения проходят общую проверку."""

    def __init__(self) -> None:
        self._data: dict[str, dict[int, Record]] = {
            kind: {} for kind in MODELS
        }

    def _check_kind(self, kind: str) -> None:
        if kind not in MODELS:
            raise ServiceError("Неизвестный тип данных.")

    def get(self, kind: str, record_id: int) -> Record:
        self._check_kind(kind)
        if record_id not in self._data[kind]:
            raise ServiceError(f"Запись с ID {record_id} не найдена.")
        """Копия не позволяет обойти проверку через изменение объекта снаружи"""
        return replace(self._data[kind][record_id])

    def list_records(self, kind: str) -> list[Record]:
        self._check_kind(kind)
        return [replace(item) for item in self._data[kind].values()]

    def create(self, kind: str, values: dict) -> Record:
        self._check_kind(kind)
        record_id = max(self._data[kind], default=0) + 1
        item = self._make_record(kind, {**values, "id": record_id})
        self._commit(kind, record_id, item)
        return replace(item)

    def update(self, kind: str, record_id: int, values: dict) -> Record:
        old = asdict(self.get(kind, record_id))
        if "id" in values:
            raise ServiceError("ID изменять нельзя.")
        item = self._make_record(kind, {**old, **values})
        self._commit(kind, record_id, item)
        return replace(item)

    def delete(self, kind: str, record_id: int) -> None:
        self.get(kind, record_id)
        self._commit(kind, record_id, None)

    def _commit(self, kind: str, record_id: int,
                item: Record | None) -> None:
        """Сначала проверяем копию. При ошибке исходные данные сохраняются"""
        candidate = {name: rows.copy() for name, rows in self._data.items()}
        if item is None:
            del candidate[kind][record_id]
        else:
            candidate[kind][record_id] = item
        self._validate(candidate)
        self._data = candidate

    @staticmethod
    def _make_record(kind: str, values: dict) -> Record:
        expected = {field.name: field.type for field in fields(MODELS[kind])}
        if not isinstance(values, dict) or set(values) != set(expected):
            raise ServiceError(f"Поля {kind}: {', '.join(expected)}.")
        for name, field_type in expected.items():
            value = values[name]
            if type(value) is not field_type:
                raise ServiceError(f"{name}: нужен тип {field_type.__name__}.")
            if field_type is str and not value.strip():
                raise ServiceError(f"{name}: строка не должна быть пустой.")
            if field_type is int:
                minimum = 0 if name == "price" else 1
                if value < minimum:
                    raise ServiceError(f"{name}: минимум {minimum}.")
        if "year" in values and values["year"] > 9999:
            raise ServiceError("Год должен находиться в диапазоне 1..9999.")
        if "email" in values:
            parts = values["email"].split("@")
            if len(parts) != 2 or not all(parts) or " " in values["email"]:
                raise ServiceError("Email должен иметь вид имя@домен.")
        if "end_date" in values:
            date.fromisoformat(values["end_date"])
        if "listened_at" in values:
            datetime.strptime(values["listened_at"], "%Y-%m-%dT%H:%M:%S")
        return MODELS[kind](**values)

    @staticmethod
    def _validate(data: dict[str, dict[int, Record]]) -> None:
        for kind, rows in data.items():
            seen = set()
            for item in rows.values():
                values = asdict(item)
                for name, target in REFERENCES.items():
                    if name in values and values[name] not in data[target]:
                        raise ServiceError(
                            f"{kind} #{item.id}: нет {target} "
                            f"с ID {values[name]}. Удаление связанной "
                            "записи также запрещено."
                        )
                if kind in UNIQUE:
                    key = tuple(values[name] for name in UNIQUE[kind])
                    if key in seen:
                        raise ServiceError(f"Повтор уникальных полей {kind}.")
                    seen.add(key)

    def to_data(self) -> dict[str, list[dict]]:
        return {
            kind: [asdict(item) for item in rows.values()]
            for kind, rows in self._data.items()
        }

    def load_data(self, raw: dict) -> None:
        if not isinstance(raw, dict) or set(raw) != set(MODELS):
            raise ServiceError("Файл должен содержать все 11 коллекций.")
        candidate: dict[str, dict[int, Record]] = {}
        for kind, rows in raw.items():
            if not isinstance(rows, list):
                raise ServiceError(f"{kind}: нужен список записей.")
            candidate[kind] = {}
            for values in rows:
                item = self._make_record(kind, values)
                if item.id in candidate[kind]:
                    raise ServiceError(f"Повтор ID в {kind}.")
                candidate[kind][item.id] = item
        self._validate(candidate)
        self._data = candidate
