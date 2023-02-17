"""
3. Задание на закрепление знаний по модулю yaml.
    Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата.
    Для этого:
        Подготовить данные для записи в виде словаря,
        в котором первому ключу соответствует список,
        второму — целое число,
        третьему — вложенный словарь,
            где значение каждого ключа — это целое число с юникод-символом,
        отсутствующим в кодировке ASCII (например, €);
    
    Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml.
    При этом обеспечить стилизацию файла с помощью параметра default_flow_style,
    а также установить возможность работы с юникодом: allow_unicode = True;
    
    Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.
"""

import yaml

JSON_ = {
    "sensor": ["T1", "T2", "T3"],
    "average_temperature_celsius": 58,
    "report": {
        "15.09.22": "33℃",
        "12.09.22": "63℃",
        "06.10.22": "11℃",
        "15.10.22": "124℃",
        "04.11.22": "70℃",
        "12.11.22": "6℃",
        "06.12.22": "83℃",
        "13.12.22": "50℃",
        "22.01.23": "72℃",
        "23.01.23": "108℃",
        "01.02.23": "72℃",
        "07.02.23": "6℃",
        "error": "12℉",
    }
}

FILE_PATH = "./res/my_result.yaml"


def serization_dict_to_yaml(file_path: str,
                            data: dict = JSON_,
                            default_flow_style=False,
                            allow_unicode=False):
    """
    serization python dictionary to file

    param file_path - path to serization
    param data - python dictionary
    param default_flow_style - serization list as block
    param allow_unicode - support unicode charset
    """

    with open(file_path, "w", encoding="utf-8") as f_h:
        yaml.dump(data,
                  f_h,
                  default_flow_style=default_flow_style,
                  allow_unicode=allow_unicode,
                  sort_keys=False)


# serization
serization_dict_to_yaml(FILE_PATH,
                        default_flow_style=False,
                        allow_unicode=True)
# test
with open(FILE_PATH, "r", encoding="utf-8") as f_read:
    res = yaml.safe_load(f_read)
    assert (JSON_ == res)
