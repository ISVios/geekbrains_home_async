"""
Unit test

"""
import random
import unittest
import task_10_1 as task 


class MatrixTest(unittest.TestCase):


    def test__all(self):
        print("\nTest maxtrix")
        TEST_VAR_0 = task.Matrix()
        TEST_VAR_1 = task.Matrix(1)
        TEST_VAR_2 = task.Matrix(1,2)

        
        # empty
        print("\tEmpty matrix\t", end="")

        self.assertEqual(TEST_VAR_0.is_empty(), True)
        print(" empty", end="")

        self.assertEqual(TEST_VAR_0.get_size(), (0,0)) # test__get_size
        print(" size", end="")
        
        self.assertEqual(TEST_VAR_0.__str__(), "Empty Matrix")
        print(" str", end="")
        
        self.assertEqual(TEST_VAR_0 + TEST_VAR_0, TEST_VAR_0)
        self.assertEqual(TEST_VAR_0 - TEST_VAR_0, TEST_VAR_0)
        self.assertEqual(TEST_VAR_1 + TEST_VAR_0, TEST_VAR_0)
        self.assertEqual(TEST_VAR_0 - TEST_VAR_1, TEST_VAR_0)
        self.assertEqual(TEST_VAR_2 + TEST_VAR_0, TEST_VAR_0)
        self.assertEqual(TEST_VAR_0 - TEST_VAR_2, TEST_VAR_0)
        print(" + - = ")

        # one elem 
        RND_ELM_1 = random.randint(0, 999)
        RND_ELM_2 = random.randint(0, 999)
        TEST_VAR_ELM_1 = task.Matrix(RND_ELM_1)
        TEST_VAR_ELM_2 = task.Matrix(RND_ELM_2)
        TEST_VAR_ELM_ADD = task.Matrix(RND_ELM_1 + RND_ELM_2)
        TEST_VAR_ELM_SUB12 = task.Matrix(RND_ELM_1 - RND_ELM_2)
        TEST_VAR_ELM_SUB21 = task.Matrix(RND_ELM_2 - RND_ELM_1)
        print("\tOneElem matrix\t", end="")
        
        self.assertEqual(TEST_VAR_1.is_empty(), False)
        print(" empty", end="")
        
        self.assertEqual(TEST_VAR_ELM_1.get_size(), (1,1)) # test__get_size
        print(" size", end="")
        
        self.assertEqual(TEST_VAR_ELM_1.get_elem(0, 0), RND_ELM_1) # test__get_elem
        self.assertEqual(TEST_VAR_ELM_2.get_elem(0, 0), RND_ELM_2) # test__get_elem
        print(" get", end="")

        self.assertEqual(TEST_VAR_ELM_1.__str__(), f"{RND_ELM_1}")
        self.assertEqual(TEST_VAR_ELM_2.__str__(), f"{RND_ELM_2}")
        print(" str", end="")
        self.assertEqual(TEST_VAR_ELM_1 + TEST_VAR_ELM_2, TEST_VAR_ELM_ADD)
        self.assertEqual(TEST_VAR_ELM_2 + TEST_VAR_ELM_1, TEST_VAR_ELM_ADD)
        self.assertEqual(TEST_VAR_ELM_1 - TEST_VAR_ELM_2, TEST_VAR_ELM_SUB12)
        self.assertEqual(TEST_VAR_ELM_2 - TEST_VAR_ELM_1, TEST_VAR_ELM_SUB21)
        print(" + - = ")

        
        # big 
        print("\tBig matrix\t", end="")
        BIG_COUNT = 1000
        BIG_COUNT_BY = 10
        BIG = [random.randint(-100, 100) for _ in range(BIG_COUNT)]
        BIG_MATRIX = task.Matrix(*BIG, rows=BIG_COUNT//BIG_COUNT_BY)

        self.assertEqual(BIG_MATRIX.is_empty(), False)
        print(" empty", end="")

        self.assertEqual(BIG_MATRIX.get_size(), (BIG_COUNT_BY, BIG_COUNT // BIG_COUNT_BY))
        print(" size", end="")
        BIG_SIZE_C, BIG_SIZE_R = BIG_MATRIX.get_size()
        # Think: why [column + row * rows] no work
        RAND_R = random.randint(0, BIG_SIZE_R - 1)
        RAND_C = random.randint(0, BIG_SIZE_C - 1)
        self.assertEqual(BIG_MATRIX.get_elem(0, 0), BIG[0])
        self.assertEqual(BIG_MATRIX.get_elem(BIG_SIZE_C-1, BIG_SIZE_R-1), BIG[-1])
        print(" get", end="")
        # print(" str", end="")
        BIG_ADD = BIG_MATRIX + BIG_MATRIX
        self.assertEqual(BIG_ADD.get_elem(0, 0), BIG[0]+BIG[0])
        self.assertEqual(BIG_ADD.get_elem(BIG_SIZE_C-1, BIG_SIZE_R-1), BIG[-1]+BIG[-1])
        print(" + - = ")
        #
        #
        # bad split 
        self.assertRaises(ValueError, task.Matrix, 1,2,3, rows=2)
        self.assertRaises(ValueError, task.Matrix, 0, rows=2)
        self.assertRaises(ValueError, task.Matrix, 9,8,7,6,5,4, rows=-1)
        # add wrong index
        print("\tErrors")

if __name__ == "__main__":
    unittest.main()

