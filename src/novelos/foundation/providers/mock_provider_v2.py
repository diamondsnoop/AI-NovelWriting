import json

from novelos.foundation.providers.base_provider import BaseProvider, ProviderRequest, ProviderResponse


class MockProvider(BaseProvider):
    provider_name = "mock"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        chapter = request.context.get("chapter_no", "unknown")
        title = request.context.get("project_title", "Untitled Project")

        if request.task_type == "plan_chapter":
            text = (
                f"# Chapter {chapter} Outline\n\n"
                f"- Project: {title}\n"
                f"- Purpose: establish the chapter's visible objective and pressure\n"
                f"- Goal: move the current main plot forward\n"
                f"- Beat 1: open with a concrete disruption or pressure point\n"
                f"- Beat 2: force the protagonist into a choice under pressure\n"
                f"- Event: the protagonist accepts a new task and meets fresh resistance\n"
                f"- Ending: leave a hook for the next chapter\n"
            )
        elif request.task_type == "plan_chapter_compact":
            next_chapter = int(chapter) + 1 if str(chapter).isdigit() else chapter
            text = (
                f"# Chapter {chapter} Compact Outline\n\n"
                f"Goal: move the current main plot forward.\n"
                f"Beat 1: open with immediate pressure on the protagonist.\n"
                f"Beat 2: reveal a new obstacle tied to the main task.\n"
                f"Beat 3: force a concrete choice with visible cost.\n"
                f"Hook: end on a lead or consequence that pushes chapter {next_chapter}.\n"
            )
        elif request.task_type == "plan_volume":
            volume_no = request.context.get("volume_no", 1)
            text = (
                f"# Volume {volume_no} Plan\n\n"
                f"- Objective: sustain escalation while advancing the core conflict.\n"
                f"- Core conflict: the protagonist must solve the visible threat without exposing hidden weaknesses.\n"
                f"- Midpoint shift: a trusted clue changes meaning and raises narrative stakes.\n"
                f"- Expected climax: choice under irreversible cost and clear setup for the next volume.\n"
            )
        elif request.task_type == "plan_chapter_beats":
            next_chapter = int(chapter) + 1 if str(chapter).isdigit() else chapter
            text = (
                f"# Chapter {chapter} Beat Sheet\n\n"
                f"1. Opening pressure: external event disrupts current plan.\n"
                f"2. Decision under pressure: protagonist picks a risky path.\n"
                f"3. Escalation: resistance becomes concrete and personal.\n"
                f"4. Micro-payoff: small win with hidden cost.\n"
                f"5. Hook: unresolved lead pushes chapter {next_chapter}.\n"
            )
        elif request.task_type == "plan_chapter_timeline":
            text = (
                f"# Chapter {chapter} Timeline\n\n"
                f"- T0: inciting pressure appears in public view.\n"
                f"- T1: protagonist confirms mission target and constraints.\n"
                f"- T2: first clash reveals hidden opposition.\n"
                f"- T3: temporary resolution with a new unresolved thread.\n"
            )
        elif request.task_type == "summarize_chapter":
            text = (
                f"# Chapter {chapter} Summary\n\n"
                f"{title} chapter {chapter}: the protagonist advances the current objective and leaves a new direction for the next chapter."
            )
        elif request.task_type == "review_continuity":
            previous_summary = request.context.get("previous_summary", "")
            draft_text = request.context.get("draft_text", "")
            score = 0.85 if previous_summary and draft_text else 0.0
            text = json.dumps(
                {
                    "score": score,
                    "issues": [] if score >= 0.5 else ["Draft does not connect to the previous summary."],
                    "rationale": "Draft continues naturally from the previous summary." if score >= 0.5 else "Continuity is weak.",
                }
            )
        elif request.task_type == "review_consistency":
            known_entities = request.context.get("known_entities", [])
            draft_text = request.context.get("draft_text", "")
            score = 0.8 if known_entities and draft_text else 0.0
            text = json.dumps(
                {
                    "score": score,
                    "issues": [] if score >= 0.5 else ["Draft conflicts with known entity records."],
                    "rationale": "No obvious contradiction with known entity records." if score >= 0.5 else "Entity consistency is weak.",
                }
            )
        elif request.task_type == "review_character":
            profiles = request.context.get("known_character_profiles", [])
            draft_text = request.context.get("draft_text", "")
            score = 0.82 if profiles and draft_text else 0.0
            text = json.dumps(
                {
                    "score": score,
                    "issues": [] if score >= 0.5 else ["Character behavior deviates from known profile."],
                    "rationale": "No obvious character drift from known profiles." if score >= 0.5 else "Character behavior appears off-profile.",
                }
            )
        elif request.task_type == "extract_entities":
            text = json.dumps(
                {
                    "characters": ["Lin He", "Su Wan"],
                    "locations": ["Black Pine Town"],
                },
                ensure_ascii=False,
            )
        elif request.task_type == "extract_foreshadowing":
            text = json.dumps(
                {
                    "foreshadowing": [
                        {
                            "setup": f"Chapter {chapter} introduces an unresolved clue.",
                            "hint": "The clue is treated as important but not yet explained.",
                            "expected_payoff": "Reveal the true meaning of the clue in a later chapter.",
                        }
                    ]
                },
                ensure_ascii=False,
            )
        elif request.task_type == "summarize_character_profile":
            character_name = request.context.get("character_name", "Unknown")
            text = f"{character_name} appears cautious, proactive, and willing to move the plot forward under pressure."
        elif request.task_type == "summarize_structured_chapter":
            chapter = request.context.get("chapter_no", 0)
            text = json.dumps(
                {
                    "key_events": [f"Chapter {chapter} advances the visible task."],
                    "main_plot_advanced": True,
                    "high_point_markers": [f"Chapter {chapter} contains a visible escalation beat."],
                    "reader_pull_marker": {
                        "has_pull": True,
                        "pull_type": "open_question",
                        "evidence": f"Chapter {chapter} ends with unresolved direction pressure.",
                    },
                }
            )
        else:
            outline = request.context.get("chapter_outline", "")
            beats = request.context.get("chapter_beats", "")
            timeline = request.context.get("chapter_timeline", "")
            volume_plan = request.context.get("volume_plan", "")
            previous_summary = request.context.get("previous_summary", "")
            retrieved_context = request.context.get("retrieved_context", [])
            text = (
                f"[{title}] Chapter {chapter} Draft\n\n"
                f"This is a skeleton draft generated by {self.provider_name}:{self.model_name}.\n"
                f"Task type: {request.task_type}.\n\n"
                f"Summary hint: {request.context.get('summary_hint', 'No summary hint.')}\n\n"
                f"Volume plan:\n{volume_plan or 'No volume plan.'}\n\n"
                f"Previous chapter summary:\n{previous_summary or 'No previous summary.'}\n\n"
                f"Retrieved context:\n{retrieved_context or 'No retrieved context.'}\n\n"
                f"Chapter beats:\n{beats or 'No beat sheet.'}\n\n"
                f"Chapter timeline:\n{timeline or 'No timeline.'}\n\n"
                f"Chapter outline:\n{outline or 'No outline.'}\n"
            )

        return ProviderResponse(
            text=text,
            provider=self.provider_name,
            model=self.model_name,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            latency_ms=0,
        )
