from pydantic import BaseModel
from beanie import Document
from pymongo import IndexModel

class _ProjectSummaryProjection(BaseModel): 
    project_id: str
    name: str


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
            IndexModel([("project_id", 1)], unique=True),
            IndexModel([("name", 1)], unique=True),
            IndexModel([("user_id", 1)]),
        ]

    @classmethod
    async def list_projects(cls, user_id: str) -> list["_ProjectSummaryProjection"]:
        return await Project.find(Project.user_id == user_id).project(_ProjectSummaryProjection).to_list()

    @classmethod
    async def find_project(cls, project_id: str) -> "Project | None":
        return await Project.find_one(Project.project_id == project_id)

    @classmethod
    async def create_project(
        cls,
        name: str,
        user_id: str,
        project_id: str,
        github_pat_token: str,
        github_repo_url: str,
        description: str | None,
    ) -> "Project":
        project = Project(
            name=name,
            user_id=user_id,
            project_id=project_id,
            github_pat_token=github_pat_token,
            github_repo_url=github_repo_url,
            description=description,
        )
        return await project.insert()
        
