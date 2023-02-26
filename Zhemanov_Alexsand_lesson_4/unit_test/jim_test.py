import unittest

import jim
import json


class JIMTest(unittest.TestCase):

    def test_jim_actions(self):
        """
        All JIM ACTIONS ENUM
        """
        print()
        all_jim_enum = set([
            "authenticate", "join", "leave", "msg", "presence", "probe", "quit"
        ])
        for e in jim.JIM_ACTION:
            self.assertIn(e.value, all_jim_enum)
            print(e, "Found")

    def test_gen_req(self):
        print()

        TEST_DICT_REC = {"action": "quit", "time": 123456}

        test_req = jim.gen_jim_req(jim.JIM_ACTION.QUIT,
                                   encoding="utf-8",
                                   time=123456)
        decode_req = test_req.decode("utf-8")
        test_gen_req_dict = json.loads(decode_req)
        self.assertEqual(TEST_DICT_REC, test_gen_req_dict)
        print("Correct gen req")

    def test_bad_response_code(self):
        print()
        for response_code in [-999, 1, 0, 640, 750, 800, 999]:
            self.assertRaises(ValueError, jim.gen_jim_answ, response_code)
            print(f"Wrong response_code ({response_code}) raise except. OK")

    def test_alert_or_error_answ(self):
        # alert
        for alert_response_code in [100, 120, 200, 234]:
            gen_answ = jim.gen_jim_answ(alert_response_code,
                                        msg=f"{alert_response_code}",
                                        time=123456,
                                        encoding="utf-8")
            decode_answ = gen_answ.decode("utf-8")
            self.assertIn("alert", decode_answ)
            print(f"alert feed for {alert_response_code}")

        print()
        for error_response_code in [300, 312, 400, 346, 400, 404, 500, 501]:
            gen_answ = jim.gen_jim_answ(error_response_code,
                                        msg=f"{error_response_code}",
                                        time=123456,
                                        encoding="utf-8")
            decode_answ = gen_answ.decode("utf-8")
            self.assertIn("error", decode_answ)
            print(f"error feed for {error_response_code}")

    def test_wrong_parse_answ(self):

        print()

        ERROR_TYPE = "ERROR"

        WRON_ANSW = "{'alert':, 'time':111}".encode("ascii")

        res = jim.parser_jim_answ(WRON_ANSW, error_type=ERROR_TYPE)

        self.assertIs(ERROR_TYPE, res)
        print(f"Unknow answer return error_type({ERROR_TYPE})")

    def test_parse_answ_with_callback(self):

        print()

        GOOD_0 = '{"action": "probe", "time": 12345}'.encode("utf-8")
        GOOD_1 = '{"response: 100", time: 232}'

        BAD_0 = '{"action": "quit"}'.encode("utf-8")
        BAD_1 = '{"action": "delete_all", "time": 1111}'.encode("utf-8")

        res = jim.parser_jim_answ(
            GOOD_0, callbacks=[jim.timestamp_need, jim.correct_action])

        print("GOOD_0", res)

        res = jim.parser_jim_answ(
            BAD_0, callbacks=[jim.timestamp_need, jim.correct_action])

        print("BAD_0", res)
        res = jim.parser_jim_answ(
            BAD_1, callbacks=[jim.timestamp_need, jim.correct_action])

        print("BAD_1", res)


if __name__ == "__main__":
    unittest.main()
