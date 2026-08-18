"""Tests cho `src/services/auto_remediation.py` — auto-fix khi HITL timeout.

Không gọi mạng, không cần key: dùng `FakeJiraClient` và monkeypatch config.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from src.models.incident import IncidentState, RemediationProposal, Severity
from src.services.auto_remediation import (
    AUTO_APPROVED_BY,
    AUTO_MARKER,
    AutoRemediationPolicy,
    execute_auto_remediation,
    should_auto_remediate,
)
from src.services.jira import FakeJiraClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_incident(
    jira: FakeJiraClient,
    severity: Severity = Severity.P3,
    action: str = "restart",
    target: str = "service-thanh-toan",
    awaiting_minutes_ago: int = 40,
) -> str:
    """Tạo một incident đã đề xuất và đang chờ duyệt."""
    from src.models.incident import IncidentSignal

    signal = IncidentSignal(
        metric_name="http_request_duration_seconds p95",
        metric_value=5.0,
        threshold=2.0,
        affected_service=target,
        severity=severity,
        breached_for_seconds=120,
        detected_at=datetime.now(UTC),
    )
    jira_key = jira.create_incident(signal)

    proposal = RemediationProposal(
        action=action,
        target=target,
        params={"to_version": "v1.4.1"} if action == "rollback" else {},
        risk="rủi ro test",
    )
    jira.post_proposal(jira_key, proposal)

    # Giả lập thời điểm chuyển sang Awaiting Approval — lùi về quá khứ.
    luc_chuyen = datetime.now(UTC) - timedelta(minutes=awaiting_minutes_ago)
    jira._transition_times[(jira_key, IncidentState.AWAITING_APPROVAL)] = luc_chuyen

    return jira_key


def _policy_bat(**overrides):
    """Patch config settings để bật auto-remediation."""
    defaults = {
        "auto_remediation_enabled": True,
        "auto_remediation_timeout_minutes": 30,
    }
    defaults.update(overrides)

    class FakeSettings:
        def __getattr__(self, name):
            return defaults.get(name, "")

    return patch(
        "src.services.auto_remediation.get_settings",
        return_value=FakeSettings(),
    )


def _policy_tat():
    """Patch config settings để tắt auto-remediation."""
    return _policy_bat(auto_remediation_enabled=False)


# ---------------------------------------------------------------------------
# Tests: should_auto_remediate()
# ---------------------------------------------------------------------------


class TestShouldAutoRemediate:
    """Quyết định có nên auto-fix không."""

    def test_khong_tu_sua_khi_tat(self):
        """Feature tắt → trả None."""
        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(jira, awaiting_minutes_ago=60)

        with _policy_tat():
            result = should_auto_remediate(
                jira, jira_key,
                severity=Severity.P3,
                proposal_action="restart",
                proposal_target="service-thanh-toan",
            )
        assert result is None

    def test_khong_tu_sua_khi_chua_du_30_phut(self):
        """Mới chờ 10 phút → chưa timeout."""
        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(jira, awaiting_minutes_ago=10)

        with _policy_bat():
            result = should_auto_remediate(
                jira, jira_key,
                severity=Severity.P3,
                proposal_action="restart",
                proposal_target="service-thanh-toan",
            )
        assert result is None

    def test_tu_sua_p3_dung_de_xuat(self):
        """P3 + 40 phút → dùng action đã đề xuất (restart)."""
        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(
            jira, severity=Severity.P3, action="restart",
            awaiting_minutes_ago=40,
        )

        with _policy_bat():
            result = should_auto_remediate(
                jira, jira_key,
                severity=Severity.P3,
                proposal_action="restart",
                proposal_target="service-thanh-toan",
            )
        assert result is not None
        assert result.action == "restart"
        assert result.forced_rollback is False

    def test_tu_sua_p4_dung_de_xuat(self):
        """P4 + 35 phút → dùng action đã đề xuất."""
        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(
            jira, severity=Severity.P4, action="increase_pool",
            awaiting_minutes_ago=35,
        )

        with _policy_bat():
            result = should_auto_remediate(
                jira, jira_key,
                severity=Severity.P4,
                proposal_action="increase_pool",
                proposal_target="service-thanh-toan",
            )
        assert result is not None
        assert result.action == "increase_pool"
        assert result.forced_rollback is False

    def test_tu_rollback_p1(self):
        """P1 + 40 phút → ép rollback bất kể đề xuất ban đầu."""
        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(
            jira, severity=Severity.P1, action="scale_up",
            awaiting_minutes_ago=40,
        )

        with _policy_bat():
            result = should_auto_remediate(
                jira, jira_key,
                severity=Severity.P1,
                proposal_action="scale_up",
                proposal_target="service-thanh-toan",
            )
        assert result is not None
        assert result.action == "rollback"
        assert result.forced_rollback is True

    def test_tu_rollback_p2(self):
        """P2 + 45 phút → ép rollback."""
        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(
            jira, severity=Severity.P2, action="restart",
            awaiting_minutes_ago=45,
        )

        with _policy_bat():
            result = should_auto_remediate(
                jira, jira_key,
                severity=Severity.P2,
                proposal_action="restart",
                proposal_target="service-thanh-toan",
            )
        assert result is not None
        assert result.action == "rollback"
        assert result.forced_rollback is True

    def test_khong_tu_sua_khi_da_co_nguoi_phan_hoi(self):
        """Issue đã được chuyển sang Remediating bởi human → không auto."""
        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(jira, awaiting_minutes_ago=60)
        # Mô phỏng human đã duyệt
        jira.approve_as_human(jira_key)

        with _policy_bat():
            result = should_auto_remediate(
                jira, jira_key,
                severity=Severity.P3,
                proposal_action="restart",
                proposal_target="service-thanh-toan",
            )
        assert result is None

    def test_timeout_tuy_chinh(self):
        """Timeout 60 phút → 40 phút chưa đủ, 65 phút đủ."""
        jira = FakeJiraClient(verbose=False)
        key_40 = _setup_incident(jira, awaiting_minutes_ago=40)
        key_65 = _setup_incident(jira, awaiting_minutes_ago=65)

        with _policy_bat(auto_remediation_timeout_minutes=60):
            result_40 = should_auto_remediate(
                jira, key_40,
                severity=Severity.P3,
                proposal_action="restart",
                proposal_target="service-thanh-toan",
            )
            result_65 = should_auto_remediate(
                jira, key_65,
                severity=Severity.P3,
                proposal_action="restart",
                proposal_target="service-thanh-toan",
            )
        assert result_40 is None
        assert result_65 is not None


# ---------------------------------------------------------------------------
# Tests: execute_auto_remediation()
# ---------------------------------------------------------------------------


class TestExecuteAutoRemediation:
    """Thi hành auto-fix và ghi comment."""

    def test_comment_ghi_ro_ly_do(self):
        """Comment trên Jira phải chứa marker AUTO_MARKER."""
        from src.services.auto_remediation import AutoRemediationDecision

        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(jira)

        decision = AutoRemediationDecision(
            jira_key=jira_key,
            action="restart",
            target="service-thanh-toan",
            params={},
            reason="Sự cố P3 đã chờ 40 phút mà không có phản hồi.",
            forced_rollback=False,
        )

        result = execute_auto_remediation(jira, decision)

        assert result.succeeded is True
        # Kiểm tra comment có marker
        comments = jira.get_comment_bodies(jira_key)
        assert any(AUTO_MARKER in c for c in comments), (
            f"Comment phải chứa '{AUTO_MARKER}'. Các comment: {comments}"
        )

    def test_approved_by_la_auto_timeout(self):
        """approved_by phải là AUTO_APPROVED_BY, không phải human."""
        from src.services.auto_remediation import AutoRemediationDecision

        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(jira)

        decision = AutoRemediationDecision(
            jira_key=jira_key,
            action="restart",
            target="service-thanh-toan",
            params={},
            reason="test",
            forced_rollback=False,
        )

        result = execute_auto_remediation(jira, decision)

        assert result.approved_by == AUTO_APPROVED_BY
        assert result.approved_by != FakeJiraClient.HUMAN_ACCOUNT_ID

    def test_chuyen_sang_remediating(self):
        """Sau auto-fix, issue phải ở trạng thái Remediating."""
        from src.services.auto_remediation import AutoRemediationDecision

        jira = FakeJiraClient(verbose=False)
        jira_key = _setup_incident(jira)

        decision = AutoRemediationDecision(
            jira_key=jira_key,
            action="restart",
            target="service-thanh-toan",
            params={},
            reason="test",
            forced_rollback=False,
        )

        execute_auto_remediation(jira, decision)

        incident = jira.get_incident(jira_key)
        assert incident is not None
        assert incident.state == IncidentState.REMEDIATING


# ---------------------------------------------------------------------------
# Tests: AutoRemediationPolicy
# ---------------------------------------------------------------------------


class TestPolicy:
    """Đọc config đúng."""

    def test_mac_dinh_tat(self):
        """Mặc định feature tắt."""
        with _policy_tat():
            policy = AutoRemediationPolicy.from_settings()
        assert policy.enabled is False

    def test_bat_va_doc_timeout(self):
        """Bật feature và đọc đúng timeout."""
        with _policy_bat(auto_remediation_timeout_minutes=45):
            policy = AutoRemediationPolicy.from_settings()
        assert policy.enabled is True
        assert policy.timeout_minutes == 45
