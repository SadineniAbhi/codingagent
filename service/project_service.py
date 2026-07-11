import uuid
from utils.logger import get_logger
from models.project import Project
from utils.custom_errors import APIError, ProjectError
from payloads.project import CreateProjectRequest
from clients.kuberentes import KubernetesClient


class ProjectService:
    def __init__(self, k8s: KubernetesClient) -> None:
        self.logger = get_logger(__name__)
        self.k8s = k8s

    async def get_project_by_id(self, project_id: str, user_id: str) -> Project:
        try:
            project = await Project.find_one(Project.project_id == project_id)

            if not project:
                self.logger.warning("No project found with id '%s'", project_id)
                raise ProjectError(f"Project '{project_id}' not found", status_code=404)

            if project.user_id != user_id:
                self.logger.warning("User is unauthorized to access project '%s'", project_id)
                raise ProjectError(f"Unauthorized to access project '{project_id}'", status_code=401)

            return project

        except APIError:
            raise
        except Exception as exc:
            raise ProjectError("Failed to fetch project", status_code=500) from exc

    async def s_list_projects(self, user_id: str) -> dict:
        try:
            projects = await Project.list_projects(user_id)
            self.logger.info("Listed %d projects for user '%s'", len(projects), user_id)
            return {"projects": [p.model_dump() for p in projects]}

        except APIError:
            raise
        except Exception as exc:
            raise ProjectError("Failed to list projects", status_code=500) from exc

    async def s_create_project(self, body: CreateProjectRequest, user_id: str) -> dict:
        try:
            project = await Project.create_project(
                name=body.name,
                user_id=user_id,
                project_id=str(uuid.uuid4()),
                github_pat_token=body.github_pat_token,
                github_repo_url=body.github_repo_url,
                description=body.description,
            )
            self.logger.info("Created project '%s' for user '%s'", project.project_id, user_id)
            return {"project_id": project.project_id, "name": project.name}

        except APIError:
            raise
        except Exception as exc:
            raise ProjectError("Failed to create project", status_code=500) from exc

