"""
1.  Задание на закрепление знаний по модулю CSV. 
    Написать скрипт, осуществляющий выборку определенных данных 
        из файлов info_1.txt, info_2.txt, info_3.txt 
        и формирующий новый «отчетный» файл в формате CSV. 
    Для этого:
        - Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и считывание данных. В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения каждого параметра поместить в соответствующий список. Должно получиться четыре списка — например, os_prod_list, os_name_list, os_code_list, os_type_list. В этой же функции создать главный список для хранения данных отчета — например, result — и поместить в него названия столбцов отчета в виде списка: «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла);
        - Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. В этой функции реализовать получение данных через вызов функции get_data(), а также сохранение подготовленных данных в соответствующий CSV-файл;
Проверить работу программы через вызов функции write_to_csv(). 

2. Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с информацией о заказах. Написать скрипт, автоматизирующий его заполнение данными. Для этого:
 - Создать функцию write_order_to_json(), в которую передается 5 параметров — товар (item), количество (quantity), цена (price), покупатель (buyer), дата (date). Функция должна предусматривать запись данных в виде словаря в файл orders.json. При записи данных указать величину отступа в 4 пробельных символа;
 - Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого параметра. 

3. Задание на закрепление знаний по модулю yaml. Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата. Для этого:
Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список, второму — целое число, третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом, отсутствующим в кодировке ASCII (например, €);
Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml. При этом обеспечить стилизацию файла с помощью параметра default_flow_style, а также установить возможность работы с юникодом: allow_unicode = True;
Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.
"""
import os
from datetime import date


def get_data() -> list[list[str]]:
    """
    get data from ./res/info_(1..3).txt and convert to table:
    
    [
    [hander_name1, hander_name2],
    [value_11, value_12],
    ...
    [value_{n}1, value_{n}2],
    ]

    Returns:
    list[list[str]]: like csv list type 
    """
    import collections
    import re

    import chardet

    FILE_LIST = [
        "./res/info_1.txt",
        "./res/info_2.txt",
        "./res/info_3.txt",
    ]

    REG = {
        "dev_by":
        re.compile(r"^Изготовитель\s+системы\:[ \r\v\t\f]+([^\n\r]+)",
                   re.MULTILINE),
        "os_name":
        re.compile(r"^Название\s+ОС\:[ \r\v\t\f]+([\w ]+)", re.MULTILINE),
        "os_code":
        re.compile(r"^Код\s+продукта\:[ \r\v\t\f]+([^\n\r]+)", re.MULTILINE),
        "cpu_arch":
        re.compile(r"^Тип\s+системы\:[ \r\v\t\f]+([^\n\r]+)", re.MULTILINE),
    }

    data = collections.OrderedDict()
    result = set()
    for pth in FILE_LIST:
        with open(pth, "rb") as hander:
            full_bytes = hander.read()
            encoding = chardet.detect(full_bytes)
            encoding = encoding.get("encoding") or "ascii"
            full_text = full_bytes.decode(encoding)

            for key, val in REG.items():
                re_res = val.findall(full_text)
                if re_res and len(re_res) > 0:
                    re_res = re_res[0]
                else:
                    re_res = None
                if key in data:
                    data[key].append(re_res)
                else:
                    data[key] = [re_res]
    result = [
        "Изготовитель системы", "Название ОС", "Код продукта", "Тип системы"
    ]

    # rotate data and conver tuple to list
    # x11 x12 x13    # x11 x21 x31
    # x21 x22 x23 -> # x12 x22 x32
    # x31 x32 x33    # x13 x23 x33
    rot_data = list(map(list, zip(*data.values())))
    result = [result, *rot_data]

    return result


def write_to_csv(pth: "str"):
    """
    store "get_data()" to csv file
    
    Parameters:
    pth(str) - path to save csv file
    """
    import csv
    data = get_data()
    with open(pth, "w", encoding="utf-8") as f_h:
        writer = csv.writer(
            f_h,
            quoting=csv.QUOTE_NONNUMERIC  # для экранирования "," в значениях
        )
        writer.writerows(data)


# in poduct price must be decimal
def write_order_to_json(item: str, quantity: int, price: float, buyer: str,
                        date: date):
    """
    """
    import json

    from chardet.universaldetector import UniversalDetector

    FILE_PATH = "./res/orders.json"
    new_order = {
        "item": item.encode("utf-8").decode("utf-8"),
        "quantity": quantity,
        "price": price,
        "buyer": buyer,
        "date": date.__str__()
    }

    # get json encoding
    detector = UniversalDetector()
    encoding = "utf-8"
    with open(FILE_PATH, "rb") as file_h:
        for line_b in file_h:
            detector.feed(line_b)
            if detector.done:
                encoding = detector.result["encoding"]
                break

    with open(FILE_PATH, "r+", encoding=encoding) as file_h:
        cur_data = json.load(file_h)
        orders = cur_data.get("orders", [])
        orders.append(new_order)
        file_h.seek(0)
        json.dump(cur_data, file_h, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    import chardet

    CSV_FILE = "out_csv.csv"
    JSON_FILE = "./res/orders.json"
    # --
    write_to_csv(CSV_FILE)
    print(f"{f'Inside {CSV_FILE}':-^79}")
    with open(CSV_FILE, "rb") as f_h:
        bytes_ = f_h.read()
        enc = chardet.detect(bytes_).get("encoding") or "ascii"
        text = bytes_.decode(enc)
        for line in text:
            print(line, end="")
    print(f"{'':-^79}")
    # --
    write_order_to_json("книга", 3, 12.50, "some_buyer", date.today())

    print(f"{f'Inside {JSON_FILE}':-^79}")
    with open(JSON_FILE, "rb") as f_h:
        bytes_ = f_h.read()
        enc = chardet.detect(bytes_).get("encoding") or "utf-8"
        text = bytes_.decode(enc)
        for line in text:
            print(line, end="")
        print()
    print(f"{'':-^79}")
