"""Консольный музыкальный онлайн-сервис. Запуск: python main.py"""

from dataclasses import asdict, fields
from pathlib import Path

from exceptions import ServiceError
from models import MODELS
from service import MusicService
from storage import JsonStorage, XmlStorage

DATA_DIR = Path(__file__).resolve().parent / "data"
JSON_FILE = str(DATA_DIR / "data.json")
XML_FILE = str(DATA_DIR / "data.xml")

LABELS = {
    "artists": "Исполнители", "genres": "Жанры", "albums": "Альбомы",
    "tracks": "Треки", "users": "Пользователи", "playlists": "Плейлисты",
    "playlist_items": "Состав плейлистов", "plans": "Тарифы",
    "subscriptions": "Подписки", "favorites": "Избранное",
    "listenings": "История прослушиваний",
}

PROMPTS = {
    "name": "Имя / название", "country": "Страна", "title": "Название",
    "artist_id": "ID исполнителя", "year": "Год",
    "album_id": "ID альбома", "genre_id": "ID жанра",
    "duration": "Длительность в секундах", "email": "Email",
    "user_id": "ID пользователя", "playlist_id": "ID плейлиста",
    "track_id": "ID трека", "position": "Позиция в плейлисте",
    "price": "Цена за месяц в рублях", "plan_id": "ID тарифа",
    "end_date": "Дата окончания YYYY-MM-DD",
    "listened_at": "Дата и время YYYY-MM-DDTHH:MM:SS",
}

class ConsoleApp:
    """Консольное меню для всех классов предметной области"""

    def __init__(self, system: MusicService) -> None:
        self.system = system

    def choose_kind(self) -> str:
        kinds = list(MODELS)
        for number, kind in enumerate(kinds, 1):
            print(f"{number}. {LABELS[kind]}")
        number = int(input("Тип данных: "))
        if not 1 <= number <= len(kinds):
            raise ServiceError("Такого пункта нет.")
        return kinds[number - 1]

    @staticmethod
    def read_values(kind: str, editing: bool = False) -> dict:
        values = {}
        for field in fields(MODELS[kind]):
            if field.name == "id":
                continue
            hint = " [Enter - оставить]" if editing else ""
            text = input(f"{PROMPTS[field.name]}{hint}: ").strip()
            if editing and not text:
                continue
            values[field.name] = field.type(text)
        return values

    def crud(self, action: str) -> None:
        kind = self.choose_kind()
        if action == "1":
            rows = self.system.list_records(kind)
            if not rows:
                print("Записей нет.")
            for item in rows:
                print(asdict(item))
        elif action == "2":
            record_id = int(input("ID записи: "))
            print(asdict(self.system.get(kind, record_id)))
        elif action == "3":
            item = self.system.create(kind, self.read_values(kind))
            print(f"Создана запись с ID {item.id}.")
        elif action == "4":
            record_id = int(input("ID записи: "))
            print(asdict(self.system.get(kind, record_id)))
            values = self.read_values(kind, editing=True)
            self.system.update(kind, record_id, values)
            print("Запись изменена.")
        else:
            record_id = int(input("ID записи: "))
            self.system.delete(kind, record_id)
            print("Запись удалена.")

    def run(self) -> None:
        while True:
            try:
                print("\n===== Музыкальный онлайн-сервис. Вариант 5 =====")
                print("1. Показать все")
                print("2. Показать один")
                print("3. Добавить")
                print("4. Изменить")
                print("5. Удалить")
                print("6. Сохранить в JSON")
                print("7. Загрузить из JSON")
                print("8. Сохранить в XML")
                print("9. Загрузить из XML")
                print("0. Выход")
                action = input("Выберите пункт: ").strip()
                if action == "0":
                    print("Работа завершена. "
                          "Данные сохраняются пунктами 6 и 8.")
                    return
                if action in {"1", "2", "3", "4", "5"}:
                    self.crud(action)
                elif action in {"6", "7", "8", "9"}:
                    if action in {"6", "7"}:
                        storage = JsonStorage()
                        path = JSON_FILE
                    else:
                        storage = XmlStorage()
                        path = XML_FILE
                    if action in {"6", "8"}:
                        storage.save(self.system.to_data(), path)
                        print(f"Сохранено в {path}")
                    else:
                        self.system.load_data(storage.load(path))
                        print(f"Загружено из {path}")
                else:
                    print("Такого пункта нет.")
            except ServiceError as error:
                print(f"Ошибка сервиса: {error}")
            except ValueError as error:
                print(f"Ошибка формата данных: {error}")
            except (EOFError, KeyboardInterrupt):
                print("\nРабота завершена.")
                return


def main() -> None:
    """Загружает начальные данные и запускает меню"""
    system = MusicService()
    try:
        system.load_data(JsonStorage().load(JSON_FILE))
        print("Загружены данные из data/data.json")
    except (ServiceError, ValueError) as error:
        print(f"Данные не загружены ({error}), начинаем с пустой базы.")
    ConsoleApp(system).run()


if __name__ == "__main__":
    main()
