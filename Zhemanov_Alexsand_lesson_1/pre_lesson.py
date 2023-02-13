#!/usr/env python
def fizzbuzz(
    fizz: int = 3,
    buzz: int = 5,
    start: "int|None" = None,
    end: "int|None" = None,
    step: "int|None" = None,
    with_enumerate: bool = False,
):
    """fizzbuzz genirator"""
    # test if begin < end
    if start != None and end != None:
        if start > end:
            raise ValueError("param 'start' must be low than 'end'") 
    begin = start if start != None else 0
    out = ""
    while True:
        if begin % fizz == 0:
            out += "fizz"
        if begin % buzz == 0:
            out += "buzz"
        if with_enumerate:
            yield begin, out
        else:
            yield out
        begin += step if step != None else 1
        out = ""
        if end and end <= begin:
            break

if __name__ == "__main__":
    print(fizzbuzz())
    for i in fizzbuzz(end=10, with_enumerate=True):
        print(i)
