import uuid
from pydantic import BaseModel
from utils.logger import get_logger
from utils.custom_errors import APIError, ProjectError
from models.project import Project
from payloads.project import CreateProjectRequest


class _ProjectSummaryProjection(BaseModel): 
    project_id: str
    name: str

logger = get_logger(__name__)


async def get_project_by_id(project_id: str, user_id: str) -> Project:
    try:
        project = await Project.find_one(Project.project_id == project_id)

        if not project:
            logger.warning(f"No project found with id `{project_id}")
            raise ProjectError(f"Project '{project_id}' not found", status_code=404)

        if project.user_id != user_id:
            logger.warning(f"user is not authenticated to fetch the details of project '{project_id}'")
            raise ProjectError(f"user is unauthorized to access the project '{project_id}'", status_code=401)

        return project

    except APIError:
        logger.exception("APIError in _get_project_by_id")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in _get_project_by_id: %s", exc)
        raise ProjectError("Failed to fetch project", status_code=500) from exc


async def s_list_projects(user_id: str) -> dict:
    try:
        projects = await Project.find(Project.user_id == user_id).project(_ProjectSummaryProjection).to_list()
        logger.info("Listed %d projects for user '%s'", len(projects), user_id)
        return {"projects": [p.model_dump() for p in projects]}

    except APIError:
        logger.exception("APIError in s_list_projects")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in s_list_projects: %s", exc)
        raise ProjectError("Failed to list projects", status_code=500) from exc


# missing in this method 
# creation of infra
# cloning of the repo
async def s_create_project(body: CreateProjectRequest, user_id: str) -> dict:
    try:
        project = Project(
            name=body.name,
            user_id=user_id,
            project_id=str(uuid.uuid4()),
            github_pat_token=body.github_pat_token,
            github_repo_url=body.github_repo_url,
            description=body.description,
        )
    
        await project.insert()
        logger.info("Created project '%s' for user '%s'", project.project_id, user_id)

        return {"project_id": project.project_id, "name": project.name}

    except APIError:
        logger.exception("APIError in s_create_project")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in s_create_project: %s", exc)
        raise ProjectError("Failed to create project", status_code=500) from exc
