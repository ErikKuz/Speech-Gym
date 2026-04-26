import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

import requests
from PyQt5.QtCore import QThread, pyqtSignal


class ApiError(Exception):
    pass


class ApiClient:
    _FIELD_LABELS = {
        "email": "Электронная почта",
        "password": "Пароль",
        "fullName": "Имя и фамилия",
        "title": "Название",
        "goal": "Цель",
        "scenario": "Сценарий",
        "languageCode": "Язык",
        "audienceType": "Аудитория",
        "durationTargetSeconds": "Целевая длительность",
        "presentationStyle": "Стиль выступления",
        "notes": "Заметки",
        "file": "Файл",
    }
    _ERROR_TRANSLATIONS = {
        "Invalid credentials.": "Неверная электронная почта или пароль.",
        "Refresh token is missing.": "Отсутствует refresh-токен.",
        "Unexpected PDF response.": "Сервер вернул неожиданный ответ при скачивании PDF.",
        "You need to sign in first.": "Сначала войдите в аккаунт.",
        "Validation failed.": "Проверьте заполненные поля.",
        "Session not found.": "Сессия не найдена.",
        "Upload not found.": "Загруженный файл не найден.",
        "Job not found.": "Задача анализа не найдена.",
        "Report not found.": "Отчет не найден.",
        "Unable to transcribe audio with ASR service.": "Не удалось распознать аудио через ASR-сервис.",
        "Access denied.": "Доступ запрещен.",
        "Forbidden.": "Доступ запрещен.",
        "Unauthorized.": "Требуется повторный вход в аккаунт.",
    }
    _ERROR_SUBSTRINGS = (
        ("Connection refused", "Сервис временно недоступен. Попробуйте снова через несколько секунд."),
        ("timed out", "Сервис не ответил вовремя. Попробуйте еще раз."),
        ("Failed to establish a new connection", "Не удалось подключиться к серверу."),
        ("Name or service not known", "Не удалось определить адрес сервера."),
        ("Max retries exceeded", "Сервер временно недоступен. Попробуйте позже."),
    )

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("SPEECHGYM_API_URL", "http://localhost:8080/api/v1")).rstrip("/")
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user: Optional[dict[str, Any]] = None

    def has_auth(self) -> bool:
        return bool(self.access_token)

    def clear_auth(self) -> None:
        self.access_token = None
        self.refresh_token = None
        self.user = None

    def register(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        data = self._request(
            "POST",
            "/auth/register",
            auth=False,
            json={"email": email, "password": password, "fullName": full_name},
        )
        self._store_auth(data)
        return data

    def login(self, email: str, password: str) -> dict[str, Any]:
        data = self._request(
            "POST",
            "/auth/login",
            auth=False,
            json={"email": email, "password": password},
        )
        self._store_auth(data)
        return data

    def refresh(self) -> dict[str, Any]:
        if not self.refresh_token:
            raise ApiError("Отсутствует refresh-токен.")
        data = self._request(
            "POST",
            "/auth/refresh",
            auth=False,
            json={"refreshToken": self.refresh_token},
        )
        self._store_auth(data)
        return data

    def me(self) -> dict[str, Any]:
        self.user = self._request("GET", "/me")
        return self.user

    def list_sessions(self, page: int = 0, size: int = 20, query: Optional[str] = None) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "size": size}
        if query:
            params["query"] = query
        return self._request("GET", "/sessions", params=params)

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/sessions",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json=payload,
        )

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/sessions/{session_id}")

    def update_session(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/sessions/{session_id}", json=payload)

    def list_uploads(self, session_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/sessions/{session_id}/uploads")

    def list_jobs(self, session_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/sessions/{session_id}/jobs")

    def list_reports(self, session_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/sessions/{session_id}/reports")

    def upload_audio(self, session_id: str, file_path: str) -> dict[str, Any]:
        path = Path(file_path)
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as file_obj:
            return self._request(
                "POST",
                f"/sessions/{session_id}/uploads",
                files={"file": (path.name, file_obj, content_type)},
                timeout=300,
            )

    def create_job(self, session_id: str, upload_id: str, options: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/sessions/{session_id}/jobs",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json={"uploadId": upload_id, "options": options or {"reportFormat": "FULL"}},
        )

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/jobs/{job_id}")

    def get_report(self, report_id: str) -> dict[str, Any]:
        return self._request("GET", f"/reports/{report_id}")

    def download_pdf(self, report_id: str) -> bytes:
        data = self._request("GET", f"/reports/{report_id}/pdf", expect_json=False, timeout=120)
        if not isinstance(data, bytes):
            raise ApiError("Сервер вернул неожиданный ответ при скачивании PDF.")
        return data

    def _store_auth(self, data: dict[str, Any]) -> None:
        self.access_token = data.get("accessToken")
        self.refresh_token = data.get("refreshToken")
        self.user = {
            "userId": data.get("userId"),
            "email": data.get("email"),
            "fullName": data.get("fullName"),
            "role": data.get("role"),
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        expect_json: bool = True,
        timeout: int = 30,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Any:
        request_headers = dict(headers or {})
        if auth:
            if not self.access_token:
                raise ApiError("Сначала войдите в аккаунт.")
            request_headers["Authorization"] = f"Bearer {self.access_token}"

        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=request_headers,
            timeout=timeout,
            **kwargs,
        )
        if response.status_code == 401 and auth and self.refresh_token:
            self.refresh()
            request_headers["Authorization"] = f"Bearer {self.access_token}"
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                headers=request_headers,
                timeout=timeout,
                **kwargs,
            )

        if not response.ok:
            raise ApiError(self._error_message(response))

        if expect_json:
            if not response.content:
                return {}
            return response.json()
        return response.content

    def _error_message(self, response: requests.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return f"Сервер вернул HTTP {response.status_code}."

        field_errors = body.get("fieldErrors")
        if field_errors:
            first = field_errors[0]
            field_name = self._FIELD_LABELS.get(str(first.get("field") or "").strip(), "Поле")
            field_message = self._translate_backend_text(first.get("message")) or "Недопустимое значение."
            return f"{field_name}: {field_message}"

        detail = body.get("detail")
        if detail:
            return self._translate_backend_text(detail)

        title = body.get("title")
        if title:
            return self._translate_backend_text(title)

        return f"Сервер вернул HTTP {response.status_code}."

    @classmethod
    def _translate_backend_text(cls, text: Any) -> str:
        message = str(text or "").strip()
        if not message:
            return ""
        if message in cls._ERROR_TRANSLATIONS:
            return cls._ERROR_TRANSLATIONS[message]
        for needle, translation in cls._ERROR_SUBSTRINGS:
            if needle.lower() in message.lower():
                return translation
        return message


class ApiWorker(QThread):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn: Callable[[], Any], parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            self.succeeded.emit(self._fn())
        except Exception as exception:
            self.failed.emit(str(exception))


api = ApiClient()
