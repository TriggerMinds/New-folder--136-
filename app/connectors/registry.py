from app.connectors.base import BaseConnector
from app.connectors.exceptions import ConnectorTypeNotFoundError

_registry: dict[str, type[BaseConnector]] = {}


def register_connector(source_type: str, connector_class: type[BaseConnector]) -> None:
    _registry[source_type] = connector_class


def get_connector(source_type: str) -> BaseConnector:
    cls = _registry.get(source_type)
    if cls is None:
        raise ConnectorTypeNotFoundError(
            f"Onbekend connectortype: {source_type}. Beschikbaar: {list(_registry.keys())}",
            source_id=source_type,
        )
    return cls()
