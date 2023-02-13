#!/usr/bin/env python

# author: Zhemanov Alexsandr (i.svoboda.vios@gamil.com)
# OS: linux arch64
# editor: neovim(utf-8 default file format)

# 1. Каждое из слов «разработка», «сокет», «декоратор» представить в строковом
#   формате и проверить тип и содержание соответствующих переменных.
#   Затем с помощью онлайн-конвертера преобразовать строковые представление
#   в формат Unicode и также проверить тип и содержимое переменных.
# manual converted
def task_1():
    words = ["разработка", "сокет", "декоратор"]
    words_unic = [
     "\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430",
     "\u0441\u043e\u043a\u0435\u0442",
     "\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440"
 ]

    print(f"{'Task_1':_^79}")
    for word, word_u in zip(words, words_unic):
        assert(type(word) is str)
        assert(type(word_u) is str)
        assert(word == word_u)
        print(f"{word:10} == {word_u:10}")

# -------------------------------------------------------------------------------
# 2. Каждое из слов «class», «function», «method» записать в байтовом типе без
#   преобразования в последовательность кодов
#   (не используя методы encode и decode) и определить тип, содержимое и длину
#   соответствующих переменных.
def task_2():
    print(f"{'Task_2':_^79}")
    words = ["class", "function", "method"]
    words_b = [b"class", b"function", b"method"]

    for word in words_b:
        print(word, "\t",f"{type(word)} len:{len(word)}" )

    print()

    for word in words:
        print(f"{word:10}\t {type(word)} len:{len(word)}" )

# -------------------------------------------------------------------------------
# 3. Определить, какие из слов «attribute», «класс», «функция», «type»
#   невозможно записать в байтовом типе.
def task_3():
    ERROR = "SyntaxError: bytes can only contain ASCII literal characters."
    print(f"{'Task_3':_^79}")

    print(b"attribute", "\tOK")
    print("b'класс'", f"\t{ERROR}")
    print("b'функция'", f"\t{ERROR}")
    print(b"type","\tOK")


# -------------------------------------------------------------------------------
# 4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из
#   строкового представления в байтовое и выполнить обратное преобразование (используя
#   методы encode и decode).

def task_4():
    print(f"{'Task_4':_^79}")
    words = ["разработка", "администрирование", "protocol", "standard"]
    words_enc = []
    words_dec = []

    for word in words:
        word_encode = word.encode("utf-8")
        word_decode = word_encode.decode("utf-8")
        words_enc.append(word_encode)
        words_dec.append(word_decode)
        print(f"{word} --> {word_encode} --> {word_decode}\n")

# -------------------------------------------------------------------------------
# 5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из
#   байтовового в строковый тип на кириллице.

def task_5():
    # у меня система на англиском -> ping eng output
    print(f"{'Task_5':_^79}")
    import subprocess
    import platform

    CMD_COMMAND = "ping"
    CMD_ARGS = "-c 10"
    URLS = ["yandex.ru", "youtube.com"]


    for url in URLS:
        cmd = [CMD_COMMAND]
        if platform.system() == "Linux":
            cmd.append(CMD_ARGS)
        cmd.append(url)
        res = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        # decode to cyrillic
        if res.stdout:
            for line in res.stdout:
                decode_line = line.decode("cp866")
                print(f"{url:12} | {decode_line}", end="")

# -------------------------------------------------------------------------------
# 6. Создать текстовый файл test_file.txt, заполнить его тремя строками:
#   «сетевоепрограммирование», «сокет», «декоратор».
#   Проверить кодировку файла по умолчанию.
#   Принудительно открыть файл в формате Unicode и вывести его содержимое.
def task_6():
    # os: linux
    # filetype default: utf-8
    print(f"{'Task_6':_^79}")
    with open("./test_file.txt") as file_h:
        print(f"Default encode: {file_h.encoding}")
        line = file_h.readline()
        print(line)

    with open("./test_file.txt", "r", encoding="utf-8") as file_h:
        print(file_h.encoding)
        line = file_h.readline()
        print(line, end="")

# -------------------------------------------------------------------------------
if __name__ == "__main__":
    task_1()
    # --
    task_2()
    # -- 
    task_3()
    # --
    task_4()
    # --
    task_5()
    # --
    task_6()
    print(f"{'':_^79}")
