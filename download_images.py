"""
Скрипт для скачивания изображений из JSON и сохранения их локально
"""
import json
import os
import requests
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CARS_FILE = "data/datacars.json"
PHOTOS_DIR = "data/photos"

def ensure_photos_dir():
    """Создает папку для фотографий если её нет"""
    if not os.path.exists(PHOTOS_DIR):
        os.makedirs(PHOTOS_DIR)
        logger.info(f"Создана папка {PHOTOS_DIR}")

def download_image(url, filepath):
    """Скачивает изображение по URL и сохраняет в файл"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        logger.info(f"Скачано: {url} -> {filepath}")
        return True
    except Exception as e:
        logger.error(f"Ошибка скачивания {url}: {e}")
        return False

def get_file_extension(url):
    """Получает расширение файла из URL"""
    parsed = urlparse(url)
    path = parsed.path
    if '.' in path:
        return os.path.splitext(path)[1]
    return '.jpg'  # По умолчанию jpg

def download_all_images():
    """Скачивает все изображения из JSON"""
    ensure_photos_dir()
    
    if not os.path.exists(CARS_FILE):
        logger.error(f"Файл {CARS_FILE} не найден!")
        return
    
    with open(CARS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated = False
    for car in data.get('cars', []):
        car_id = car.get('id')
        if not car_id:
            continue
        
        photos = car.get('photos', [])
        if not photos:
            continue
        
        local_photos = []
        for idx, photo_url in enumerate(photos):
            if isinstance(photo_url, str) and photo_url.startswith('http'):
                # Это URL, нужно скачать
                ext = get_file_extension(photo_url)
                filename = f"car_{car_id}_{idx+1}{ext}"
                filepath = os.path.join(PHOTOS_DIR, filename)
                
                if not os.path.exists(filepath):
                    if download_image(photo_url, filepath):
                        local_photos.append(filename)
                    else:
                        # Если не удалось скачать, оставляем URL
                        local_photos.append(photo_url)
                else:
                    # Файл уже существует
                    local_photos.append(filename)
            else:
                # Уже локальный файл
                local_photos.append(photo_url)
        
        if local_photos != photos:
            car['photos'] = local_photos
            updated = True
    
    if updated:
        with open(CARS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("JSON обновлен с локальными путями к фотографиям")
    else:
        logger.info("Все фотографии уже скачаны или обновление не требуется")

if __name__ == "__main__":
    download_all_images()

