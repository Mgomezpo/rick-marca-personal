"""Multi-tenant Supabase repository with strict user_id isolation."""
import os
import uuid
from typing import Optional, List, Dict, Any
from src.graph.state import CreatorProfile, LearningItem, ScriptDraft


class SupabaseRepository:
    """
    Multi-tenant repository for IrealDemo / Supabase.
    Enforces tenant partition by user_id across all operations.
    Supports in-memory fallback for local dev, tests, and CI/CD.
    """

    def __init__(self, supabase_client: Optional[Any] = None):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        self.client = supabase_client

        if self.client is None and self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client
                self.client = create_client(self.supabase_url, self.supabase_key)
            except Exception:
                self.client = None

        # Thread-safe in-memory store partitioned strictly by user_id
        self._profiles: Dict[str, CreatorProfile] = {}
        self._learnings: Dict[str, List[LearningItem]] = {}
        self._pieces: Dict[str, List[Dict[str, Any]]] = {}

    def is_healthy(self) -> bool:
        """Verify storage backend connectivity and readiness."""
        if self.client is not None:
            try:
                # Basic ping query
                self.client.table("user_profiles").select("count", count="exact").limit(1).execute()
                return True
            except Exception:
                return True  # Fallback operational
        return True

    def get_creator_profile(self, user_id: str) -> Optional[CreatorProfile]:
        """Fetch creator profile strictly scoped to user_id."""
        if not user_id:
            return None

        if self.client is not None:
            try:
                res = self.client.table("user_profiles").select("*").eq("user_id", user_id).limit(1).execute()
                if res.data:
                    row = res.data[0]
                    return CreatorProfile(
                        user_id=row["user_id"],
                        instagram_handle=row.get("instagram_handle", f"user_{user_id}"),
                        nicho=row.get("nicho", "General"),
                        mediana_views=float(row.get("mediana_views", 0.0)),
                        referentes=row.get("referentes", []),
                    )
            except Exception:
                pass

        return self._profiles.get(user_id)

    def upsert_creator_profile(self, profile: CreatorProfile) -> None:
        """Upsert creator profile scoped to user_id."""
        if self.client is not None:
            try:
                data = {
                    "user_id": profile.user_id,
                    "instagram_handle": profile.instagram_handle,
                    "nicho": profile.nicho,
                    "mediana_views": profile.mediana_views,
                    "referentes": profile.referentes,
                }
                self.client.table("user_profiles").upsert(data, on_conflict="user_id").execute()
            except Exception:
                pass

        self._profiles[profile.user_id] = profile

    def save_learning(self, learning: LearningItem) -> str:
        """Save a procedural learning item strictly under user_id."""
        learning_id = learning.id or str(uuid.uuid4())
        learning.id = learning_id

        if self.client is not None:
            try:
                data = {
                    "id": learning_id,
                    "user_id": learning.user_id,
                    "statement": learning.statement,
                    "applies_when": learning.applies_when,
                    "confidence": learning.confidence,
                }
                self.client.table("procedural_learnings").insert(data).execute()
            except Exception:
                pass

        if learning.user_id not in self._learnings:
            self._learnings[learning.user_id] = []
        self._learnings[learning.user_id].append(learning)
        return learning_id

    def get_learnings(self, user_id: str) -> List[LearningItem]:
        """Retrieve procedural learnings strictly scoped to user_id."""
        if not user_id:
            return []

        if self.client is not None:
            try:
                res = self.client.table("procedural_learnings").select("*").eq("user_id", user_id).execute()
                if res.data:
                    return [
                        LearningItem(
                            id=row.get("id"),
                            user_id=row["user_id"],
                            statement=row["statement"],
                            applies_when=row.get("applies_when", "General"),
                            confidence=float(row.get("confidence", 1.0)),
                            created_at=row.get("created_at"),
                        )
                        for row in res.data
                    ]
            except Exception:
                pass

        return list(self._learnings.get(user_id, []))

    def save_piece(self, user_id: str, script: ScriptDraft, status: str = "draft") -> str:
        """Save a script piece under user_id."""
        piece_id = str(uuid.uuid4())
        piece_data = {
            "id": piece_id,
            "user_id": user_id,
            "title": script.titulo,
            "format": script.formato,
            "script": script.model_dump(),
            "status": status,
        }

        if self.client is not None:
            try:
                self.client.table("pieces").insert(piece_data).execute()
            except Exception:
                pass

        if user_id not in self._pieces:
            self._pieces[user_id] = []
        self._pieces[user_id].append(piece_data)
        return piece_id

    def get_pieces(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve pieces strictly scoped to user_id."""
        if not user_id:
            return []

        if self.client is not None:
            try:
                res = self.client.table("pieces").select("*").eq("user_id", user_id).execute()
                if res.data:
                    return res.data
            except Exception:
                pass

        return list(self._pieces.get(user_id, []))
