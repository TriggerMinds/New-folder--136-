class CountryPackError(Exception):
    def __init__(self, message: str, file_path: str | None = None):
        self.message = message
        self.file_path = file_path
        super().__init__(message)


class CountryPackNotFoundError(CountryPackError):
    pass


class CountryPackValidationError(CountryPackError):
    pass


class CountryPackParseError(CountryPackError):
    pass
