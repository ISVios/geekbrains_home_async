#!/usr/bin/env python
"""
"""
import sys
import argparse
from jim.server import JIMServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JIM server.')
    parser.add_argument("-p",
                        "--port",
                        const=1,
                        type=int,
                        nargs="?",
                        default=7777,
                        help="TCP-port. (default: 7777)")
    parser.add_argument("-a",
                        "--addr",
                        const=1,
                        type=str,
                        nargs="?",
                        default="0.0.0.0",
                        help="IP-addres to listen. (default: 0.0.0.0)")

    parser.add_argument("-c",
                        "--count",
                        const=1,
                        type=int,
                        nargs="?",
                        default=10,
                        help="Count of max supported client. (default: 10).")

    parser.add_argument("-l",
                        "--log",
                        const=1,
                        type=int,
                        nargs="?",
                        default=10,
                        help="Logger level. (default: 10).")

    args = parser.parse_args()

    server = JIMServer()
    server.run(args)
