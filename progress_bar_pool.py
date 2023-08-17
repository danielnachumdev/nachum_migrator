from typing import Optional
from tqdm import tqdm
from utils import t_list, t_type

from abc import ABC, abstractmethod


class ProgressBar(ABC):
    @abstractmethod
    def __init__(self, position, **kwargs): ...

    @abstractmethod
    def update(self, amount: float = 1): ...

    @abstractmethod
    def write(self, *args, sep=" ", end="\n"): ...

    @abstractmethod
    def reset(self): ...


class MockProgressBar(ProgressBar):
    _instances = []

    @staticmethod
    def get_instances() -> t_list["MockProgressBar"]:
        return MockProgressBar._instances

    @staticmethod
    def append_instance(instance: "MockProgressBar"):
        MockProgressBar._instances.append(instance)

    @staticmethod
    def _manage_prints(str_to_print: str, instance: Optional["MockProgressBar"] = None) -> None:
        print(f"\r{str_to_print}", end="")

    def __init__(self, iterable=None, position: int = 0, **kwargs):
        self.iterable = iterable
        self.position = position
        self.leave: bool = True
        self.desc: str = ""
        self.total: float = 100
        self.initial_value: float = 0
        self.current_value = 0
        self.ncols: int = 30
        self.unit: str = "it"
        self.pbar_format = "{l_bar} |{bar}| {n_fmt:.2f}/{total_fmt:.2f}{unit} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
        self.__dict__.update(kwargs)
        self.index = len(MockProgressBar.get_instances())
        MockProgressBar.append_instance(self)

    def _draw(self) -> None:
        percent = self.current_value / self.total
        num_to_fill = int(percent * self.ncols)
        progress_str = num_to_fill * "#" + (self.ncols - num_to_fill) * " "
        MockProgressBar._manage_prints(self.pbar_format.format(
            l_bar=self.desc,
            bar=progress_str,
            n_fmt=self.current_value,
            total_fmt=self.total,
            elapsed="?",
            remaining="?",
            rate_fmt="?",
            postfix="?",
            unit=self.unit
        ), self)

    def update(self, amount: float = 1):
        self.current_value = min(self.current_value + amount, self.total)
        self._draw()

    def write(self, *args, sep=" ", end="\n"):
        MockProgressBar._manage_prints(sep.join(map(str, args)) + end)

    def reset(self):
        self.current_value = self.initial_value
        self._draw()


class ProgressBarPool:
    def __init__(
            self,
            pbar_class: t_type[ProgressBar],
            num_of_bars: int = 1,
            global_options: Optional[dict] = None,
            individual_options: Optional[t_list[Optional[dict]]] = None
    ) -> None:
        self.bars: t_list[tqdm] = []
        if global_options is None:
            global_options = {}
        if individual_options is None:
            individual_options = [{} for _ in range(num_of_bars)]
        if len(individual_options) != num_of_bars:
            raise ValueError("")
        for i in range(num_of_bars):
            if individual_options[i] is None:
                individual_options[i] = {}
        for i in range(num_of_bars):
            final_options: dict = global_options.copy()
            final_options.update(individual_options[i])  # type:ignore
            if "desc" not in final_options:
                final_options["desc"] = f"pbar {i}"
            t = pbar_class(
                position=i,
                **final_options
            )
            self.bars.append(t)

    def write(self, *args, sep=" ", end="\n") -> None:
        self.bars[0].write(sep.join((str(a) for a in args)), end=end)


__all__ = [
    "ProgressBarPool"
]
