import os
from gp_wrapper.utils import get_python_version

if get_python_version() < (3, 9):
    from typing import List as t_list,Dict as t_dict
else:
    from builtins import list as t_list,dict as t_dict


def _get_children(folder: str) -> t_list[str]:
    return os.listdir(folder)


def get_files(folder: str) -> t_list[str]:
    res = []
    for child in _get_children(folder):
        if os.path.isfile(f"{folder}/{child}"):
            res.append(child)
    return res


def get_directories(folder: str) -> t_list[str]:
    res = []
    for child in _get_children(folder):
        if os.path.isdir(f"{folder}/{child}"):
            res.append(child)
    return res
_INFO = "INFO:"  # ColoredText.yellow("INFO")+":"
_WARNING = "WARNING:"  # ColoredText.orange("WARNING")+":"
_ERROR = "ERROR:"  # ColoredText.red("ERROR")+":"
MARGIN = len(_WARNING) + 4
INFO, WARNING, ERROR = [s.ljust(MARGIN) for s in [_INFO, _WARNING, _ERROR]]
def directory_exists(folder:str)->bool:
    return os.path.exists(folder) and os.path.isdir(folder)
__all__ = [
    "get_files",
    "get_directories",
    "directory_exists",
    "t_dict",
    "t_list",
    "INFO",
    "WARNING",
    "ERROR"
]
