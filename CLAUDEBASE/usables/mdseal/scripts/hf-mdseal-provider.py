#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys


def main() -> int:
    if "--doctor" in sys.argv:
        print(json.dumps({
            "schema": "mdseal.provider-doctor.v1",
            "status": "passed",
            "capabilities": [],
            "ocrEnabled": False,
            "modelsLoaded": False,
            "networkUsed": False,
            "message": "Provider sidecar stub is reachable. OCR is not implemented."
        }, indent=2))
        return 0
    print(json.dumps({"schema": "mdseal.provider-doctor.v1", "status": "skipped"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
