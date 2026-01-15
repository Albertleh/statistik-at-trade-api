"""Centralized application settings loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-backed settings for database and data source."""
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "tradepulse"
    postgres_user: str = "tradepulse"
    postgres_password: str = "tradepulse"
    data_url: str = "https://data.statistik.gv.at/data/OGD_konjidxhan21_KJIX_H_21_1.csv"

    @property
    def database_dsn(self) -> str:
        """Build a psycopg2 connection string from env settings."""
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password}"
        )


settings = Settings()
