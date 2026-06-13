import httpx
from utils.logger import get_logger
from utils.custom_errors import APIError, InvalidGitHubToken, GitHubAPIError

logger = get_logger(__name__)


async def s_verify_token(token: str) -> dict:
    try:
        logger.debug("Verifying GitHub token")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.github.com/user", headers=headers)
        except httpx.RequestError as exc:
            logger.exception("Network error reaching GitHub API: %s", exc)
            raise GitHubAPIError("Failed to reach GitHub API", status_code=502) 

        logger.debug("GitHub API responded with status %s", resp.status_code)

        if resp.status_code == 401:
            logger.warning("GitHub token rejected with 401 — token invalid or expired")
            raise InvalidGitHubToken("Invalid or expired GitHub token", status_code=401)

        if resp.status_code != 200:
            logger.error("Unexpected GitHub API status %s: %s", resp.status_code, resp.text)
            raise GitHubAPIError(f"GitHub API returned unexpected status {resp.status_code}", status_code=502)

        scopes = [s.strip() for s in resp.headers.get("x-oauth-scopes", "").split(",") if s.strip()]
        has_repo = "repo" in scopes

        if not has_repo:
            logger.warning("Token for user is missing 'repo' scope — current scopes: %s", scopes)
            raise GitHubAPIError("GitHub token is missing 'repo' scope", status_code=403)

        return {
            "scopes": scopes,
            "has_repo_access": has_repo,
        }

    except APIError:
        logger.exception("APIError in s_verify_token")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in s_verify_token: %s", exc)
        raise GitHubAPIError("An unexpected error occurred", status_code=500)


async def s_list_repos(token: str) -> list[dict]:
    await s_verify_token(token)
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

        repos = []
        # pagination should be not hard code for now this works ig ha swill do later
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                try:
                    resp = await client.get(
                        "https://api.github.com/user/repos",
                        headers=headers,
                        params={"per_page": 100, "page": page},
                    )
                except httpx.RequestError as exc:
                    logger.exception("Network error fetching repos: %s", exc)
                    raise GitHubAPIError("Failed to reach GitHub API", status_code=502) 

                if resp.status_code == 401:
                    logger.warning("GitHub token rejected with 401 while listing repos")
                    raise InvalidGitHubToken("Invalid or expired GitHub token", status_code=401)

                if resp.status_code != 200:
                    logger.error("Unexpected GitHub API status %s: %s", resp.status_code, resp.text)
                    raise GitHubAPIError(f"GitHub API returned unexpected status {resp.status_code}", status_code=502)

                page_repos = resp.json()
                if not page_repos:
                    break

                repos.extend(page_repos)
                page += 1

        logger.info("Listed %d repos", len(repos))
        return [{"full_name": r["full_name"], "url": r["html_url"]} for r in repos]

    except APIError:
        logger.exception("APIError in s_list_repos")
        raise
    except Exception as exc:
        logger.exception("Unexpected error in s_list_repos: %s", exc)
        raise GitHubAPIError("An unexpected error occurred", status_code=500) 
