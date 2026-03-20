#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from skill_tensor_cycle import main


if __name__ == "__main__":
    raise SystemExit(main(["inventory", *(__import__("sys").argv[1:])]))
