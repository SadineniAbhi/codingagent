from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PAT_TOKEN: str
    REPO_URL: str
    PATH_PREFIX: str
    ANTHROPIC_API_KEY: str

    model_config = {"env_file": ".env"}


settings = Settings() # type: ignore
