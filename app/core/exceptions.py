"""Custom exceptions for Wildlife Conservation API"""

class WildlifeConservationException(Exception):
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class KoboAPIException(WildlifeConservationException):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(f"Kobo API Error: {message}", status_code)

class DatabaseException(WildlifeConservationException):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(f"Database Error: {message}", status_code)
