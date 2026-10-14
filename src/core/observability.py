import contextvars
import json
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

# Context Variables para propagación de contexto en hilos y corutinas asíncronas
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")
_entry_point: contextvars.ContextVar[str] = contextvars.ContextVar("entry_point", default="system")
_user_id: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")

def generate_correlation_id(prefix: str = "req") -> str:
    """Genera un identificador de correlación único y legible."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def set_request_context(
    correlation_id: Optional[str] = None,
    entry_point: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """Fija el contexto de la solicitud en el contexto asíncrono actual."""
    if correlation_id is not None:
        _correlation_id.set(correlation_id)
    if entry_point is not None:
        _entry_point.set(entry_point)
    if user_id is not None:
        _user_id.set(user_id)

def get_correlation_id() -> str:
    return _correlation_id.get() or "no_corr_id"

def get_entry_point() -> str:
    return _entry_point.get() or "unknown"

def get_user_id() -> str:
    return _user_id.get() or "anonymous"

class StructuredLogRecord(logging.LogRecord):
    """LogRecord enriquecido con datos de observabilidad contextual."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.correlation_id = get_correlation_id()
        self.entry_point = get_entry_point()
        self.user_id = get_user_id()

class StructuredFormatter(logging.Formatter):
    """
    Formateador de logs estructurados legible para humanos y fácilmente
    parseable por sistemas de observabilidad (CloudWatch, Datadog, GCP Logging).
    """
    def format(self, record: logging.LogRecord) -> str:
        corr_id = getattr(record, "correlation_id", get_correlation_id())
        entry = getattr(record, "entry_point", get_entry_point())
        uid = getattr(record, "user_id", get_user_id())
        event = getattr(record, "event", "log")
        
        asctime = self.formatTime(record, self.datefmt)
        base = f"{asctime} [{record.levelname}] [{entry}] [{corr_id}] [{event}] {record.getMessage()}"
        
        # Atributos adicionales pasados en extra
        extras = getattr(record, "structured_extra", {})
        if extras:
            formatted_extras = " ".join(f"{k}={v}" for k, v in extras.items())
            base = f"{base} | {formatted_extras}"

        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base

def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str = "",
    **extra: Any
) -> None:
    """
    Emite un log estructurado con nombre de evento estable y atributos clave-valor.
    Garantiza consistencia y trazabilidad sin cadenas de texto huérfanas.
    """
    # Evitar registrar secretos o tokens por seguridad
    safe_extra = {}
    for k, v in extra.items():
        k_lower = k.lower()
        if "token" in k_lower or "secret" in k_lower or "password" in k_lower or "key" in k_lower:
            safe_extra[k] = "[REDACTED]"
        else:
            safe_extra[k] = v

    extra_dict = {
        "event": event,
        "correlation_id": get_correlation_id(),
        "entry_point": get_entry_point(),
        "user_id": get_user_id(),
        "structured_extra": safe_extra,
    }
    logger.log(level, message or event, extra=extra_dict)

@contextmanager
def trace_span(
    name: str,
    logger: Optional[logging.Logger] = None,
    entry_point: Optional[str] = None,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **attributes: Any
) -> Iterator[Dict[str, Any]]:
    """
    Context manager para medir la duración de una operación (LLM, tool, base de datos)
    y registrar el span en logs estructurados con correlación.
    """
    if entry_point or correlation_id or user_id:
        set_request_context(
            correlation_id=correlation_id,
            entry_point=entry_point,
            user_id=user_id
        )

    active_logger = logger or logging.getLogger("rick.trace")
    start = time.time()
    span_info: Dict[str, Any] = {
        "name": name,
        "attributes": dict(attributes),
        "status": "in_progress",
    }

    log_event(
        active_logger,
        logging.DEBUG,
        event=f"{name}_started",
        message=f"Iniciando span: {name}",
        **attributes
    )

    try:
        yield span_info
        elapsed_ms = int((time.time() - start) * 1000)
        span_info["status"] = "success"
        span_info["duration_ms"] = elapsed_ms

        log_event(
            active_logger,
            logging.INFO,
            event=f"{name}_completed",
            message=f"Span completado: {name} en {elapsed_ms}ms",
            duration_ms=elapsed_ms,
            **attributes
        )
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        span_info["status"] = "error"
        span_info["duration_ms"] = elapsed_ms
        span_info["error"] = str(e)

        log_event(
            active_logger,
            logging.ERROR,
            event=f"{name}_failed",
            message=f"Span fallido: {name} ({e}) en {elapsed_ms}ms",
            duration_ms=elapsed_ms,
            error_type=type(e).__name__,
            error_message=str(e),
            **attributes
        )
        raise
