"""Auto-remediation khi timeout — Agent tự sửa nếu không ai phản hồi.

CHỦ SỞ HỮU: Việt

## Vì sao có module này

Sự cố xảy ra vào đêm, không ai trực → issue nằm ở `Awaiting Approval` mãi mà
không được duyệt. 30 phút trôi qua mà hệ thống không cải thiện và không có phản
hồi từ người → Agent tự thi hành.

## MỐI QUAN HỆ VỚI HITL

Module này **CỐ Ý bypass** cổng HITL (`hitl.assert_human_approved()`). Đây là
**ngoại lệ có điều kiện**, KHÔNG phải xoá bỏ HITL:

- HITL vẫn là đường đi chính (webhook + poll_jira_approvals)
- Module này chỉ can thiệp khi HITL đã **hết thời gian chờ** (mặc định 30 phút)
- Mặc định **TẮT** — phải bật `AUTO_REMEDIATION_ENABLED=1` trong `.env`
- Comment trên Jira ghi rõ "tự thi hành do hết thời chờ", phân biệt với human

## Nguyên tắc cách ly

- KHÔNG import `hitl.py`
- KHÔNG sửa `remediation.py`, `executors.py`, `incident_graph.py`, `webhooks.py`
- Gọi `remediation.execute()` y hệt webhook, chỉ khác `approved_by`
- Tích hợp vào `run_agent.py` bằng 1 hàm gọi trong loop

## Chính sách theo mức độ

| Mức   | Hành vi khi timeout                                  |
|-------|------------------------------------------------------|
| P3/P4 | Thi hành **đúng hành động đã đề xuất** (đề xuất gốc)|
| P1/P2 | Ép **rollback** bất kể đề xuất ban đầu là gì        |
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.config import get_settings
from src.models.incident import IncidentState, Severity
from src.services import deploys
from src.services.remediation import RemediationResult, execute

logger = logging.getLogger(__name__)

#: Giá trị `approved_by` khi Agent tự duyệt do timeout. Dùng chuỗi cố định để
#: phân biệt rõ với human accountId (dạng `712020:xxxx`) trong mọi audit trail.
AUTO_APPROVED_BY = "AUTO_TIMEOUT_AGENT"

#: Comment marker — tương tự `REMEDIATION_MARKER` trong `remediation.py` nhưng
#: khác chữ, để phân biệt auto-fix với human-approved fix khi đọc Jira.
AUTO_MARKER = "Tự thi hành do hết thời chờ"


@dataclass(frozen=True)
class AutoRemediationPolicy:
    """Chính sách auto-fix khi timeout, đọc từ `.env`."""

    enabled: bool
    timeout_minutes: int

    @staticmethod
    def from_settings() -> AutoRemediationPolicy:
        """Đọc cấu hình từ `Settings`. Gọi mỗi lần kiểm để env thay đổi được."""
        settings = get_settings()
        return AutoRemediationPolicy(
            enabled=settings.auto_remediation_enabled,
            timeout_minutes=settings.auto_remediation_timeout_minutes,
        )


@dataclass(frozen=True)
class AutoRemediationDecision:
    """Quyết định auto-fix cho một issue cụ thể."""

    jira_key: str
    action: str
    target: str
    params: dict
    reason: str
    #: `True` nếu hành động bị ép rollback (P1/P2), khác với đề xuất gốc.
    forced_rollback: bool


def _is_human_responded(
    jira,  # JiraClient
    jira_key: str,
) -> bool:
    """Kiểm tra xem đã có phản hồi từ human chưa.

    "Phản hồi" = issue đã được chuyển sang `Remediating` bởi bất kỳ ai (bao gồm
    cả webhook). Nếu đã có → HITL đã xử lý, không cần auto-fix.
    """
    try:
        author = jira.get_transition_author(jira_key, IncidentState.REMEDIATING)
        return author is not None
    except Exception:
        # Lỗi đọc Jira: an toàn hơn là coi như đã có phản hồi → không auto-fix.
        return True


def should_auto_remediate(
    jira,  # JiraClient
    jira_key: str,
    severity: Severity,
    proposal_action: str,
    proposal_target: str,
    proposal_params: dict | None = None,
    deploy_service: str | None = None,
) -> AutoRemediationDecision | None:
    """Quyết định có nên auto-fix issue này không.

    Returns:
        `AutoRemediationDecision` nếu nên auto-fix.
        `None` nếu KHÔNG nên (feature tắt, chưa đủ thời gian, đã có human, ...).
    """
    policy = AutoRemediationPolicy.from_settings()
    if not policy.enabled:
        return None

    # Đã có human phản hồi → HITL đã xử lý, không cần auto.
    if _is_human_responded(jira, jira_key):
        return None

    # Đọc thời điểm chuyển sang Awaiting Approval — mốc bắt đầu đếm timeout.
    try:
        awaiting_since = jira.get_transition_time(
            jira_key, IncidentState.AWAITING_APPROVAL
        )
    except Exception:
        return None

    if awaiting_since is None:
        return None

    now = datetime.now(UTC)
    elapsed = now - awaiting_since
    timeout = timedelta(minutes=policy.timeout_minutes)

    if elapsed < timeout:
        return None

    elapsed_minutes = int(elapsed.total_seconds() / 60)

    # Quyết định hành động theo mức độ.
    if severity in (Severity.P1, Severity.P2):
        # P1/P2: ép rollback bất kể đề xuất ban đầu.
        service = deploy_service or proposal_target
        history = deploys.recent_deploys(service)
        if history:
            to_version = history[0].get("version", "phiên bản trước")
        else:
            to_version = "phiên bản trước"

        return AutoRemediationDecision(
            jira_key=jira_key,
            action="rollback",
            target=proposal_target,
            params={"to_version": to_version},
            reason=(
                f"Sự cố {severity.value} đã chờ {elapsed_minutes} phút "
                f"mà không có phản hồi. Tự rollback về {to_version}."
            ),
            forced_rollback=True,
        )
    else:
        # P3/P4: dùng đúng hành động đã đề xuất.
        return AutoRemediationDecision(
            jira_key=jira_key,
            action=proposal_action,
            target=proposal_target,
            params=proposal_params or {},
            reason=(
                f"Sự cố {severity.value} đã chờ {elapsed_minutes} phút "
                f"mà không có phản hồi. Tự thi hành: {proposal_action} → {proposal_target}."
            ),
            forced_rollback=False,
        )


def execute_auto_remediation(
    jira,  # JiraClient
    decision: AutoRemediationDecision,
) -> RemediationResult:
    """Thi hành auto-fix và post comment lên Jira.

    Gọi `remediation.execute()` với `approved_by=AUTO_APPROVED_BY`.
    Comment lên Jira ghi rõ lý do tự thi hành.

    KHÔNG gọi `hitl.assert_human_approved()` — đây là bypass có chủ đích.
    """
    logger.warning(
        "AUTO-REMEDIATION: %s — %s → %s (lý do: %s)",
        decision.jira_key,
        decision.action,
        decision.target,
        decision.reason,
    )

    result = execute(
        decision.action,
        decision.target,
        approved_by=AUTO_APPROVED_BY,
        params=decision.params,
    )

    # Post comment lên Jira — phân biệt rõ với human-approved.
    comment = (
        f"⚠️ **{AUTO_MARKER}**\n\n"
        f"{decision.reason}\n\n"
        f"---\n\n"
        f"{result.as_comment()}\n\n"
        f"---\n\n"
        f"🔒 Hành vi này mặc định **TẮT**. Bật bằng `AUTO_REMEDIATION_ENABLED=1` "
        f"trong `.env`. Để tắt lại, xoá biến hoặc đặt về `0`."
    )
    try:
        jira.add_comment(decision.jira_key, comment)
    except Exception as error:
        logger.warning(
            "%s: không post được comment auto-remediation (%s)",
            decision.jira_key,
            error,
        )

    # Chuyển issue sang Remediating — giống webhook.
    try:
        jira.transition(decision.jira_key, IncidentState.REMEDIATING)
    except Exception as error:
        logger.warning(
            "%s: không chuyển được sang Remediating sau auto-fix (%s)",
            decision.jira_key,
            error,
        )

    return result
