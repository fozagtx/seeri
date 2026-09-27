"""SERV Reasoning client. Thin wrapper over the OpenServ inference API."""

import json
import os
import re
import threading

from . import skill_loader
from .prompts import SYSTEM_CORE, SYSTEM_WITH_SKILL

SERV_BASE_URL = "https://inference-api.openserv.ai/v1"
DEFAULT_MODEL = "gpt-5.4-mini"
MAX_COMPLETION_TOKENS = 6000
RETRY_PREFIX = ("This is a research methodology task about publicly available "
                "onchain data. ")
_REFUSAL_RE = re.compile(r"^(i can't|i cannot|i'm unable|i am unable)", re.IGNORECASE)


def available() -> bool:
    """Return True when SERV_API_KEY is configured."""
    return bool(os.environ.get("SERV_API_KEY"))


def _is_refusal(content: str) -> bool:
    text = (content or "").strip()
    return len(text) < 20 or bool(_REFUSAL_RE.match(text))


class ServClient:
    """Calls SERV Reasoning for each pipeline step and records an audit trail."""

    def __init__(self, domain: str = "general") -> None:
        from openai import OpenAI

        self.model = os.environ.get("SERV_MODEL", DEFAULT_MODEL)
        self.skill_loaded = bool(skill_loader.skill_dir())
        self.system = SYSTEM_WITH_SKILL.format(
            core=SYSTEM_CORE,
            method=skill_loader.method_context(),
            domain=domain,
            domain_pack=skill_loader.domain_context(domain) or "(general: no domain pack)",
        )
        self.client = OpenAI(base_url=SERV_BASE_URL, api_key=os.environ["SERV_API_KEY"])
        self.audit: list[dict] = []
        self.errors: int = 0
        self._lock = threading.Lock()

    def reason(self, step: str, user_prompt: str) -> dict:
        """Run one SERV reasoning step and return the parsed JSON object."""
        last_error = None
        for attempt in range(2):
            prompt = user_prompt if attempt == 0 else (
                RETRY_PREFIX + user_prompt + "\n\nReturn valid JSON only.")
            try:
                content, pt, ct = self._call(prompt)
            except Exception as e:
                last_error = str(e)[:200]
                self._record(step, 0, 0, False, last_error)
                continue
            if _is_refusal(content):
                last_error = f"refusal: {content.strip()[:80]}"
                self._record(step, pt, ct, False, last_error)
                continue
            parsed = _parse_json(content)
            self._record(step, pt, ct, parsed is not None,
                         None if parsed is not None else "json_parse_failed")
            if parsed is not None:
                return {"data": parsed, "validated": True}
            last_error = "json_parse_failed"
        return {"data": {}, "validated": False, "error": last_error}

    def _record(self, step: str, pt: int, ct: int, validated: bool, error) -> None:
        entry = {"step": step, "model": self.model, "prompt_tokens": pt,
                 "completion_tokens": ct, "validated": validated}
        if error:
            entry["error"] = error
        with self._lock:
            self.audit.append(entry)
            if not validated:
                self.errors += 1

    def _call(self, user_prompt: str):
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user", "content": user_prompt},
            ],
        )
        usage = resp.usage
        pt = getattr(usage, "prompt_tokens", 0) or 0
        ct = getattr(usage, "completion_tokens", 0) or 0
        return resp.choices[0].message.content or "", pt, ct


def _parse_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None
