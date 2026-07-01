"""Agent execution: run the tool-calling loop with a step cap."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.ai.context import AgentContext
from app.ai.prompts import build_system_prompt
from app.ai.provider import build_chat_model
from app.ai.tools import build_tools
from app.core.ai_providers import AIProvidersConfig
from app.core.config import Settings

MAX_STEPS = 6
FALLBACK_TEXT_EN = "Sorry, I got stuck. Try phrasing that differently?"
FALLBACK_TEXT_FA = "متأسفم، گیر کردم. یه‌جور دیگه بگو؟"

log = logging.getLogger(__name__)


@dataclass
class AgentResult:
    text: str
    preview_ids: list[str]


async def run_agent(
    ctx: AgentContext,
    *,
    user_message: str,
    ai_config: AIProvidersConfig,
    settings: Settings,
) -> AgentResult:
    ctx.raw_input_text = user_message
    tools = build_tools(ctx)
    tool_map = {t.name: t for t in tools}

    llm = build_chat_model(ai_config, settings).bind_tools(tools)

    messages: list[BaseMessage] = [
        SystemMessage(content=build_system_prompt(ctx)),
        HumanMessage(content=user_message),
    ]

    final_text: str | None = None
    for step in range(MAX_STEPS):
        response = await llm.ainvoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", []) or []
        if not tool_calls:
            final_text = _text_from(response)
            break

        for call in tool_calls:
            name = call["name"]
            args = call.get("args") or {}
            call_id = call["id"]

            tool = tool_map.get(name)
            if tool is None:
                result = f"error: unknown tool {name!r}"
            else:
                try:
                    result = await tool.ainvoke(args)
                except Exception as exc:  # noqa: BLE001 — surface to the LLM as an error string
                    log.exception("tool %s failed", name)
                    result = f"error: {exc}"
            messages.append(
                ToolMessage(content=str(result), tool_call_id=call_id, name=name)
            )
        log.debug("agent step %d complete (tools: %s)", step, [c["name"] for c in tool_calls])

    if final_text is None:
        final_text = FALLBACK_TEXT_FA if ctx.user.language_code == "fa" else FALLBACK_TEXT_EN

    return AgentResult(text=final_text, preview_ids=list(ctx.pending_preview_ids))


def _text_from(msg: AIMessage) -> str:
    content = msg.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(p for p in parts if p).strip()
    return str(content)
