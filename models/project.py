from beanie import Document
from pymongo import IndexModel


class Project(Document):
    name: str
    user_id: str
    project_id: str
    github_pat_token: str
    github_repo_url: str
    description: str | None = None

    class Settings:
        name = "projects"
        indexes = [
            IndexModel([("project_id")], unique=True),
            IndexModel([("name")], unique=True),
            IndexModel([("user_id")]),
        ]
