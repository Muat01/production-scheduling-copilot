"""
Classic job-shop benchmark instances, downloaded on demand (not redistributed).

Source: JSPLIB (github.com/tamy0612/JSPLIB), which collects the OR-Library
instances. Optimal makespans as listed in JSPLIB's instances.json. Original
references: Fisher & Thompson (1963) for ft06/ft10, Lawrence (1984) for la*,
Adams, Balas & Zawack (1988) for abz5.
"""
from __future__ import annotations

import os
import tempfile
import urllib.request

from jobshop import FT06, Instance, parse_standard

URL = "https://raw.githubusercontent.com/tamy0612/JSPLIB/master/instances/{name}"
OPTIMUM = {"ft06": 55, "ft10": 930, "la01": 666, "la02": 655, "la03": 597, "la04": 590,
           "la05": 593, "la16": 945, "la19": 842, "abz5": 1234}
SOURCE = {"ft06": "Fisher & Thompson (1963)", "ft10": "Fisher & Thompson (1963)", "abz5": "Adams et al. (1988)"}


def load(name: str) -> Instance:
    if name == "ft06":
        return parse_standard(FT06, "ft06")
    cache = os.path.join(tempfile.gettempdir(), "jsplib")
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, name)
    if not os.path.exists(path):
        with urllib.request.urlopen(URL.format(name=name), timeout=30) as r, open(path, "wb") as f:
            f.write(r.read())
    with open(path) as f:
        return parse_standard(f.read(), name)
