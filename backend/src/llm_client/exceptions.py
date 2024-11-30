class LLMClientInitializeException(Exception):

    def __init__(
        self,
        message: str = "Failed to initialize the LLM client due to an error",
    ):
        self.message = message
        super().__init__(self.message)
