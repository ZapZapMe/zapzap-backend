# Logging configuration
from logging.config import fileConfig

from alembic import context
from db import Base, engine
from models.db import SyncState, Tip, Tweet, User
from sqlalchemy import engine_from_config

target_metadata = Base.metadata

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode"""
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
