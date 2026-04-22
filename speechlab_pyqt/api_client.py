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
            raise ApiError("Refresh token is missing.")
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
            raise ApiError("Unexpected PDF response.")
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
                raise ApiError("You need to sign in first.")
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
            return f"Backend returned HTTP {response.status_code}."

        field_errors = body.get("fieldErrors")
        if field_errors:
            first = field_errors[0]
            return f"{first.get('field', 'Field')}: {first.get('message', 'Invalid value.')}"

        detail = body.get("detail")
        if detail:
            return str(detail)

        title = body.get("title")
        if title:
            return str(title)

        return f"Backend returned HTTP {response.status_code}."


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
