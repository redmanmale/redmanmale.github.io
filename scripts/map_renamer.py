import os
import sys

def build_dict_from_txt(txt_path):
    """
    Читает txt файл и возвращает словарь:
    ключ - номер строки с ведущим нулём (01, 02, ...),
    значение - содержимое строки.
    """
    mapping = {}
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for idx, line in enumerate(lines, start=1):
        key = f"{idx:02}"  # ведущий ноль для 1-значных чисел
        value = line.strip()
        mapping[key] = value
    return mapping

def rename_files_in_folder(folder_path, mapping):
    """
    Переименовывает файлы в указанной папке согласно словарю.
    """
    for filename in os.listdir(folder_path):
        old_path = os.path.join(folder_path, filename)
        if os.path.isfile(old_path):
            name, ext = os.path.splitext(filename)
            if name in mapping:
                new_name = mapping[name] + ext
                new_path = os.path.join(folder_path, new_name)
                os.rename(old_path, new_path)
                print(f"Переименовано: {filename} -> {new_name}")

def main():
    """ переименовывает файлы в папке: имя файла без расширения = номер,
    который ищется в txt и берёт оттуда строку с этим номером для нового имени файла"""
    if len(sys.argv) != 3:
        print("Использование: python script.py <путь_к_папке> <путь_к_txt>")
        sys.exit(1)

    folder_path = sys.argv[1]
    txt_path = sys.argv[2]

    if not os.path.isdir(folder_path):
        print(f"Ошибка: {folder_path} — папка не найдена")
        sys.exit(1)
    if not os.path.isfile(txt_path):
        print(f"Ошибка: {txt_path} — файл не найден")
        sys.exit(1)

    mapping = build_dict_from_txt(txt_path)
    rename_files_in_folder(folder_path, mapping)

if __name__ == "__main__":
    main()
