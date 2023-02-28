#!/usr/bin/env python3

""" My Matrix class """

# from __future__ import annotations

# Todo: fix empty matrix size


import re


class Matrix:
    """ Matrix """
    __data: dict

    def ___(self):
        return self.__data

    def __init__(self, *elems, rows=1) -> None:

        # test split elems
        if rows <= 0 or len(elems) % rows != 0:
            raise ValueError("Can't split len(elems) / rows")

        self.__data = {}

        columns = len(elems) // rows

        if len(elems) > 0:
            self.__data["size"] = (columns, rows)

        row = 0
        column = 0
        for num in elems:
            self.__data[(column, row)] = num
            column +=1
            if column >= columns:
                column = 0
                row += 1
                # ToDo:  add if row > rows 

    def get_size(self) -> tuple:
        """ return size of matrix (columns, rows) """
        return self.__data.get("size", (0, 0))

    def get_elem(self, column_index, row_index):
        """ return elems of pos(column, row) """
       
        value = self.__data.get((column_index, row_index))

        if value is None:
            raise ValueError(f"Unknow index {(column_index, row_index)}")
        
        return value

    def __arifm_func(self, func, other: 'Matrix') -> list:

        (columns, rows) = self.get_size()

        return [func(self.get_elem(x, y),  other.get_elem(x, y))
                for x in range(columns) for y in range(rows)]

    def __add__(self, other: 'Matrix') -> 'Matrix':
        
        if self.is_empty() or other.is_empty():
            return Matrix()
        
        """ operator + for matrix. return a new matrix """
        if self.get_size() != other.get_size():
            raise ValueError("Matrix's sizies must be eq")

        return Matrix(*self.__arifm_func(lambda x, y: x + y, other), rows=self.get_size()[1])

    def __sub__(self, other: "Matrix") -> 'Matrix':
        """ operator - for matrix. return a new matrix """
        
        if self.is_empty() or other.is_empty():
            return Matrix()

        if self.get_size() != other.get_size():
            raise ValueError("Matrix's sizies must be eq")

        return Matrix(*self.__arifm_func(lambda x, y: x - y, other), rows=self.get_size()[1])

    def __eq__(self, other: "Matrix") -> bool:
        if self.get_size() != other.get_size():
            raise ValueError("Matrix's sizies must be eq")
        
        (columns, rows) = self.get_size()

        for y in range(rows):
            for x in range(columns):
                if self.get_elem(x,y) != other.get_elem(x,y):
                    return False

        return True

        
    def is_empty(self):

        (columns, rows) = self.get_size()

        return columns * rows == 0

    

    def __str__(self) -> str:


        if self.is_empty():
            return "Empty Matrix"
        
        (columns, rows) = self.get_size()

        output = ""
        for j, row in enumerate(range(rows)):

            for i, column in enumerate(range(columns)):
                output += f"{self.get_elem(column, row)}"

                if i != columns - 1:
                    output += " "

            if j != rows - 1:
                output += "\n"

        return output
