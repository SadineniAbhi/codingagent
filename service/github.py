import httpx
from utils.logger import get_logger
from utils.custom_errors import APIError, InvalidGitHubToken, GitHubAPIError, UnableToCloneRepoError
from service.bash_service import run_command


class GithubService:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    async def s_verify_token(self, token: str) -> dict:
        try:
            self.logger.debug("Verifying GitHub token")

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get("https://api.github.com/user", headers=headers)
            except httpx.RequestError:
                raise GitHubAPIError("Failed to reach GitHub API", status_code=502)

            self.logger.debug("GitHub API responded with status %s", resp.status_code)

            if resp.status_code == 401:
                self.logger.warning("GitHub token rejected with 401 — token invalid or expired")
                raise InvalidGitHubToken("Invalid or expired GitHub token", status_code=401)

            if resp.status_code != 200:
                self.logger.error("Unexpected GitHub API status %s: %s", resp.status_code, resp.text)
                raise GitHubAPIError(f"GitHub API returned unexpected status {resp.status_code}", status_code=502)

            scopes = [s.strip() for s in resp.headers.get("x-oauth-scopes", "").split(",") if s.strip()]
            has_repo = "repo" in scopes

            if not has_repo:
                self.logger.warning("Token is missing 'repo' scope — current scopes: %s", scopes)
                raise GitHubAPIError("GitHub token is missing 'repo' scope", status_code=403)

            return {
                "scopes": scopes,
                "has_repo_access": has_repo,
            }

        except APIError:
            raise
        except Exception as exc:
            raise GitHubAPIError("An unexpected error occurred", status_code=500) from exc

    async def s_list_repos(self, token: str) -> list[dict]:
        await self.s_verify_token(token)
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }

            repos = []
            page = 1

            async with httpx.AsyncClient() as client:
                while True:
                    try:
                        resp = await client.get(
                            "https://api.github.com/user/repos",
                            headers=headers,
                            params={"per_page": 100, "page": page},
                        )
                    except httpx.RequestError:
                        raise GitHubAPIError("Failed to reach GitHub API", status_code=502)

                    if resp.status_code == 401:
                        self.logger.warning("GitHub token rejected with 401 while listing repos")
                        raise InvalidGitHubToken("Invalid or expired GitHub token", status_code=401)

                    if resp.status_code != 200:
                        self.logger.error("Unexpected GitHub API status %s: %s", resp.status_code, resp.text)
                        raise GitHubAPIError(f"GitHub API returned unexpected status {resp.status_code}", status_code=502)

                    page_repos = resp.json()
                    if not page_repos:
                        break

                    repos.extend(page_repos)
                    page += 1

            self.logger.info("Listed %d repos", len(repos))
            return [{"full_name": r["full_name"], "url": r["html_url"]} for r in repos]

        except APIError:
            raise
        except Exception as exc:
            raise GitHubAPIError("An unexpected error occurred", status_code=500) from exc

    def clone_repo(self, repo_url: str, pat_token: str) -> bool:
        self.logger.info("Cloning repository")
        url_with_token = repo_url.replace("https://", f"https://x:{pat_token}@")
        res = run_command(f"git clone {url_with_token}")
        if res.returncode != 0:
            self.logger.error("Failed to clone repository")
            raise UnableToCloneRepoError("Unable to clone the repo please check the secret", 500)
        self.logger.info("Repository cloned successfully")
        return True
