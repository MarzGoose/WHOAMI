import json
from datetime import datetime, timezone
from pathlib import Path
from signals.base import Signal
from pack.llm import LLMClient


PACK_PROMPT_TEMPLATE = """You are a forensic identity analyst. Below are {signal_count} signals extracted from {subject_name}'s personal data. These signals were detected automatically from their digital exhaust files — data generated without narrator curation.

Your task: produce a structured WHOAMI context pack. This is a portable identity document designed to give any AI immediate, calibrated understanding of this person — replacing the need for a lengthy intake interview.

SIGNALS:
{signals_text}

Produce the context pack in this format:

# WHOAMI Context Pack — {subject_name}
Generated: {date}
Signals: {signal_count} | Sources: {sources}

## Identity Signals

[For each signal, write a clear, forensic, non-judgmental statement of what the data shows. Present contradictions as open findings, not conclusions. Do not resolve or explain away conflicts.]

## Patterns Requiring Attention

[List 3-5 patterns that cut across multiple signals. Note confidence level. Flag anything that appears in both conversation data and behavioural data.]

## Open Questions

[3-5 questions this data raises that self-report cannot answer. These are interview prompts for follow-up.]

## For the AI Reading This Pack

[One paragraph briefing the downstream AI on how to use this pack — what to probe, what to avoid assuming, what the subject's narrator is likely to over-represent.]

Write forensically. No flattery. No resolution of contradictions. Present evidence, not verdicts."""


def generate_pack(
    signals: list[Signal],
    subject_name: str = "User",
    output_path: str | None = None,
    api_key: str | None = None,
) -> str:
    signals_text = "\n\n".join(
        f"[{s.signal_type} | {s.confidence}]\n"
        f"Finding: {s.finding}\n"
        f"Evidence: {s.evidence}\n"
        f"Sources: {', '.join(s.sources)}"
        for s in signals
    )

    all_sources = sorted({src for s in signals for src in s.sources})

    prompt = PACK_PROMPT_TEMPLATE.format(
        signal_count=len(signals),
        subject_name=subject_name,
        signals_text=signals_text,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        sources=", ".join(all_sources),
    )

    client = LLMClient(api_key=api_key)
    pack_text = client.complete(prompt)

    if output_path:
        Path(output_path).write_text(pack_text, encoding="utf-8")
        json_path = Path(output_path).with_suffix(".json")
        json_path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "subject_name": subject_name,
                    "signal_count": len(signals),
                    "signals": [
                        {
                            "signal_type": s.signal_type,
                            "confidence": s.confidence,
                            "sources": s.sources,
                            "finding": s.finding,
                            "evidence": s.evidence,
                            "metadata": s.metadata,
                        }
                        for s in signals
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return pack_text
