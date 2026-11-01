"""Tutor adapter interface."""

from abc import ABC, abstractmethod

from radiant.models import Scenario, TutorResponse


class TutorAdapter(ABC):
    name = "base"

    @abstractmethod
    def respond(self, scenario: Scenario) -> TutorResponse:
        """Return a structured response for one scenario."""
