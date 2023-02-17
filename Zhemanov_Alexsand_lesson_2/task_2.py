"""
    2. Задание на закрепление знаний по модулю json. 
    Есть файл orders в формате JSON с информацией о заказах.
    Написать скрипт, автоматизирующий его заполнение данными.
    Для этого:
        - Создать функцию write_order_to_json(),
        в которую передается 5 параметров — 
            товар (item),
            количество (quantity),
            цена (price),
            покупатель (buyer),
            дата (date).
        Функция должна предусматривать запись данных 
            в виде словаря в файл orders.json. 
        При записи данных указать величину отступа в 4 пробельных символа;
    - Проверить работу программы через вызов функции write_order_to_json() 
        с передачей в нее значений каждого параметра. 
"""
from datetime import date

# in poduct price must be decimal
import json

from chardet.universaldetector import UniversalDetector


def write_order_to_json(item: str, quantity: int, price: float, buyer: str,
                        date: date):
    """
    add order to ./res/orders.json
    """

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

    JSON_FILE = "./res/orders.json"
    # --
    write_order_to_json("книга_1", 3, 120.50, "some_buyer", date.today())
    write_order_to_json("Все лето в один день", 7, 400.00, "some_buyer",
                        date.today())
    write_order_to_json("книга_3", 4, 300.75, "some_buyer", date.today())
    write_order_to_json("451 ℉", 1, 550.45, "some_buyer", date.today())
    # --

    print(f"{f'Inside {JSON_FILE}':-^79}")
    with open(JSON_FILE, "rb") as f_h:
        bytes_ = f_h.read()
        enc = chardet.detect(bytes_).get("encoding") or "utf-8"
        text = bytes_.decode(enc)
        for line in text:
            print(line, end="")
        print()
    print(f"{'':-^79}")
