from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    input_path: Path
    output_path: Path
    debug: bool = True
