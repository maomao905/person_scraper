from pathlib import Path

def mkdir(dir_name):
    dir = Path(dir_name)
    if not dir.exists():
        dir.mkdir(parents=True)
