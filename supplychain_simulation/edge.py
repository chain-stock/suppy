from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class Edge:
    """A relation between two nodes

    Arguments:
        source: The predecessor of the `destination` Node
        destination: The successor of the `source` Node
        number: The amount of `source` needed to make `destination`
    """

    source: str
    destination: str
    number: int

    @property
    def id(self) -> str:
        """Provide the id attribute so we can be used as a key in an IdDict"""
        return f"{self.source}->{self.destination}"
