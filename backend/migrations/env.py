# backend/migrations/env.py

import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 将项目根目录添加到路径，方便导入 app 模块
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# 导入 Base，供 target_metadata 使用
from app.infrastructure.database.models import Base

# Alembic Config 对象，读取 alembic.ini
config = context.config

# 读取 alembic.ini 中的日志配置
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        # If alembic.ini logging section is misconfigured,
        # proceed without logger setup.
        pass

# 指定 MetaData 对象为 Base.metadata，以支持自动生成迁移
target_metadata = Base.metadata  # 

def run_migrations_offline():
    """在离线模式下运行迁移（不需要实际连接数据库）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    """在异步环境中运行迁移（配合 AsyncEngine）"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    """在在线模式下运行迁移，使用 asyncio 运行"""
    asyncio.run(run_async_migrations())

# 根据模式选择执行流程
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
