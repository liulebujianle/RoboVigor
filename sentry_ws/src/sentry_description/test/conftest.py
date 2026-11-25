"""为源码目录中的 Xacro 检查提供包路径。"""
from pathlib import Path

import pytest
import xacro.substitution_args

PACKAGE = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def description_source_lookup(monkeypatch):
    """替换 ROS 包路径查找，仍使用实际 Xacro 模型展开。"""
    lookup = xacro.substitution_args._eval_find

    def find(package):
        return PACKAGE.as_posix() if package == 'sentry_description' else lookup(package)

    monkeypatch.setattr(xacro.substitution_args, '_eval_find', find)
