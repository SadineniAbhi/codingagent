from utils.custom_errors import UnableToCloneRepoError
from utils.logger import get_logger
from service.bash_service import run_command

logger = get_logger(__name__)


def clone_repo(repo_url: str, pat_token: str) -> bool:
    logger.info("Cloning repository")
    url_with_token = repo_url.replace("https://", f"https://x:{pat_token}@")
    res = run_command(f"git clone {url_with_token}")
    if res.returncode != 0:
        logger.error("Failed to clone repository")
        raise UnableToCloneRepoError("Unable to clone the repo please check the secret", 500)
    logger.info("Repository cloned successfully")
    return True
