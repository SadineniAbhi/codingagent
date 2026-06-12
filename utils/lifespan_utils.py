import json
from custom_errors import UnableToCloneRepoError 

from service.bash_service import run_command



def clone_repo(repo_url: str, pat_token: str) -> bool:
    url_with_token = repo_url.replace("https://", f"https://x:{pat_token}@")
    res = run_command(f"git clone {url_with_token}")
    if res.returncode != 0:
        raise UnableToCloneRepoError("Unable to clone the repo please check the secret", 500)
    return True
