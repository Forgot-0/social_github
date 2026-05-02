import shutil
from pathlib import Path

def clean_pycache(directory: str):
    # Превращаем строку в объект пути
    root = Path(directory).resolve()
    
    if not root.exists():
        print(f"Ошибка: Директория '{root}' не найдена.")
        return

    print(f"Начинаю поиск __pycache__ в: {root}")
    
    # rglob ищет рекурсивно во всех подпапках
    count = 0
    for pycache_folder in root.rglob("__pycache__"):
        if pycache_folder.is_dir():
            try:
                # rmtree удаляет папку вместе со всем содержимым (.pyc файлы)
                shutil.rmtree(pycache_folder)
                print(f"✅ Удалено: {pycache_folder.relative_to(root)}")
                count += 1
            except Exception as e:
                print(f"❌ Не удалось удалить {pycache_folder}: {e}")

    print(f"\nГотово! Всего удалено папок: {count}")

if __name__ == "__main__":
    # Укажите здесь путь к вашему проекту
    # '.' означает текущую папку, где лежит скрипт
    target_path = input("Введите путь к директории (или оставьте пустым для '.'): ").strip() or "."
    clean_pycache(target_path)