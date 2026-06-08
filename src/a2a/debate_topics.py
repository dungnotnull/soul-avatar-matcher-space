"""
Structured debate topic bank for A2A compatibility sessions.

10 topics covering finance, conflict, creativity, lifestyle, values,
risk, communication style, family, ambition, and humor.
"""

from __future__ import annotations

DEBATE_TOPICS: list[dict] = [
    {
        "id": "finance",
        "title": "Financial Philosophy",
        "prompt_a": "How do you approach saving versus spending? Describe your philosophy on money management and what financial security means to you.",
        "prompt_b": "The other person has shared their financial perspective. Where do you see common ground, and where might you differ? Be honest about your comfort level with their approach.",
    },
    {
        "id": "conflict",
        "title": "Conflict Resolution",
        "prompt_a": "When you disagree with someone close to you, how do you typically handle it? Describe your conflict resolution style and what you need from the other person during disagreements.",
        "prompt_b": "You've heard how the other person handles conflict. How compatible do you feel your approaches are? What potential friction points do you see?",
    },
    {
        "id": "creativity",
        "title": "Creativity & Self-Expression",
        "prompt_a": "What role does creativity play in your life? How do you express yourself — through art, ideas, problem-solving, or something else entirely?",
        "prompt_b": "Having heard the other person's creative orientation, do you find their mode of expression complementary to yours? Share your genuine reaction.",
    },
    {
        "id": "lifestyle",
        "title": "Daily Life & Routines",
        "prompt_a": "Describe your ideal day — from morning to night. What routines matter to you, and how much flexibility do you need in your daily life?",
        "prompt_b": "How well would your daily rhythm mesh with what the other person described? Where might adjustments be needed, and are you open to them?",
    },
    {
        "id": "values",
        "title": "Core Values & Ethics",
        "prompt_a": "What principles guide your decisions in life? Share the values you hold most deeply — the ones you would not compromise on, even when it's difficult.",
        "prompt_b": "You've heard the other person's core values. Where do you see alignment, and where do you sense potential tension? Be honest rather than agreeable.",
    },
    {
        "id": "risk",
        "title": "Risk & Uncertainty",
        "prompt_a": "How do you approach major life decisions involving uncertainty — career changes, moves, relationships? What's your relationship with risk and the unknown?",
        "prompt_b": "Based on how the other person handles risk, do you think your decision-making styles would complement or clash? Share your authentic take.",
    },
    {
        "id": "communication",
        "title": "Communication Style",
        "prompt_a": "Are you direct or diplomatic? Do you process thoughts internally before speaking, or work through ideas out loud? Describe your natural communication patterns.",
        "prompt_b": "How well do you think your communication style would mesh with what the other person described? Could you adapt to each other's patterns?",
    },
    {
        "id": "family",
        "title": "Family & Belonging",
        "prompt_a": "What does family mean to you — whether biological, chosen, or community? How important is a shared sense of belonging in your close relationships?",
        "prompt_b": "Having heard the other person's perspective on family, how aligned do you feel? What differences excite or concern you?",
    },
    {
        "id": "ambition",
        "title": "Ambition & Growth",
        "prompt_a": "How do you define personal growth and success? What are you striving toward right now, and how does ambition manifest in your daily life?",
        "prompt_b": "The other person has shared their growth trajectory. Does their pace and direction feel compatible with yours? Be honest about any mismatch you sense.",
    },
    {
        "id": "humor",
        "title": "Humor & Playfulness",
        "prompt_a": "What makes you laugh? Share your sense of humor — the kind of wit, absurdity, or warmth that genuinely delights you.",
        "prompt_b": "Based on the other person's humor style, do you think you'd laugh together — or at the same things? Humor compatibility matters more than people admit.",
    },
]


def get_topic(topic_id: str) -> dict | None:
    for topic in DEBATE_TOPICS:
        if topic["id"] == topic_id:
            return topic
    return None


def get_all_topic_ids() -> list[str]:
    return [t["id"] for t in DEBATE_TOPICS]


def get_default_topics() -> list[str]:
    return ["finance", "conflict", "values", "communication", "ambition"]
