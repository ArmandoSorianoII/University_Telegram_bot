import os
import json
from datetime import datetime
import hashlib


class AnalyticsLogger:
    def __init__(self) -> None:
        self.log_file_path = os.getenv("LOG_FILE_PATH", "logs/interactions.log")
        self.anonymize = os.getenv("ANONYMIZE_LOGS", "false").lower() == "true"
        directory = os.path.dirname(self.log_file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _get_user_id(self, update) -> str | None:
        chat = update.effective_chat
        if not chat:
            return None
        chat_id = str(chat.id)
        if not self.anonymize:
            return chat_id
        return hashlib.sha256(chat_id.encode("utf-8")).hexdigest()

    def log_interaction(self, update, question: str, answer: str, source: str | None = None, used_web: bool | None = None) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": self._get_user_id(update),
            "question": question,
            "answer": answer,
            "source": source,
            "used_web": used_web,
        }
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass
