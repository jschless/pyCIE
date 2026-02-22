"""Exercise tests for Lab 32 AAA access control."""

from __future__ import annotations

import pytest

from pycie.protocols.aaa import (
    AAAService,
    AAAUser,
    BackendResponse,
    BackendStatus,
    BackendUnavailable,
)

pytestmark = [pytest.mark.exercise, pytest.mark.lab32]


class AcceptBackend:
    def authenticate(self, username: str, password: str) -> BackendResponse:
        if username == "alice" and password == "ok":
            return BackendResponse(status=BackendStatus.ACCEPT, role="netadmin")
        return BackendResponse(status=BackendStatus.REJECT)


class FlakyBackend:
    def authenticate(self, username: str, password: str) -> BackendResponse:
        raise BackendUnavailable("down")


def test_local_login_success_and_session_role() -> None:
    aaa = AAAService()
    aaa.add_local_user(AAAUser("alice", "pw", "operator"))

    assert aaa.login("alice", "pw", now_ms=1)
    assert aaa.sessions["alice"] == "operator"


def test_backend_accept_takes_precedence_over_local_role() -> None:
    aaa = AAAService(backend=AcceptBackend())
    aaa.add_local_user(AAAUser("alice", "ok", "viewer"))

    assert aaa.login("alice", "ok", now_ms=5)
    assert aaa.sessions["alice"] == "netadmin"


def test_backend_reject_denies_when_backend_reachable() -> None:
    aaa = AAAService(backend=AcceptBackend())
    aaa.add_local_user(AAAUser("alice", "bad", "viewer"))

    assert not aaa.login("alice", "bad", now_ms=10)


def test_backend_unavailable_falls_back_to_local_if_enabled() -> None:
    aaa = AAAService(backend=FlakyBackend(), fallback_to_local=True)
    aaa.add_local_user(AAAUser("bob", "pw", "operator"))

    assert aaa.login("bob", "pw", now_ms=15)
    assert aaa.sessions["bob"] == "operator"


def test_backend_unavailable_denies_if_fallback_disabled() -> None:
    aaa = AAAService(backend=FlakyBackend(), fallback_to_local=False)
    aaa.add_local_user(AAAUser("bob", "pw", "operator"))

    assert not aaa.login("bob", "pw", now_ms=20)


def test_authorize_denies_without_session() -> None:
    aaa = AAAService()
    aaa.command_roles = {"show run": {"operator"}}

    assert not aaa.authorize("alice", "show run", now_ms=30)


def test_authorize_enforces_command_role_map() -> None:
    aaa = AAAService()
    aaa.add_local_user(AAAUser("alice", "pw", "operator"))
    aaa.add_local_user(AAAUser("root", "pw", "netadmin"))
    aaa.command_roles = {
        "show run": {"operator", "netadmin"},
        "conf t": {"netadmin"},
    }

    assert aaa.login("alice", "pw", now_ms=40)
    assert aaa.login("root", "pw", now_ms=41)
    assert aaa.authorize("alice", "show run", now_ms=42)
    assert not aaa.authorize("alice", "conf t", now_ms=43)
    assert aaa.authorize("root", "conf t", now_ms=44)


def test_accounting_records_track_login_authorize_logout() -> None:
    aaa = AAAService()
    aaa.add_local_user(AAAUser("alice", "pw", "operator"))
    aaa.command_roles = {"show ip int brief": {"operator"}}

    assert aaa.login("alice", "pw", now_ms=100)
    assert aaa.authorize("alice", "show ip int brief", now_ms=101)
    aaa.logout("alice", now_ms=102)

    events = [record.event for record in aaa.accounting]
    assert events == ["login_success", "authorize_success", "logout"]
