class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

class UnableToCloneRepoError(APIError):
    pass

class FailedToStream(APIError):
    pass

class GraphNotPaused(APIError):
    pass

class FailedToResume(APIError):
    pass

class ThreadNotFound(APIError):
    pass

class FailedToGetState(APIError):
    pass

class CommandFailed(APIError):
    pass

class InvalidGitHubToken(APIError):
    pass

class GitHubAPIError(APIError):
    pass

class ProjectError(APIError):
    pass

