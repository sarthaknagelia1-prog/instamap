"""
backend/agents/content_generation_agent.py

Content Generation Agent:
Turns planned calendar items into complete, publish-ready content drafts:
- 3-part caption (hook -> body -> CTA)
- Targeted hashtag set
- Visual direction notes (camera angles, text overlays, b-roll)
- Audio/music recommendations for video/reels
- Recommended posting schedule

Supports offline deterministic generation by default, with optional LLM enhancement.
"""

from __future__ import annotations
import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import ContentDraft


def _generate_deterministic_draft(
    content_type: str,
    theme: str,
    concept_angle: str,
    niche: Optional[str],
) -> Dict[str, Any]:
    """Generates structured copy using high-converting creator templates."""
    clean_niche = niche or "Creator"

    if content_type == "reel":
        return {
            "title": f"The 3-Step {theme} Framework",
            "hook": f"Most {clean_niche.lower()}s get this completely wrong. Here is what actually moves the needle in 2026:",
            "body": (
                "1. Focus on retention first — if people leave in the first 3 seconds, the algorithm cuts distribution.\n"
                "2. One clear takeaway per video — stop trying to cover 5 ideas in 45 seconds.\n"
                "3. Deliver value before asking for anything in return."
            ),
            "call_to_action": "Save this reel so you don't forget it when scripting your next video.",
            "hashtags": [f"#{clean_niche.lower()}tips", "#instagramgrowth", "#contentstrategy", "#creatorgrowth", "#reelsgrowth"],
            "visual_direction": "Direct-to-camera with high-contrast text overlay in center-screen. Cut every 2.5-3 seconds with subtle zoom punches. Use dynamic b-roll for step 2.",
            "audio_suggestion": "Upbeat subtle lo-fi beat or trending motivational background sound (low volume under voiceover).",
        }
    elif content_type == "carousel":
        return {
            "title": f"The Complete Blueprint: {theme}",
            "hook": f"Slide 1: The exact framework I used to double results in {clean_niche.lower()} (swipe to read 👉)",
            "body": (
                "Slide 2: The Core Problem — why traditional methods fail.\n"
                "Slide 3: Step 1: Clarify your target audience's #1 burning question.\n"
                "Slide 4: Step 2: Create a high-contrast visual or comparison chart.\n"
                "Slide 5: Step 3: End with a frictionless action checklist.\n"
                "Slide 6: Summary infographic & cheat sheet."
            ),
            "call_to_action": "Share this carousel with someone who needs this framework today.",
            "hashtags": [f"#{clean_niche.lower()}strategy", "#carouseltips", "#contentmarketing", "#growthmindset", "#instagramtips"],
            "visual_direction": "Minimalist slide design (dark background, bold yellow/white typography). Consistent font pairing. Seamless swipe indicator on bottom-right of every slide.",
            "audio_suggestion": None,
        }
    else:  # image / static / story
        return {
            "title": f"Real Talk: {theme}",
            "hook": f"An uncomfortable truth about succeeding in {clean_niche.lower()}:",
            "body": (
                "Consistency without strategy is just exhaustion.\n\n"
                "Before you post your next piece of content, ask yourself:\n"
                "• Does this teach something specific?\n"
                "• Is this shareable?\n"
                "• Would I stop scrolling to read this?"
            ),
            "call_to_action": "Drop your thoughts below — agree or disagree?",
            "hashtags": [f"#{clean_niche.lower()}community", "#buildinpublic", "#authenticity", "#contentcreator"],
            "visual_direction": "Clean, authentic visual (workspace setup or high-resolution behind-the-scenes portrait). Avoid generic stock imagery.",
            "audio_suggestion": None,
        }


def _enhance_draft_with_llm(
    content_type: str,
    theme: str,
    concept_angle: str,
    niche: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Optional LLM enhancement for tailored copy."""
    try:
        from backend.agents.llm_client import LLMClient
        client = LLMClient()
        prompt = f"""
You are an expert Instagram Copywriter and Scriptwriter.
Draft a high-converting {content_type.upper()} post:
- Topic / Theme: {theme}
- Angle: {concept_angle}
- Niche: {niche or 'Creator'}

Return valid JSON with keys:
- "title": short working title
- "hook": high-stopping-power first line / 3-second hook
- "body": valuable, well-paced body copy / script
- "call_to_action": high-conversion save/share/comment prompt
- "hashtags": list of 5 targeted hashtags
- "visual_direction": specific filming or design instructions
- "audio_suggestion": audio or music vibe suggestion
"""
        raw = client.generate(prompt=prompt, system_prompt="You are a professional social media scriptwriter. Return valid JSON only.")
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:].strip()
        return json.loads(clean)
    except Exception:
        return None


def run_content_generation_agent(
    creator_id: str,
    plan_item: Dict[str, Any],
    plan_id: Optional[str] = None,
    niche: Optional[str] = None,
    use_llm: bool = False,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Generates a full ready-to-publish draft package from a planned content item.
    Persists to ContentDraft table if db session is provided.
    """
    content_type = plan_item.get("content_type", "reel")
    theme = plan_item.get("theme", "Growth Strategy")
    concept_angle = plan_item.get("concept_angle", "Educational value breakdown")
    scheduled_time = plan_item.get("scheduled_time")

    draft_package = _generate_deterministic_draft(content_type, theme, concept_angle, niche)

    if use_llm:
        llm_draft = _enhance_draft_with_llm(content_type, theme, concept_angle, niche)
        if llm_draft:
            draft_package = {**draft_package, **llm_draft}

    draft_id = str(uuid.uuid4())
    result = {
        "draft_id": draft_id,
        "creator_id": creator_id,
        "plan_id": plan_id,
        "content_type": content_type,
        "title": draft_package.get("title", f"Draft: {theme}"),
        "hook": draft_package.get("hook", ""),
        "body": draft_package.get("body", ""),
        "call_to_action": draft_package.get("call_to_action", ""),
        "hashtags": draft_package.get("hashtags", []),
        "visual_direction": draft_package.get("visual_direction"),
        "audio_suggestion": draft_package.get("audio_suggestion"),
        "recommended_time": scheduled_time,
        "status": "draft",
    }

    if db is not None:
        record = ContentDraft(
            id=draft_id,
            creator_id=creator_id,
            plan_id=plan_id,
            content_type=content_type,
            title=result["title"],
            hook=result["hook"],
            body=result["body"],
            call_to_action=result["call_to_action"],
            hashtags=result["hashtags"],
            visual_direction=result["visual_direction"],
            audio_suggestion=result["audio_suggestion"],
            recommended_time=scheduled_time,
            status="draft",
        )
        db.add(record)
        db.commit()

    return result
