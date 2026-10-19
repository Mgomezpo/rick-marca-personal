"""Models for content matrix and video analytics (10 Canonical Columns)."""
from typing import Dict, Any
from pydantic import BaseModel, Field


class MatrixRow(BaseModel):
    """
    Standard 10-column canonical schema for video content analysis.
    Captures creator metrics, relative performance, and hook/narrative anatomy.
    """
    post_id: str = Field(..., description="ID único o URL del post")
    account_handle: str = Field(..., description="Handle de Instagram del creador")
    views: int = Field(..., ge=0, description="Visualizaciones totales registradas")
    account_median: float = Field(..., ge=0, description="Mediana histórica de la cuenta")
    relative_performance: float = Field(..., ge=0, description="Multiplicador R = views / account_median")
    hook_text: str = Field(..., description="Texto literal del gancho (primeros 3 segundos)")
    hook_type: str = Field(..., description="Categoría del gancho (ej. 'confesion_error', 'quiebre_creencia')")
    format: str = Field(..., description="Contenedor visual (ej. 'historia_personal', 'leccion', 'pantalla')")
    emotion: str = Field(..., description="Intención o emoción psicológica provocada")
    duration_seconds: int = Field(..., ge=1, description="Duración total del video en segundos")

    @classmethod
    def from_raw(cls, data: Dict[str, Any], account_median: float) -> "MatrixRow":
        """Construct MatrixRow calculating relative performance R automatically."""
        views = int(data.get("views", 0))
        r = round(views / account_median, 2) if account_median > 0 else 0.0

        return cls(
            post_id=str(data.get("post_id", "unknown")),
            account_handle=str(data.get("account_handle", "unknown")),
            views=views,
            account_median=float(account_median),
            relative_performance=r,
            hook_text=str(data.get("hook_text", "")),
            hook_type=str(data.get("hook_type", "general")),
            format=str(data.get("format", "reel")),
            emotion=str(data.get("emotion", "curiosidad")),
            duration_seconds=int(data.get("duration_seconds", 45)),
        )
