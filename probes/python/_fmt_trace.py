#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import traceback
from formatron.schemas import json_schema

schema_dict = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "score": {"type": "number"}},
    "required": ["name", "score"],
    "$id": "https://example.com/test.json",
    "$schema": "http://json-schema.org/draft-07/schema#"
}

try:
    schema_obj = json_schema.create_schema(schema_dict)
    print("create_schema OK:", type(schema_obj).__name__)
    print("MRO:", [c.__name__ for c in type(schema_obj).__mro__[:5]])
    from formatron.formatter import FormatterBuilder
    f = FormatterBuilder()
    f.append_line("{}".format(f.json(schema_obj)))
    print("FormatterBuilder.json OK")
except Exception:
    traceback.print_exc()
