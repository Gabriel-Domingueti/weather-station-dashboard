from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação, lidas de variáveis de ambiente (.env)."""

    # GitHub - onde os CSVs gerados pelo GitHub Actions estão versionados
    github_owner: str = "seu-usuario"
    github_repo: str = "weather-station-dashboard"
    github_branch: str = "main"

    # ThingSpeak - usado só para a leitura "ao vivo"
    thingspeak_channel_id: str = ""
    thingspeak_read_api_key: str = ""

    # Cache em memória dos CSVs
    cache_refresh_minutes: int = 30

    # CORS - origens permitidas a consumir a API (ajuste para o domínio do front em produção)
    cors_origins: list[str] = ["http://localhost:5173"]

    # Diretório local de dados (para desenvolvimento local / container)
    local_data_dir: str = "/app/data"

    # Chave simples para proteger o endpoint de refresh manual chamado pelo GitHub Actions
    refresh_token: str = "troque-este-token"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def raw_base_url(self) -> str:
        return (
            f"https://raw.githubusercontent.com/{self.github_owner}/"
            f"{self.github_repo}/{self.github_branch}/data"
        )


settings = Settings()
