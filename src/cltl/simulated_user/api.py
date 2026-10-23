import abc
import dataclasses
from typing import List, Optional

@dataclasses.dataclass
class Object:
    """
    Information about an object.

    Includes the type of the object
    """
    type: str
    label: str
    confidence: Optional[float]

class SimulatedUser(abc.ABC):

    def respond(self, statement: str, history: List[str]) -> Optional[str]:
        """
        Parameters
        ----------
        statement : str
            The utterance to respond to.
        history : List[ImageAnnotation]
            The most recent image annotations that reflect a change, oldest first.

        Returns
        -------
        Optional[str]
            The response, or None if the statement should not be responded to.
        """
        raise NotImplementedError("")
