"""Curator semantic organization layer."""

from .service import CuratorBuilder

__all__ = ["CuratorBuilder", "CuratorExporter", "create_export"]


def __getattr__(name: str):
    """Keep exporter imports lazy so ``python -m archivist.curator.exporter`` is clean."""
    if name in {"CuratorExporter", "create_export"}:
        from .exporter import CuratorExporter, create_export

        return {"CuratorExporter": CuratorExporter, "create_export": create_export}[name]
    raise AttributeError(name)
