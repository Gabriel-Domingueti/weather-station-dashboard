import logging
from datetime import datetime, timezone

import pandas as pd

from app.infrastructure.csv_repository import CSVRepository

logger = logging.getLogger(__name__)


class DataCache:
    """
    Mantém o daily_summary.csv em memória e sabe quando foi atualizado
    pela última vez. Evita que toda requisição do front dispare uma
    chamada ao GitHub, e sobrevive tranquilamente aos cold starts do
    free tier (o primeiro request após "acordar" já recarrega tudo).
    """

    def __init__(self, repository: CSVRepository) -> None:
        self._repository = repository
        self.daily_summary: pd.DataFrame = pd.DataFrame()
        self.last_refreshed: datetime | None = None

    async def refresh(self) -> None:
        logger.info("Atualizando cache de dados a partir do GitHub...")
        self.daily_summary = await self._repository.fetch_daily_summary()
        self.last_refreshed = datetime.now(timezone.utc)
        logger.info("Cache atualizado: %s linhas", len(self.daily_summary))

    async def ensure_fresh(self) -> None:
        if self.last_refreshed is None:
            await self.refresh()


# Instância única compartilhada pela aplicação (injetada via app.state)
data_cache = DataCache(repository=CSVRepository())
