import json
from datetime import datetime, timezone
from pathlib import Path
from signals.base import Signal
from pack.llm import LLMClient


PACK_PROMPT_TEMPLATE = """You are a forensic identity analyst. Below are {signal_count} signals extracted from {subject_name}'s personal data. These signals were detected automatically from digital exhaust files — data generated without narrator curation.

Your task: produce a structured WHOAMI context pack. This is a portable identity document designed to give any AI immediate, calibrated understanding of this person.

SIGNALS:
{signals_text}

CALIBRATION RULES — follow these strictly:
- Each signal includes a DATA_QUALITY field: "sufficient" or "marginal"
- For MARGINAL signals: use hedged language ("may suggest", "tentatively", "weakly indicated"). Do not present as established finding.
- Do not synthesise cross-signal patterns when the majority of signals are marginal. Note the limitation instead.
- For signals with effect_size < 0.10: treat as indicative only, not conclusive.
- If fewer than 2 signals are "sufficient" quality, open the pack with a data quality caveat before the identity signals section.

Produce the context pack in this format:

# WHOAMI Context Pack — {subject_name}
Generated: {date}
Signals: {signal_count} | Sources: {sources}

---

## Identity Signals

[For each signal: state what the data shows, include the confidence level, and note data quality where marginal. Present contradictions as open findings. Do not resolve or explain away conflicts.]

## Patterns Requiring Attention

[List patterns that cut across multiple SUFFICIENT signals only. If cross-signal synthesis is not warranted, say so explicitly and explain why. Note confidence level for each pattern.]

## Open Questions

[3-5 questions this data raises that self-report cannot answer.]

## For the AI Reading This Pack

[One paragraph: how to use this pack, what to probe, what the subject's narrator likely over-represents, what the data cannot confirm.]

Write forensically. No flattery. No resolution of contradictions. Present evidence, not verdicts."""


def _format_signal(s: Signal) -> str:
    data_quality = s.metadata.get("data_quality", "sufficient")
    effect_size = s.metadata.get("effect_size")
    effect_str = f" | effect_size: {effect_size:.3f}" if effect_size is not None else ""
    return (
        f"[{s.signal_type} | confidence: {s.confidence} | data_quality: {data_quality}{effect_str}]\n"
        f"Finding: {s.finding}\n"
        f"Evidence: {s.evidence}\n"
        f"Sources: {', '.join(s.sources)}"
    )


def generate_pack(
    signals: list[Signal],
    subject_name: str = "User",
    output_path: str | None = None,
    api_key: str | None = None,
) -> str:
    signals_text = "\n\n".join(_format_signal(s) for s in signals)
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
