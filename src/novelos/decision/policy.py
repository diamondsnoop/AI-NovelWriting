from __future__ import annotations


SUPPORTED_DECISION_MODES = {"defer", "auto_recommended", "abort"}


def normalize_decision_mode(mode: str | None) -> str:
    resolved = (mode or "defer").strip().lower()
    if resolved not in SUPPORTED_DECISION_MODES:
        raise ValueError(f"Unsupported decision mode: {mode}")
    return resolved


def select_option(question: dict, mode: str) -> str:
    options = question.get("options", [])
    labels = [str(item.get("label", "")).strip() for item in options if str(item.get("label", "")).strip()]
    if not labels:
        raise ValueError("Decision question does not contain valid options.")

    if mode == "auto_recommended":
        return labels[0]
    if mode == "abort":
        for label in labels:
            if "abort" in label:
                return label
        for label in labels:
            if "defer" in label:
                return label
        return labels[0]

    # defer
    for label in labels:
        if "defer" in label:
            return label
    return labels[0]
