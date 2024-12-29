class UpvoteException(Exception):
    """
    Exception raised when an error occurs while upvoting a news article.
    """

    def __init__(
        self,
        message: str = "Failed to upvote the news article",
    ):
        self.message = message
        super().__init__(self.message)