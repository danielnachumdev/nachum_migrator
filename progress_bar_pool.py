import time
from abc import ABC, abstractmethod
from typing import Optional
from tqdm import tqdm
from utils import t_list, t_type
from gp_wrapper import ProgressBar

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
        self.pbar_format = "{l_bar} |{bar}| {n_fmt:.2f}/{total_fmt:.2f}{unit}" \
                           " [{elapsed:.2f}<{remaining}, {rate_fmt:.2f}{unit}{postfix}]"
        self.__dict__.update(kwargs)
        self.index = len(MockProgressBar.get_instances())
        MockProgressBar.append_instance(self)
        self.initial_start_time = time.time()
        self.prev_update: float = self.initial_start_time
        self.delta: float = 0
        self.prev_value = self.initial_value

    def _draw(self) -> None:
        percent = self.current_value / self.total
        num_to_fill = int(percent * self.ncols)
        progress_str = num_to_fill * "#" + (self.ncols - num_to_fill) * " "
        to_print = self.pbar_format.format(
            l_bar=self.desc,
            bar=progress_str,
            n_fmt=self.current_value,
            total_fmt=self.total,
            elapsed=self.prev_update - self.initial_start_time,
            remaining="?",
            rate_fmt=(self.current_value - self.prev_value) / self.delta if self.delta != 0 else 0,
            postfix="/s",
            unit=self.unit
        )
        MockProgressBar._manage_prints(to_print, self)

    def update(self, amount: float = 1):
        self.prev_value = self.current_value
        self.current_value = min(self.current_value + amount, self.total)
        current_time = time.time()
        self.delta = current_time - self.prev_update
        self.prev_update = current_time
        self._draw()

    def write(self, *args, sep=" ", end="\n"):
        MockProgressBar._manage_prints(sep.join(map(str, args)) + end)

    def reset(self):
        self.current_value = self.initial_value
        self.initial_start_time = time.time()
        self.delta = 0
        self.prev_value = self.initial_value
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
            raise ValueError("must suply the same number of options as there are bars")
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
