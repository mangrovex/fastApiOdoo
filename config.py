import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    db_host: str = 'localhost'
    db_port: int = 5432
    db_user: str = 'admin@manexware.com'
    db_password: str = 'M3d3c2022*'
    db_name: str = 'promedec'

    class Config:
        env_file = os.getenv("ODOO_RC", "odoo.cfg")


def get_settings():
    return Settings()
