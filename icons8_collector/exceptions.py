from typing import Optional, Any


class Icons8CollectorError(Exception):

    def __init__(
        self, 
        message: str, 
        *,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        # Sanitize message to prevent sensitive data leakage
        self.message = self._sanitize_message(message)
        self.context = context or {}
        self.original_error = original_error
        super().__init__(self.message)
    
    @staticmethod
    def _sanitize_message(message: str) -> str:
        import re
        # Redact email addresses
        message = re.sub(
            r'[\w\.-]+@[\w\.-]+\.\w+', 
            '[EMAIL REDACTED]', 
            message
        )
        # Redact potential passwords or tokens (common patterns)
        message = re.sub(
            r'(password|token|secret|key|auth)[=:\s]+[^\s]+',
            r'\1=[REDACTED]',
            message,
            flags=re.IGNORECASE
        )
        return message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


class AuthenticationError(Icons8CollectorError):

    def __init__(
        self,
        message: str,
        *,
        login_attempted: bool = True,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        self.login_attempted = login_attempted
        super().__init__(
            message, 
            context=context, 
            original_error=original_error
        )


class ScrapingError(Icons8CollectorError):

    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        icons_found: int = 0,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        self.url = url
        self.icons_found = icons_found
        super().__init__(
            message, 
            context=context, 
            original_error=original_error
        )


class DownloadError(Icons8CollectorError):

    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        self.url = url
        self.status_code = status_code
        super().__init__(
            message, 
            context=context, 
            original_error=original_error
        )


class ConversionError(Icons8CollectorError):

    def __init__(
        self,
        message: str,
        *,
        source_path: Optional[str] = None,
        target_path: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        # Don't store full paths for security
        self.source_filename = source_path.split('/')[-1] if source_path else None
        self.target_filename = target_path.split('/')[-1] if target_path else None
        super().__init__(
            message, 
            context=context, 
            original_error=original_error
        )


class ConfigurationError(Icons8CollectorError):

    def __init__(
        self,
        message: str,
        *,
        config_key: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        self.config_key = config_key
        super().__init__(
            message, 
            context=context, 
            original_error=original_error
        )


class BrowserError(Icons8CollectorError):

    def __init__(
        self,
        message: str,
        *,
        browser_type: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        self.browser_type = browser_type
        super().__init__(
            message, 
            context=context, 
            original_error=original_error
        )


class ValidationError(Icons8CollectorError):

    def __init__(
        self,
        message: str,
        *,
        field_name: Optional[str] = None,
        invalid_value: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        self.field_name = field_name
        # Don't store potentially sensitive invalid values
        self.invalid_value_type = type(invalid_value).__name__ if invalid_value else None
        super().__init__(
            message, 
            context=context, 
            original_error=original_error
        )
