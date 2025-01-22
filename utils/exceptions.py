class BehaveError(Exception):
    """
    Base exception for Behave errors.
    """

    def __init__(self, bdd_type: str, name: str, reason: str):
        """
        Initialize a BehaveError.
        """
        self.bdd_type = bdd_type
        self.name = name
        self.reason = reason

    def __str__(self):
        """
        Return a string representation of the error.
        """
        return f"{self.bdd_type} '{self.name}' is marked to Error, reason: {self.reason}"


class BehaveFeatureError(BehaveError):
    """
    Exception for Feature-level errors in Behave.
    """

    def __init__(self, name: str, reason: str):
        """
        Initialize a BehaveFeatureError.
        """
        super().__init__(bdd_type="Feature", name=name, reason=reason)


class BehaveScenarioError(BehaveError):
    """
    Exception for Scenario-level errors in Behave.
    """

    def __init__(self, name: str, reason: str):
        """
        Initialize a BehaveScenarioError.
        """
        super().__init__(bdd_type="Scenario", name=name, reason=reason)


class BehaveStepError(BehaveError):
    """
    Exception for Step-level errors in Behave.
    """

    def __init__(self, name: str, reason: str):
        """
        Initialize a BehaveStepError.
        """
        super().__init__(bdd_type="Step", name=name, reason=reason)
