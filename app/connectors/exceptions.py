class ConnectorError(Exception):
    def __init__(self, message: str, source_id: str | None = None, http_status: int | None = None):
        self.message = message
        self.source_id = source_id
        self.http_status = http_status
        super().__init__(message)


class ConnectorTypeNotFoundError(ConnectorError):
    pass


class ConnectorHTTPError(ConnectorError):
    pass


class ConnectorParseError(ConnectorError):
    pass
