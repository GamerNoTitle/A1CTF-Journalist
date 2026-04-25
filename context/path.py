import os
from pathlib import Path

def get_workdir():
    return Path(os.getenv("WORKDIR", Path(__file__).parent.parent.absolute()))

if __name__ == "__main__":
    print(get_workdir())