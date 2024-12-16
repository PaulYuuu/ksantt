class BehaveError(Exception):
    """
    Base exception for Behave errors.

    Attributes:
        bdd_type (str): The type of the BDD entity (e.g., Feature, Scenario, Step).
        name (str): The name of the feature, scenario, or step that caused the error.
        reason (str): The reason for the error.
    """

    def __init__(self, bdd_type: str, name: str, reason: str) -> None:
        """
        Initialize a BehaveError.

        Args:
            bdd_type (str): The type of the BDD entity (e.g., Feature, Scenario, Step).
            name (str): The name of the feature, scenario, or step.
            reason (str): The reason for the error.
        """
        self.bdd_type = bdd_type
        self.name = name
        self.reason = reason

    def __str__(self) -> str:
        """Return a string representation of the error."""
        return f"{self.bdd_type} '{self.name}' is marked to Error, reason: {self.reason}"


class BehaveFeatureError(BehaveError):
    """
    Exception for Feature-level errors in Behave.

    Inherits from BehaveError.
    """

    def __init__(self, name: str, reason: str) -> None:
        """
        Initialize a BehaveFeatureError.

        Args:
            name (str): The name of the feature.
            reason (str): The reason for the feature error.
        """
        super().__init__(bdd_type="Feature", name=name, reason=reason)


class BehaveScenarioError(BehaveError):
    """
    Exception for Scenario-level errors in Behave.

    Inherits from BehaveError.
    """

    def __init__(self, name: str, reason: str) -> None:
        """
        Initialize a BehaveScenarioError.

        Args:
            name (str): The name of the scenario.
            reason (str): The reason for the scenario error.
        """
        super().__init__(bdd_type="Scenario", name=name, reason=reason)


class BehaveStepError(BehaveError):
    """
    Exception for Step-level errors in Behave.

    Inherits from BehaveError.
    """

    def __init__(self, name: str, reason: str) -> None:
        """
        Initialize a BehaveStepError.

        Args:
            name (str): The name of the step.
            reason (str): The reason for the step error.
        """
        super().__init__(bdd_type="Step", name=name, reason=reason)
