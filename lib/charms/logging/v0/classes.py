"""Module for general logging functionalities and abstractions."""

from logging import getLogger, Logger
from typing import Callable, Union, Any

from cgnal.core.logging import (
    LevelsDict,
    StrLevelTypes,
)

levels: LevelsDict = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}


class WithLogging:
    """Base class to be used for providing a logger embedded in the class."""

    @property
    def logger(self) -> Logger:
        """
        Create logger.

        :return: default logger
        """
        nameLogger = str(self.__class__).replace("<class '", "").replace("'>", "")
        return getLogger(nameLogger)

    def logResult(
            self, msg: Union[Callable[..., str], str], level: StrLevelTypes = "INFO"
    ) -> Callable[..., Any]:
        """
        Return a decorator to allow logging of inputs/outputs.

        :param msg: message to log
        :param level: logging level
        :return: wrapped method
        """

        def wrap(x: Any) -> Any:
            if isinstance(msg, str):
                self.logger.log(levels[level], msg)
            else:
                self.logger.log(levels[level], msg(x))
            return x

        return wrap
