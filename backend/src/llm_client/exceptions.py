class LLMClientInitializeException(Exception):
    """
    Exception raised for errors during the initialization of the LLM client.
    """

    def __init__(
        self,
        message: str = "Failed to initialize the LLM client due to an error",
    ):
        self.message = message
        super().__init__(self.message)

class EvaluationFailure(ValueError):
    """
    Exception raised when the evaluation of the relevance of the news title with the prompt fails.
    Or when the response from the LLM model cannot be decoded (invalid json).
    """
    def __init__(
        self,
        message: str = "Failed to evaluate the relevance of the news title with the prompt",
    ):
        self.message = message
        super().__init__(self.message)
