"""Repository: satu modul per agregat (users, models, predictions)."""

from app.db.repositories import model_repo, prediction_repo, user_repo

__all__ = ["user_repo", "model_repo", "prediction_repo"]
