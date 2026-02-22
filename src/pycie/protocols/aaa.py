"""Lab 32: AAA authentication and authorization model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class BackendStatus(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"


@dataclass(frozen=True)
class BackendResponse:
    status: "BackendStatus | str"
    role: str | None = None


class BackendUnavailable(RuntimeError):
    """Raised when a remote AAA backend cannot be reached."""


class AAABackend(Protocol):
    def authenticate(self, username: str, password: str) -> BackendResponse:
        """Validate credentials against backend store."""


@dataclass(frozen=True)
class AAAUser:
    username: str
    password: str
    role: str


@dataclass(frozen=True)
class AccountingRecord:
    event: str
    username: str
    detail: str
    timestamp_ms: float


@dataclass
class AAAService:
    """AAA service with backend-first and local fallback behavior."""

    local_users: dict[str, AAAUser] = field(default_factory=dict)
    backend: AAABackend | None = None
    fallback_to_local: bool = True
    command_roles: dict[str, set[str]] = field(default_factory=dict)
    sessions: dict[str, str] = field(default_factory=dict)
    accounting: list[AccountingRecord] = field(default_factory=list)

    def add_local_user(self, user: AAAUser) -> None:
        self.local_users[user.username] = user

    def login(self, username: str, password: str, *, now_ms: float = 0.0) -> bool:
        """Authenticate user and create session role binding."""
        backend_decision = self._authenticate_backend(username, password)
        if backend_decision is not None:
            accepted, role = backend_decision
            if accepted:
                self.sessions[username] = role
                self._record("login_success", username, "backend", now_ms)
                return True
            self._record("login_denied", username, "backend_reject", now_ms)
            return False

        user = self.local_users.get(username)
        if user is None or user.password != password:
            self._record("login_denied", username, "local_reject", now_ms)
            return False

        self.sessions[username] = user.role
        self._record("login_success", username, "local", now_ms)
        return True

    def authorize(self, username: str, command: str, *, now_ms: float = 0.0) -> bool:
        """Authorize command based on session role and command policy."""
        role = self.sessions.get(username)
        if role is None:
            self._record("authorize_denied", username, "no_session", now_ms)
            return False

        allowed = self.command_roles.get(command)
        if allowed is None:
            self._record("authorize_success", username, f"implicit:{command}", now_ms)
            return True

        decision = role in allowed
        if decision:
            self._record("authorize_success", username, f"role:{role}", now_ms)
        else:
            self._record("authorize_denied", username, f"role:{role}", now_ms)
        return decision

    def logout(self, username: str, *, now_ms: float = 0.0) -> None:
        self.sessions.pop(username, None)
        self._record("logout", username, "session_removed", now_ms)

    def _authenticate_backend(self, username: str, password: str) -> tuple[bool, str] | None:
        if self.backend is None:
            return None

        try:
            response = self.backend.authenticate(username, password)
        except BackendUnavailable:
            if self.fallback_to_local:
                return None
            return (False, "")

        status = BackendStatus(response.status)
        if status == BackendStatus.ACCEPT:
            role = response.role
            if role is None:
                local = self.local_users.get(username)
                role = local.role if local is not None else "user"
            return (True, role)
        return (False, "")

    def _record(self, event: str, username: str, detail: str, timestamp_ms: float) -> None:
        self.accounting.append(
            AccountingRecord(
                event=event,
                username=username,
                detail=detail,
                timestamp_ms=timestamp_ms,
            )
        )
