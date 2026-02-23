"""Edge-case tests for Lab 32 AAA access control."""

from __future__ import annotations

import pytest

from pycie.protocols.aaa import AAAService, AAAUser, BackendResponse, BackendStatus

pytestmark = [pytest.mark.exercise, pytest.mark.lab32]


class AcceptNoRoleBackend:
    def authenticate(self, username: str, password: str) -> BackendResponse:
        if password == "ok":
            return BackendResponse(status=BackendStatus.ACCEPT, role=None)
        return BackendResponse(status=BackendStatus.REJECT)


def test_backend_accept_without_role_falls_back_to_local_role() -> None:
    aaa = AAAService(backend=AcceptNoRoleBackend())
    aaa.add_local_user(AAAUser("alice", "ok", "operator"))

    assert aaa.login("alice", "ok", now_ms=10)
    assert aaa.sessions["alice"] == "operator"


def test_backend_accept_without_role_uses_default_role_when_user_missing_locally() -> None:
    aaa = AAAService(backend=AcceptNoRoleBackend())

    assert aaa.login("remote-user", "ok", now_ms=20)
    assert aaa.sessions["remote-user"] == "user"

