def build_overwrite_question(chapter_path: str) -> dict:
    return {
        "decision_type": "overwrite_write",
        "question": f"Chapter file already exists: {chapter_path}",
        "options": [
            {
                "label": "overwrite",
                "description": "Replace the existing chapter file with the new draft.",
            },
            {
                "label": "abort",
                "description": "Stop the write flow and keep the existing chapter file.",
            },
        ],
    }


def build_semantic_question(trigger: dict) -> dict:
    trigger_code = str(trigger.get("trigger_code", "")).strip()
    if trigger_code == "review_severe_issue":
        return _build_review_severe_question(trigger)
    if trigger_code == "setting_conflict":
        return _build_setting_conflict_question(trigger)
    if trigger_code == "route_branch":
        return _build_route_branch_question(trigger)
    raise ValueError(f"Unsupported semantic trigger code: {trigger_code}")


def _build_review_severe_question(trigger: dict) -> dict:
    payload = trigger.get("payload", {}) if isinstance(trigger.get("payload"), dict) else {}
    checker = str(payload.get("checker", "unknown")).strip()
    issues = payload.get("issues", [])
    issue_text = "; ".join(str(item).strip() for item in issues if str(item).strip())[:300]
    return {
        "decision_type": "review_severe_issue",
        "question": (
            f"Review reported a severe issue in `{checker}`."
            f"{' Details: ' + issue_text if issue_text else ''}"
        ),
        "options": [
            {
                "label": "revise_now",
                "description": "Apply revision before continuing write flow.",
            },
            {
                "label": "continue_with_warning",
                "description": "Continue current flow and keep warning in report.",
            },
            {
                "label": "defer",
                "description": "Defer this decision and mark it for later review.",
            },
        ],
    }


def _build_setting_conflict_question(trigger: dict) -> dict:
    payload = trigger.get("payload", {}) if isinstance(trigger.get("payload"), dict) else {}
    score = payload.get("score")
    issues = payload.get("issues", [])
    issue_text = "; ".join(str(item).strip() for item in issues if str(item).strip())[:300]
    return {
        "decision_type": "setting_conflict",
        "question": (
            "Consistency checker detected a possible setting conflict."
            f"{' Score: ' + str(score) if score is not None else ''}"
            f"{' Details: ' + issue_text if issue_text else ''}"
        ),
        "options": [
            {
                "label": "prefer_consistency",
                "description": "Preserve established setting and revise current draft.",
            },
            {
                "label": "prefer_current_draft",
                "description": "Keep current draft direction and allow setting update later.",
            },
            {
                "label": "defer",
                "description": "Defer this decision and mark it for later review.",
            },
        ],
    }


def _build_route_branch_question(trigger: dict) -> dict:
    payload = trigger.get("payload", {}) if isinstance(trigger.get("payload"), dict) else {}
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
    text_candidates = [str(item).strip() for item in candidates if str(item).strip()]
    primary = text_candidates[0] if len(text_candidates) >= 1 else "Primary branch candidate"
    secondary = text_candidates[1] if len(text_candidates) >= 2 else "Secondary branch candidate"
    return {
        "decision_type": "route_branch",
        "question": "Writing context suggests route branching. Choose the preferred route.",
        "options": [
            {
                "label": "branch_primary",
                "description": f"Prefer route: {primary}",
            },
            {
                "label": "branch_secondary",
                "description": f"Prefer route: {secondary}",
            },
            {
                "label": "defer",
                "description": "Defer route choice and keep both branches open for now.",
            },
        ],
    }
