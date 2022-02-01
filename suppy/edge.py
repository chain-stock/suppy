from dataclasses import dataclass, field


@dataclass(frozen=True, eq=True)
class Edge:
    """A relation between two nodes

    Arguments:
        source: The predecessor of the `destination` Node
        destination: The successor of the `source` Node
        number: The amount of `source` needed to make `destination`.
            should be > 0
    """

    source: str
    destination: str
    number: int = field(compare=False)  # Only check source and destination for equality

    @property
    def id(self) -> str:
        """Provide the id attribute so we can be used as a key in an IdDict"""
        return f"{self.source}->{self.destination}"

    def __post_init__(self) -> None:
        """Ensure that number is > 0"""
        if self.number <= 0:
            raise ValueError("Edge.number must be more than 0")
