"""Inspect/respond to bounded connector IPC; does not contain credentials."""

import argparse
import json
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("directory")
p.add_argument("--respond")
p.add_argument("--result-file")
a = p.parse_args()
directory = Path(a.directory)
if a.respond:
    if not re.fullmatch(r"[a-f0-9]{32}", a.respond):
        p.error("Invalid request ID")
    if not a.result_file or not (directory / (a.respond + ".request.json")).exists():
        p.error("Existing request and --result-file required")
    result = json.loads(Path(a.result_file).read_text())
    target = directory / (a.respond + ".response.json")
    if target.exists():
        p.error("Response already exists")
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps({"id": a.respond, "result": result}, ensure_ascii=False))
    temp.replace(target)
else:
    for path in sorted(directory.glob("*.request.json")):
        key = path.name.split(".")[0]
        if not (directory / (key + ".response.json")).exists():
            print(path.read_text())
