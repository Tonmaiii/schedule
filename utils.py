from pathlib import Path


def create_file(path: str):
    output_file = Path(path)
    output_file.parent.mkdir(exist_ok=True, parents=True)
    return open(output_file, "w", encoding="utf-8")
