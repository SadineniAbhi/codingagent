from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    name: str
    github_pat_token: str
    github_repo_url: str
    description: str | None = None
