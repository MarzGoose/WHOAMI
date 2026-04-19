from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Iterator


@dataclass
class Message:
    source: str
    source_id: str
    timestamp: datetime
    sender: str
    content: str
    thread_id: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Transaction:
    source: str
    source_id: str
    timestamp: datetime
    amount: float
    description: str
    category: str = ""
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, path: str) -> Iterator:
        """Yield normalised records from a source file."""
        ...
