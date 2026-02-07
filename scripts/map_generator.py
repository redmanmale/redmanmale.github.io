import os
import sys
import tempfile
import shutil
import msvcrt

marker = "style=\"fill:#fff;fill-rule:nonzero;stroke:#202020;stroke-width: 10px\""
target_marker = "style=\"fill:#f00;fill-rule:nonzero;stroke:#202020;stroke-width: 10px\""

def generate_file(file_in, file_out):
    cmd = "inkscape.com " + file_in + " --export-width=1000 --export-type=PNG --export-area-drawing --export-filename=" + file_out
    os.system(cmd)

def process_file(target_file, output_dir):
    if not os.path.isfile(target_file):
        print(f"Ошибка: файл '{target_file}' не существует")
        return

    if not os.path.isdir(output_dir):
        print(f"Ошибка: директория '{output_dir}' не существует")
        return

    line_numbers = []
    try:
        with open(target_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for i, line in enumerate(lines, 1):  # начинаем с 1 для удобства чтения
            if marker in line:
                line_numbers.append(i)

        print(f"Найдено {len(line_numbers)} вхождений")

        if not line_numbers:
            print("Маркеры не найдены")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            counter = 1
            for line_num in line_numbers:
                base_name = os.path.basename(target_file)
                name, ext = os.path.splitext(base_name)
                temp_filename = f"{name}_modified_{line_num}{ext}"
                temp_filepath = os.path.join(temp_dir, temp_filename)

                try:
                    shutil.copy2(target_file, temp_filepath)

                    with open(temp_filepath, 'r', encoding='utf-8') as file:
                        temp_lines = file.readlines()

                    if 0 < line_num <= len(temp_lines):
                        temp_lines[line_num-1] = temp_lines[line_num-1].replace(marker, target_marker, 1)
                    else:
                        print(f"Предупреждение: строка {line_num} выходит за пределы файла")
                        continue

                    with open(temp_filepath, 'w', encoding='utf-8') as file:
                        file.writelines(temp_lines)

                    output_path = os.path.join(output_dir, f'{counter:02d}.png')
                    generate_file(temp_filepath, output_path)

                    size = len(line_numbers)
                    percent = round(counter * 100 / size)
                    print(f"готово {counter}/{size} = {percent}%")
                    counter += 1

                except Exception as e:
                    print(f"Ошибка при обработке строки {line_num}: {e}")
                    break
            print("Обработка завершена. Временные файлы автоматически удалены.")
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")

def process_file2(target_file, output_dir, line_numbers):
    temp_dir = tempfile.mkdtemp()
    try:
        file_name = os.path.basename(target_file)
        temp_filepath = os.path.join(temp_dir, file_name)

        shutil.copy2(target_file, temp_filepath)

        with open(temp_filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        line_numbers = [int(num.strip()) for num in line_numbers.split(',')]

        i = 0
        occurrence_count = 0
        for s in lines:
            i += 1
            if s.find(marker) != -1:
                occurrence_count += 1
                if occurrence_count in line_numbers:
                    lines[i-1] = s.replace(marker, target_marker, 1)

        with open(temp_filepath, 'w', encoding='utf-8') as file:
            file.writelines(lines)

        output_path = os.path.join(output_dir, 'map.png')
        generate_file(temp_filepath, output_path)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def get_numbers_from_file(file_path):
    matching_lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                if line.startswith('+'):
                    matching_lines.append(line_number)
    except FileNotFoundError:
        return ''
    except Exception as e:
        print(f"Произошла ошибка при чтении файла: {e}")
    return ','.join(str(i) for i in matching_lines)

def main():
    """генератор карты из svg в png, имеет 3 режима
    1. путь к svg, путь к папке - генерит картинки для всех регионов по одному закрашенному, имя файла = номер в svg
    2. путь к svg, путь к папке, список чисел - генерит одну картинку со всеми указанными регионами
    3. путь к svg, путь к папке, путь к txt файлу со списком посещённых регионов (помечены +) - генерит одну картинку со всеми указанными в файле регионами
    """
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print("Использование: python script.py <путь_к_файлу> <путь_к_папке> [список регионов через запятую]")
        print("Пример: python script.py input.svg output/ 1,4,66")
        sys.exit(1)

    target_file = sys.argv[1]
    output_dir = sys.argv[2]

    if len(sys.argv) == 3:
        process_file(target_file, output_dir)
        sys.exit(0)

    tmp = sys.argv[3]
    line_numbers = get_numbers_from_file(tmp)

    if not line_numbers:
        line_numbers = tmp

    process_file2(target_file, output_dir, line_numbers)

if __name__ == "__main__":
    main()
