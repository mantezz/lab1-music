"""Классы предметной области музыкального онлайн-сервиса"""

from dataclasses import dataclass

@dataclass
class Artist:
    id: int
    name: str
    country: str

@dataclass
class Genre:
    id: int
    name: str

@dataclass
class Album:
    id: int
    title: str
    artist_id: int
    year: int

@dataclass
class Track:
    id: int
    title: str
    album_id: int
    genre_id: int
    duration: int

@dataclass
class User:
    id: int
    name: str
    email: str

@dataclass
class Playlist:
    id: int
    title: str
    user_id: int

@dataclass
class PlaylistItem:
    id: int
    playlist_id: int
    track_id: int
    position: int

@dataclass
class Plan:
    id: int
    name: str
    price: int

@dataclass
class Subscription:
    id: int
    user_id: int
    plan_id: int
    end_date: str  #Дата в формате YYYY-MM-DD

@dataclass
class Favorite:
    id: int
    user_id: int
    track_id: int

@dataclass
class Listening:
    id: int
    user_id: int
    track_id: int
    listened_at: str  #Дата и время в формате YYYY-MM-DDTHH:MM:SS

Record = (Artist | Genre | Album | Track | User | Playlist | PlaylistItem | Plan | Subscription | Favorite | Listening)

#Порядок используется в меню и при записи файлов
MODELS = {
    "artists": Artist,
    "genres": Genre,
    "albums": Album,
    "tracks": Track,
    "users": User,
    "playlists": Playlist,
    "playlist_items": PlaylistItem,
    "plans": Plan,
    "subscriptions": Subscription,
    "favorites": Favorite,
    "listenings": Listening,
}
