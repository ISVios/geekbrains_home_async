"""
Unit test
How Run:  python -m unit_test.jim_test  
"""

import json
import random
import unittest

import jim


class JIMTest(unittest.TestCase):

    def test_jim_actions(self):
        """
        All JIM ACTIONS ENUM
        """
        print("\nTest JIMAction Enum")
        all_jim_enum = set([
            "authenticate", "join", "leave", "msg", "presence", "probe", "quit"
        ])
        for action in jim.JIMAction:
            self.assertIn(action.value, all_jim_enum)

    def test__gen_jim_req(self):
        print("\nTest 'gen_jim_req'")

        TEST_VAR = {"action": "quit", "time": 123456}

        res_bytes = jim.gen_jim_req(jim.JIMAction.QUIT,
                                    time=123456,
                                    encoding="utf-8")
        res_str = res_bytes.decode("utf-8")
        res_dict = json.loads(res_str)
        self.assertEqual(TEST_VAR, res_dict)

    def test__parser_jim_answ(self):
        print("\nTest 'parser_jim_answ'")
        # no callbacks
        req = jim.gen_jim_req(jim.JIMAction.PRОBE, time=123456)
        answ = jim.parser_jim_answ(req)
        self.assertIs(jim.GoodAnswer, type(answ))
        # with callbacks

        answ = jim.parser_jim_answ(
            req,
            callbacks=[
                lambda x: jim.need_field_value(x, "action", jim.JIMAction.PRОBE
                                               .value),
                lambda x: jim.need_field(x, "time")
            ])
        self.assertIs(jim.GoodAnswer, type(answ))

    def test__response_group(self):
        print("\nTest 'response_group'")
        for num in range(100):
            fist_two_number = str(num).ljust(2, "0")
            # alert
            alert_with_1 = int('1' + fist_two_number)
            alert_with_2 = int('2' + fist_two_number)

            self.assertEqual(jim.ResponseGroup.Alert,
                             jim.response_group(alert_with_1))
            self.assertEqual(jim.ResponseGroup.Alert,
                             jim.response_group(alert_with_2))

            # error
            error_with_3 = int('3' + fist_two_number)
            error_with_4 = int('4' + fist_two_number)
            error_with_5 = int('5' + fist_two_number)

            self.assertEqual(jim.ResponseGroup.Error,
                             jim.response_group(error_with_3))
            self.assertEqual(jim.ResponseGroup.Error,
                             jim.response_group(error_with_4))
            self.assertEqual(jim.ResponseGroup.Error,
                             jim.response_group(error_with_5))
            # unknow
            unknown = int(str(random.randint(6, 9)) + fist_two_number)
            self.assertEqual(jim.ResponseGroup.Unknown,
                             jim.response_group(unknown))

    def test__need_field(self):
        print("\nTest 'need_field'")
        # GOOD
        GOOD_0 = {"time": 12, "action": "probe"}
        GOOD_1 = {"time": 12, "response": 100, "alert": "test"}

        res_0_0 = jim.need_field(GOOD_0, "time")
        res_0_1 = jim.need_field(GOOD_0, "action")

        self.assertEqual(res_0_1, res_0_0)
        self.assertEqual(res_0_0, GOOD_0)

        # BAD
        BAD_0 = {"time": 12, "do": "probe"}
        BAD_1 = {"clock": 12, "return": 100, "res": "test"}

        self.assertRaises(ValueError, jim.need_field, BAD_0, "action")
        self.assertRaises(ValueError, jim.need_field, BAD_1, "response")

    def test__need_field_value(self):
        print("\nTest 'need_field_value'")
        # GOOD
        GOOD_0 = {"time": 12, "action": "probe"}
        GOOD_1 = {"time": 12, "response": 100, "alert": "test"}

        res_0_0 = jim.need_field_value(GOOD_0, "action", "probe")
        res_0_1 = jim.need_field_value(GOOD_0, "time", 12)

        self.assertEqual(res_0_1, res_0_0)
        self.assertEqual(res_0_0, GOOD_0)
        # ToDo: add with many=True

        # BAD
        BAD_0 = {"time": 12, "do": "probe"}
        BAD_1 = {"clock": 12, "return": 100, "res": "test"}

        self.assertRaises(ValueError, jim.need_field, BAD_0, "action", "quit")
        self.assertRaises(ValueError, jim.need_field, BAD_1, "response", 200)
        # ToDo: add with many=True

    def test__gen_jim_answ(self):
        print("\nTest 'gen_jim_answ'")

        # GOOD
        for response_code in [
                100, 120, 200, 234, 300, 312, 400, 346, 400, 404, 500, 501
        ]:
            answ_bytes = jim.gen_jim_answ(response_code,
                                          msg=f"response_code",
                                          time=123456,
                                          encoding="utf-8")
            answ_str = answ_bytes.decode("utf-8")
            answ_dict = json.loads(answ_str)
            if jim.response_group(response_code) == jim.ResponseGroup.Alert:
                self.assertIn("alert", answ_dict)
            elif jim.response_group(response_code) == jim.ResponseGroup.Error:
                self.assertIn("error", answ_dict)
            self.assertEqual(answ_dict["time"], 123456)
        # BAD
        for response_code in [-999, 9, 900, 679, 800]:
            self.assertRaises(ValueError, jim.gen_jim_answ, response_code)

    def test_parse_answ_with_callback(self):

        print("\nTest parser_jim_answ_with_callback")

        GOOD_0 = '{"action": "probe", "time": 12345}'.encode("utf-8")
        GOOD_1 = '{"response": 100, "time": 232}'.encode("utf-8")
        GOOD_2 = '{"action": "presponse", time: 1111}'.encode("utf-8")

        BAD_0 = '{"action": "quit"}'.encode("utf-8")
        BAD_1 = '{"action": "delete_all", "time": 1111}'.encode("utf-8")

        res = jim.parser_jim_answ(
            GOOD_0, callbacks=[jim.time_need, jim.correct_action])

        self.assertIs(jim.GoodAnswer, type(res))
        # print("GOOD_0", res)

        res = jim.parser_jim_answ(GOOD_1,
                                  callbacks=[jim.time_need, jim.response_need])

        self.assertIs(jim.GoodAnswer, type(res))
        # print("GOOD_1", res)

        res = jim.parser_jim_answ(
            BAD_0, callbacks=[jim.time_need, jim.correct_action])

        self.assertIs(jim.BadAnswer, type(res))
        # print("BAD_0", res)
        res = jim.parser_jim_answ(
            BAD_1, callbacks=[jim.time_need, jim.correct_action])

        self.assertIs(jim.BadAnswer, type(res))
        # print("BAD_1", res)


if __name__ == "__main__":
    unittest.main()
