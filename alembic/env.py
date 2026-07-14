"""
alembic env.py
- app.core.config.settings.DATABASE_URL을 사용 (alembic.ini의 sqlalchemy.url은 placeholder).
- app.models를 import해서 Base.metadata에 전체 테이블이 등록되게 한 뒤 target_metadata로 넘김
  (autogenerate가 모든 모델을 인식하려면 반드시 import가 선행돼야 함).
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401  (Base.metadata에 테이블 등록 목적)

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """PostGIS가 만드는 시스템 테이블/뷰는 우리 모델이 아니므로 autogenerate diff에서 제외."""
    if type_ == "table" and name in ("spatial_ref_sys",):
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()