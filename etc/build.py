import os
from datetime import datetime
from pathlib import Path

import yaml

from mrilabs.frontend.header import DEFAULT_WORKDIR

info = Path(os.getenv("CONFIG"), "info.yml") or DEFAULT_WORKDIR / "state.json"
build_stamp = {"build_info": "x", "build_version": 0.1}

if not info.exists():
    info.touch()
with open(info, "r+") as file:
    build_stamp["build_info"] = datetime.now()
    yaml.dump(build_stamp, file, default_flow_style=False)
