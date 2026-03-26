from __future__ import annotations

import os
import re
import json
import time
import uuid
import textwrap
import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
import pandas as pd

try:
    import yaml  # pyyaml
except Exception:
    yaml = None


# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="SmartMed Review 4.3",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Constants / Design Tokens
# -----------------------------
APP_VERSION = "4.3.0"
DEFAULT_MAX_TOKENS = 12000
DEFAULT_TEMPERATURE = 0.2

# UI language dictionary (minimal core; expand as needed)
I18N = {
    "English": {
        "app_title": "SmartMed Review 4.3",
        "global_settings": "Global Settings",
        "theme": "Theme",
        "language": "Language",
        "style": "Painter Style",
        "jackpot": "Jackpot",
        "lock_style": "Lock style for session",
        "provider_keys": "Provider API Keys",
        "managed_env": "Managed by environment",
        "missing_key": "Missing API key",
        "enter_key": "Enter API key (session-only)",
        "clear_key": "Clear session key",
        "models": "Models",
        "default_model": "Default model",
        "max_tokens": "Max tokens",
        "temperature": "Temperature",
        "dashboard": "Dashboard",
        "live_log": "Live Log",
        "builder": "510(k) Guidance Builder",
        "agent_studio": "Agent Studio",
        "note_keeper": "AI Note Keeper",
        "run": "Run",
        "cancel": "Cancel (best-effort)",
        "download": "Download",
        "copy": "Copy",
        "input": "Input",
        "output": "Output",
        "markdown_view": "Markdown View",
        "text_view": "Text View",
        "edit_output": "Edit output (effective output used downstream)",
        "artifacts": "Artifacts",
        "select_artifact": "Select artifact",
        "save_as_artifact": "Save as artifact",
        "artifact_name": "Artifact name",
        "constraint_panel": "Constraint Panel",
        "tables_count": "Markdown tables count",
        "entities_count": "Entities count",
        "word_estimate": "Word estimate",
        "char_count": "Character count",
        "status": "Status",
        "warnings": "Warnings",
        "regenerate_hint": "Regenerate hint",
        "template": "Template",
        "use_default_template": "Use default template",
        "paste_template": "Paste template (TXT/Markdown)",
        "describe_template": "Describe template (text)",
        "generate_organized": "Generate Organized Document (A)",
        "generate_guidance": "Generate Review Guidance (B)",
        "generate_skill": "Generate SKILL.md (C)",
        "organized_doc": "Organized Document (A)",
        "review_guidance": "510(k) Review Guidance (B)",
        "skill_md": "SKILL.md",
        "note_input": "Paste note (TXT/Markdown)",
        "organize_note": "Organize note",
        "ai_magics": "AI Magics",
        "apply_magic": "Apply magic",
        "export_logs": "Export logs",
        "export_jsonl": "Export JSONL",
        "export_txt": "Export TXT",
        "run_inspector": "Run Inspector",
        "preflight_blocked": "Preflight blocked",
    },
    "繁體中文": {
        "app_title": "SmartMed Review 4.3",
        "global_settings": "全域設定",
        "theme": "主題",
        "language": "語言",
        "style": "畫家風格",
        "jackpot": "Jackpot 抽風格",
        "lock_style": "鎖定本次工作階段風格",
        "provider_keys": "供應商 API Key",
        "managed_env": "由環境變數管理",
        "missing_key": "缺少 API Key",
        "enter_key": "輸入 API Key（僅此工作階段）",
        "clear_key": "清除工作階段 Key",
        "models": "模型",
        "default_model": "預設模型",
        "max_tokens": "最大 tokens",
        "temperature": "溫度",
        "dashboard": "儀表板",
        "live_log": "即時日誌",
        "builder": "510(k) 指引生成器",
        "agent_studio": "Agent 工作室",
        "note_keeper": "AI 筆記管家",
        "run": "執行",
        "cancel": "取消（盡力而為）",
        "download": "下載",
        "copy": "複製",
        "input": "輸入",
        "output": "輸出",
        "markdown_view": "Markdown 檢視",
        "text_view": "文字檢視",
        "edit_output": "編輯輸出（後續使用編輯後版本）",
        "artifacts": "產物",
        "select_artifact": "選擇產物",
        "save_as_artifact": "儲存為產物",
        "artifact_name": "產物名稱",
        "constraint_panel": "限制條件檢查",
        "tables_count": "Markdown 表格數量",
        "entities_count": "實體數量",
        "word_estimate": "字數估算",
        "char_count": "字元數",
        "status": "狀態",
        "warnings": "警告",
        "regenerate_hint": "重新生成提示",
        "template": "模板",
        "use_default_template": "使用預設審查指引模板",
        "paste_template": "貼上模板（TXT/Markdown）",
        "describe_template": "描述模板（文字）",
        "generate_organized": "產生整理文件（A）",
        "generate_guidance": "產生審查指引（B）",
        "generate_skill": "產生 SKILL.md（C）",
        "organized_doc": "整理文件（A）",
        "review_guidance": "510(k) 審查指引（B）",
        "skill_md": "SKILL.md",
        "note_input": "貼上筆記（TXT/Markdown）",
        "organize_note": "整理筆記",
        "ai_magics": "AI 魔法",
        "apply_magic": "套用魔法",
        "export_logs": "匯出日誌",
        "export_jsonl": "匯出 JSONL",
        "export_txt": "匯出 TXT",
        "run_inspector": "執行檢視器",
        "preflight_blocked": "前置檢查已阻擋",
    },
}

THEMES = ["Light", "Dark"]

# 20 painter-inspired style presets (simple token sets; no IP assets)
PAINTER_STYLES: Dict[str, Dict[str, str]] = {
    "Monet": {"bg1": "#f7fbff", "bg2": "#eaf3ff", "accent": "#3a86ff", "coral": "#ff6f61"},
    "Van Gogh": {"bg1": "#0b1320", "bg2": "#1c2b4a", "accent": "#ffb703", "coral": "#ff6f61"},
    "Picasso": {"bg1": "#f6f1ea", "bg2": "#efe7da", "accent": "#2a9d8f", "coral": "#ff6f61"},
    "Klimt": {"bg1": "#111111", "bg2": "#1b1b1b", "accent": "#d4af37", "coral": "#ff6f61"},
    "Hokusai": {"bg1": "#f3f7ff", "bg2": "#e6efff", "accent": "#1d4ed8", "coral": "#ff6f61"},
    "Rothko": {"bg1": "#120c0c", "bg2": "#231010", "accent": "#e63946", "coral": "#ff6f61"},
    "Pollock": {"bg1": "#0f0f12", "bg2": "#18181f", "accent": "#a855f7", "coral": "#ff6f61"},
    "Vermeer": {"bg1": "#fbf7ef", "bg2": "#f1e7d1", "accent": "#2563eb", "coral": "#ff6f61"},
    "Matisse": {"bg1": "#fff7f5", "bg2": "#ffe7e1", "accent": "#ef4444", "coral": "#ff6f61"},
    "Rembrandt": {"bg1": "#0f0b07", "bg2": "#1a120b", "accent": "#f59e0b", "coral": "#ff6f61"},
    "Turner": {"bg1": "#f7fbff", "bg2": "#fff3d6", "accent": "#fb7185", "coral": "#ff6f61"},
    "Cézanne": {"bg1": "#f3f4f6", "bg2": "#e5e7eb", "accent": "#16a34a", "coral": "#ff6f61"},
    "Magritte": {"bg1": "#eef6ff", "bg2": "#dbeafe", "accent": "#0ea5e9", "coral": "#ff6f61"},
    "Dalí": {"bg1": "#0b0f1a", "bg2": "#111827", "accent": "#22c55e", "coral": "#ff6f61"},
    "Kandinsky": {"bg1": "#0b0b0f", "bg2": "#12121a", "accent": "#f97316", "coral": "#ff6f61"},
    "Hopper": {"bg1": "#f8fafc", "bg2": "#e2e8f0", "accent": "#0f172a", "coral": "#ff6f61"},
    "O’Keeffe": {"bg1": "#ffffff", "bg2": "#f3f4f6", "accent": "#7c3aed", "coral": "#ff6f61"},
    "Basquiat": {"bg1": "#0b0b0b", "bg2": "#161616", "accent": "#facc15", "coral": "#ff6f61"},
    "Bruegel": {"bg1": "#f7f2e8", "bg2": "#efe3c7", "accent": "#14532d", "coral": "#ff6f61"},
    "Ukiyo-e": {"bg1": "#f6fbff", "bg2": "#e0f2fe", "accent": "#0284c7", "coral": "#ff6f61"},
}

DEFAULT_STYLE = "Monet"


DEFAULT_TEMPLATE_ZH = """# 經皮冠狀動脈擴張術 (PTCA) 藥物塗層球囊 (DCB) 導管審查指引

## 1. 範疇
本指引適用於用於經皮冠狀動脈擴張術 (PTCA) 的藥物塗層球囊 (DCB) 導管。這些裝置設計用於在球囊擴張過程中，將藥物直接傳遞至冠狀動脈壁，以改善管腔直徑並降低再狹窄的發生率。

### 1.1 分類與法規狀態
- TFDA 分類：E.0005 (經皮冠狀動脈擴張術導管)
- 風險等級：第三級 (高風險)
- 排除產品：含有生物藥物成分的組合產品不在本指引範疇內

### 1.2 基本原則
製造商必須提供完整的驗證數據，涵蓋臨床前測試以確保安全性與有效性。所有測試必須在完成、滅菌的產品或經驗證的等效樣品上進行。若使用非滅菌或未完成的樣品，必須提供充分的科學理由。

## 2. 審查重點
### 2.1 技術文件與產品描述
### 2.2 藥物成分的化學、製造與管制 (CMC)
### 2.3 製造流程（塗層製程）

## 3. 審查流程（流程圖）
（此處可插入流程描述）

## 4. 安全與性能數據要求
### 4.1 工程與功能測試
### 4.2 塗層特性
### 4.3 藥理與毒理

## 5. 國際法規比較（可含表格）
## 6. 缺失風險評估（可含表格）
## 7. 法規追溯熱圖（可含表格）
## 8. 技術深度解析
"""


# -----------------------------
# Session State Initialization
# -----------------------------
def _init_session() -> None:
    ss = st.session_state
    ss.setdefault("app_version", APP_VERSION)
    ss.setdefault("theme", "Light")
    ss.setdefault("language", "English")
    ss.setdefault("style_locked", True)
    ss.setdefault("painter_style", DEFAULT_STYLE)

    ss.setdefault("default_model", "gpt-4.1-mini")
    ss.setdefault("default_max_tokens", DEFAULT_MAX_TOKENS)
    ss.setdefault("default_temperature", DEFAULT_TEMPERATURE)

    ss.setdefault("events", [])  # structured run events
    ss.setdefault("runs", [])    # run summaries for dashboard
    ss.setdefault("active_run_id", None)

    ss.setdefault("session_keys", {})  # provider -> key (session-only)
    ss.setdefault("artifacts", {})     # name -> content
    ss.setdefault("artifact_meta", {}) # name -> meta dict

    # 510(k) builder state
    ss.setdefault("k510_input_doc", "")
    ss.setdefault("k510_output_A_raw", "")
    ss.setdefault("k510_output_A_effective", "")
    ss.setdefault("k510_template_mode", "default")  # default|paste|describe
    ss.setdefault("k510_template_paste", DEFAULT_TEMPLATE_ZH)
    ss.setdefault("k510_template_desc", "")
    ss.setdefault("k510_template_outline", "")
    ss.setdefault("k510_output_B_raw", "")
    ss.setdefault("k510_output_B_effective", "")
    ss.setdefault("k510_skill_md_raw", "")
    ss.setdefault("k510_skill_md_effective", "")

    # Note keeper state
    ss.setdefault("note_input", "")
    ss.setdefault("note_output_raw", "")
    ss.setdefault("note_output_effective", "")
    ss.setdefault("note_pinned_prompt", "")

    # Agent studio state
    ss.setdefault("agents_yaml_text", "")
    ss.setdefault("agents_loaded", [])
    ss.setdefault("agent_selected_name", "")
    ss.setdefault("agent_prompt_overrides", {})  # agent_name -> {system,user}
    ss.setdefault("agent_output_raw", {})
    ss.setdefault("agent_output_effective", {})

    # Log filter state
    ss.setdefault("log_filter_run_id", "")
    ss.setdefault("log_filter_module", "All")
    ss.setdefault("log_filter_severity", "All")


_init_session()


# -----------------------------
# Utility: i18n
# -----------------------------
def t(key: str) -> str:
    lang = st.session_state.get("language", "English")
    return I18N.get(lang, I18N["English"]).get(key, key)


# -----------------------------
# WOW UI CSS
# -----------------------------
def apply_wow_css(theme: str, painter_style: str) -> None:
    style = PAINTER_STYLES.get(painter_style, PAINTER_STYLES[DEFAULT_STYLE])
    bg1, bg2 = style["bg1"], style["bg2"]
    accent, coral = style["accent"], style["coral"]

    if theme == "Dark":
        base_text = "#e5e7eb"
        panel_bg = "rgba(15, 23, 42, 0.55)"
        border = "rgba(148, 163, 184, 0.22)"
    else:
        base_text = "#0f172a"
        panel_bg = "rgba(255, 255, 255, 0.72)"
        border = "rgba(15, 23, 42, 0.12)"

    css = f"""
    <style>
      .stApp {{
        background: linear-gradient(135deg, {bg1} 0%, {bg2} 100%);
        color: {base_text};
      }}
      .wow-panel {{
        background: {panel_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 16px 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.10);
      }}
      .wow-badge {{
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid {border};
        background: rgba(255,255,255,0.10);
        font-size: 12px;
      }}
      .wow-accent {{
        color: {accent};
        font-weight: 700;
      }}
      .wow-coral {{
        color: {coral};
        font-weight: 700;
      }}
      .wow-divider {{
        height: 1px;
        background: {border};
        margin: 12px 0;
      }}
      /* Make code blocks nicer */
      pre, code {{
        border-radius: 10px !important;
      }}
      /* Buttons */
      .stButton>button {{
        border-radius: 12px;
        border: 1px solid {border};
      }}
      /* Text areas */
      textarea {{
        border-radius: 12px !important;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


apply_wow_css(st.session_state["theme"], st.session_state["painter_style"])


# -----------------------------
# Logging / Observability
# -----------------------------
def now_utc_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def redact_secrets(text: str) -> str:
    """Best-effort redaction of API keys/tokens if accidentally present in strings."""
    if not text:
        return text
    patterns = [
        r"sk-[A-Za-z0-9]{20,}",
        r"AIza[0-9A-Za-z\-_]{20,}",   # google-ish
        r"(?i)anthropic[_\- ]?api[_\- ]?key\s*[:=]\s*\S+",
        r"(?i)xai[_\- ]?api[_\- ]?key\s*[:=]\s*\S+",
        r"(?i)openai[_\- ]?api[_\- ]?key\s*[:=]\s*\S+",
    ]
    redacted = text
    for p in patterns:
        redacted = re.sub(p, "[REDACTED]", redacted)
    return redacted


def log_event(
    module: str,
    severity: str,
    event_type: str,
    message: str,
    run_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    ev = {
        "ts_utc": now_utc_iso(),
        "run_id": run_id or st.session_state.get("active_run_id") or "",
        "module": module,
        "severity": severity,
        "event_type": event_type,
        "message": redact_secrets(message),
        "extra": extra or {},
    }
    st.session_state["events"].append(ev)


def begin_run(module: str, title: str, model: str, params: Dict[str, Any]) -> str:
    run_id = str(uuid.uuid4())
    st.session_state["active_run_id"] = run_id
    run = {
        "run_id": run_id,
        "ts_start_utc": now_utc_iso(),
        "ts_end_utc": "",
        "module": module,
        "title": title,
        "model": model,
        "provider": model_to_provider(model),
        "status": "running",
        "params": params,
        "metrics": {},
        "warnings": [],
        "errors": [],
        "artifacts": [],
    }
    st.session_state["runs"].append(run)
    log_event(module, "info", "run_started", f"{title} started", run_id=run_id, extra={"model": model, "params": params})
    return run_id


def end_run(run_id: str, status: str, metrics: Optional[Dict[str, Any]] = None) -> None:
    for r in st.session_state["runs"]:
        if r["run_id"] == run_id:
            r["ts_end_utc"] = now_utc_iso()
            r["status"] = status
            if metrics:
                r["metrics"].update(metrics)
            break
    log_event("system", "info" if status == "success" else "warn", "run_ended", f"Run ended: {status}", run_id=run_id)
    if st.session_state.get("active_run_id") == run_id:
        st.session_state["active_run_id"] = None


def attach_artifact_to_run(run_id: str, artifact_name: str) -> None:
    for r in st.session_state["runs"]:
        if r["run_id"] == run_id:
            r["artifacts"].append(artifact_name)
            break


# -----------------------------
# Providers / Model Routing
# -----------------------------
OPENAI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini"]
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
GROK_MODELS = ["grok-4-fast-reasoning", "grok-3-mini"]
# Anthropic list is configurable; provide a safe default list but allow arbitrary "claude-"
ANTHROPIC_DEFAULT = ["claude-3.5-sonnet", "claude-3.5-haiku"]

ALL_MODELS = OPENAI_MODELS + GEMINI_MODELS + GROK_MODELS + ANTHROPIC_DEFAULT


def model_to_provider(model: str) -> str:
    if model in OPENAI_MODELS or model.startswith("gpt-"):
        return "openai"
    if model in GEMINI_MODELS or model.startswith("gemini-"):
        return "gemini"
    if model in GROK_MODELS or model.startswith("grok-"):
        return "grok"
    if model in ANTHROPIC_DEFAULT or model.startswith("claude-"):
        return "anthropic"
    # default fallback
    return "openai"


def env_key_for_provider(provider: str) -> str:
    mapping = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "grok": "XAI_API_KEY",
    }
    return mapping.get(provider, "")


def get_api_key(provider: str) -> Tuple[Optional[str], str]:
    """
    Returns (key, source) where source in {"env","session","missing"}.
    """
    env_var = env_key_for_provider(provider)
    if env_var and os.getenv(env_var):
        return os.getenv(env_var), "env"

    k = st.session_state.get("session_keys", {}).get(provider)
    if k:
        return k, "session"

    return None, "missing"


def preflight_check(model: str) -> Tuple[bool, str]:
    provider = model_to_provider(model)
    key, source = get_api_key(provider)
    if not key:
        return False, f"{t('missing_key')}: {provider} ({env_key_for_provider(provider)})"
    return True, f"ok ({provider}, {source})"


def _requests_post_json(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout_s: int = 120,
) -> Dict[str, Any]:
    r = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    # Bugfix: provide useful error body without throwing obscure exceptions
    if r.status_code >= 400:
        try:
            body = r.json()
        except Exception:
            body = {"text": r.text}
        raise RuntimeError(f"HTTP {r.status_code} error: {body}")
    return r.json()


def call_llm(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """
    Unified LLM call returning a text response.
    Defensive parsing across providers.
    """
    provider = model_to_provider(model)
    ok, msg = preflight_check(model)
    if not ok:
        raise RuntimeError(msg)

    key, _ = get_api_key(provider)
    assert key is not None

    if provider == "openai":
        # OpenAI Chat Completions
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt or ""},
            ],
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        data = _requests_post_json(url, headers, payload, timeout_s=180)
        return data["choices"][0]["message"]["content"]

    if provider == "gemini":
        # Gemini generateContent
        # Bugfix: endpoint expects model in path and key in query.
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        # Bugfix: Gemini expects "contents" with role parts.
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": (system_prompt or "").strip() + "\n\n" + (user_prompt or "").strip()}]}
            ],
            "generationConfig": {
                "temperature": float(temperature),
                "maxOutputTokens": int(max_tokens),
            },
        }
        data = _requests_post_json(url, headers, payload, timeout_s=180)
        # Defensive parsing
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: {data}")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join([p.get("text", "") for p in parts])
        return text or json.dumps(data)[:2000]

    if provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "system": system_prompt or "",
            "messages": [{"role": "user", "content": user_prompt or ""}],
        }
        data = _requests_post_json(url, headers, payload, timeout_s=180)
        # Defensive parsing for Anthropic content blocks
        content = data.get("content", [])
        if isinstance(content, list):
            texts = []
            for block in content:
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
            return "\n".join(texts).strip()
        return str(content)

    if provider == "grok":
        # xAI is OpenAI-compatible in many setups.
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt or ""},
            ],
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        data = _requests_post_json(url, headers, payload, timeout_s=180)
        return data["choices"][0]["message"]["content"]

    raise RuntimeError(f"Unknown provider for model={model}")


# -----------------------------
# Markdown Constraints Utilities
# -----------------------------
TABLE_REGEX = re.compile(r"(?m)^\|.+\|\s*\n^\|(?:\s*:?-+:?\s*\|)+\s*$")


def count_markdown_tables(md: str) -> int:
    if not md:
        return 0
    # Detect common Markdown pipe-table header + separator line
    return len(TABLE_REGEX.findall(md))


def estimate_words_and_chars(text: str) -> Tuple[int, int]:
    if not text:
        return 0, 0
    chars = len(text)
    # Word estimate: split on whitespace for Latin; for CJK this undercounts, so we show chars too.
    words = len(re.findall(r"\S+", text))
    return words, chars


ENTITY_MARKER_REGEX = re.compile(r"(?m)^\s*-\s*\*\*Entity\s*#\d+\*\*", re.IGNORECASE)


def count_entities(md: str) -> int:
    if not md:
        return 0
    return len(ENTITY_MARKER_REGEX.findall(md))


def constraint_summary(md: str) -> Dict[str, Any]:
    tables = count_markdown_tables(md)
    entities = count_entities(md)
    words, chars = estimate_words_and_chars(md)
    return {"tables": tables, "entities": entities, "words_est": words, "chars": chars}


def make_constraint_warnings(
    md: str,
    expected_tables: int,
    expected_entities: int,
    min_words: int,
    max_words: int,
) -> List[str]:
    s = constraint_summary(md)
    warns = []
    if s["tables"] != expected_tables:
        warns.append(f"Table count mismatch: expected {expected_tables}, got {s['tables']}.")
    if s["entities"] != expected_entities:
        warns.append(f"Entity count mismatch: expected {expected_entities}, got {s['entities']}.")
    # word estimate is heuristic, especially for CJK; still useful
    if s["words_est"] < min_words or s["words_est"] > max_words:
        warns.append(f"Length outside target band (word-est): target {min_words}–{max_words}, got ~{s['words_est']}. (CJK note: also check chars={s['chars']})")
    return warns


# -----------------------------
# Agents YAML Loading
# -----------------------------
@dataclass
class AgentDef:
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    default_model: str = "gpt-4.1-mini"
    default_max_tokens: int = DEFAULT_MAX_TOKENS
    default_temperature: float = DEFAULT_TEMPERATURE


def default_agents() -> List[AgentDef]:
    return [
        AgentDef(
            name="k510-organize-doc",
            description="Transform 510(k) submission summary/review note/guidance into an organized Markdown doc preserving all original info. Exactly 5 tables and 20 entities with context.",
            system_prompt="You are a senior medical device regulatory reviewer assistant. Do not fabricate. Preserve all original information.",
            user_prompt_template=textwrap.dedent("""
            Task: Transform the INPUT into an organized Markdown document.

            HARD CONSTRAINTS:
            - Output MUST be Markdown.
            - Keep ALL original information. Do NOT delete any original facts.
              If you restructure, include a 'Source Preservation Appendix' that contains the original content verbatim.
            - Exactly 5 Markdown pipe tables in the entire document.
            - Exactly 20 entities with context, in a section titled '## Entities with Context (20)'.
              Each entity must be a bullet beginning with: - **Entity #N**
              and must include: Name, Type, Context (with Source Anchor), Why it matters, Source Anchor(s).
            - Target length: 2000–3000 words (approx; also ensure the output is substantial).
            - Add 'Source Anchors' like SRC-001, SRC-002... for each source chunk.

            REQUIRED TABLES (exactly 5 total):
            1) Document Map
            2) Key Claims / Statements (Traceable)
            3) Evidence/Artifact Inventory (As Stated)
            4) Risk / Deficiency Candidates
            5) Terminology & Abbreviation Index

            INPUT (verbatim, do not lose anything):
            ---
            {input_text}
            ---
            """).strip(),
            default_model="gpt-4.1-mini",
        ),
        AgentDef(
            name="k510-normalize-template",
            description="Normalize template (default/pasted/description) into a Template Outline artifact.",
            system_prompt="You are a regulatory documentation architect. Produce a concise Template Outline without adding new regulatory requirements.",
            user_prompt_template=textwrap.dedent("""
            Task: Create a 'Template Outline' for a 510(k) review guidance document.

            Inputs:
            - TEMPLATE (may be full template text OR a description)
            - If TEMPLATE is empty, infer a reasonable outline from the default context, but do not fabricate regulatory claims.

            Output MUST be Markdown with:
            - # Template Outline
            - ## Headings (ordered list with hierarchy)
            - ## Required sections (bullets)
            - ## Table placement guidance
            - ## Checklist expectations
            - ## Language/tone notes

            TEMPLATE:
            ---
            {input_text}
            ---
            """).strip(),
            default_model="gpt-4o-mini",
        ),
        AgentDef(
            name="k510-generate-review-guidance",
            description="Transform the organized doc into a template-aligned 510(k) review guidance with 5 tables, 20 entities, and a review checklist.",
            system_prompt="You are a senior 510(k) reviewer. Be strict, practical, and traceable. Do not fabricate evidence or standards not mentioned; if needed, label assumptions clearly.",
            user_prompt_template=textwrap.dedent("""
            Task: Using the ORGANIZED DOCUMENT and TEMPLATE OUTLINE, write a 510(k) Review Guidance document.

            HARD CONSTRAINTS:
            - Output MUST be Markdown.
            - Exactly 5 Markdown pipe tables total.
            - Exactly 20 entities with context in '## Entities with Context (20)' using bullet format '- **Entity #N** ...'
            - Must include '## Review Checklist' with actionable items aligned to template sections.
            - Target length: 3000–4000 words (approx; substantial detail).

            TABLES (exactly 5 total; adapt names to template if needed):
            1) Regulatory Pathway & Classification Snapshot
            2) Submission Completeness / Expected Sections
            3) Standards & Test Expectations Traceability
            4) Risk-to-Evidence Mapping
            5) Decision & Escalation Triggers

            TRACEABILITY:
            - Reference Source Anchors (SRC-###) where relevant.
            - Do not remove original information; carry forward key points and preserve traceability.

            TEMPLATE OUTLINE:
            ---
            {template_outline}
            ---

            ORGANIZED DOCUMENT:
            ---
            {organized_doc}
            ---
            """).strip(),
            default_model="gpt-4.1-mini",
        ),
        AgentDef(
            name="skill-md-generator",
            description="Create SKILL.md for an agent to review 510(k) submissions based on the preview review guidance, following skill-creator best practices.",
            system_prompt="You are a skill-creator assistant. Create a reusable skill description that triggers reliably for 510(k) review tasks and produces structured outputs. No code.",
            user_prompt_template=textwrap.dedent("""
            Task: Create a SKILL.md (or skill.md) that will be used by an agent to review a 510(k) submission using the provided REVIEW GUIDANCE.

            REQUIREMENTS:
            - Use Markdown with YAML frontmatter at the top.
            - Include:
              - name
              - description (pushy triggers; should trigger when user asks for 510(k) review, deficiency identification, checklist-based review, submission completeness review)
            - Body must include:
              - When to use / when not to use
              - Required inputs (what parts of submission are needed)
              - Step-by-step workflow for review (intake -> completeness -> claim/evidence -> gaps -> risk-based prioritization -> output package)
              - Output formats: (1) Review memo, (2) Deficiency list, (3) Checklist report, (4) Traceability summary
              - Guardrails: no fabrication, uncertainty labeling, cite submission sections
              - 2–3 realistic test prompts (no assertions needed)

            REVIEW GUIDANCE (preview):
            ---
            {input_text}
            ---
            """).strip(),
            default_model="gpt-4o-mini",
        ),
        AgentDef(
            name="note-organizer",
            description="Organize a pasted note into structured Markdown, highlight keywords in coral color.",
            system_prompt="You are an expert note organizer. Do not invent facts. Keep meaning. Output Markdown. Highlight keywords in coral using <span style='color:#ff6f61;font-weight:700'>keyword</span>.",
            user_prompt_template=textwrap.dedent("""
            Transform the note into organized Markdown with:
            - Title (if inferable)
            - Sections with headings
            - Action items / decisions / open questions
            - Keywords highlighted in coral inline (HTML span)
            - Keep original facts; do not add new facts.

            NOTE:
            ---
            {input_text}
            ---
            """).strip(),
            default_model="gpt-4o-mini",
        ),
    ]


def load_agents_from_yaml_text(yaml_text: str) -> List[AgentDef]:
    if not yaml_text.strip():
        return default_agents()
    if yaml is None:
        raise RuntimeError("pyyaml not installed; cannot parse agents.yaml text.")
    data = yaml.safe_load(yaml_text)
    agents = []
    for a in data.get("agents", []):
        agents.append(
            AgentDef(
                name=str(a.get("name", "")).strip(),
                description=str(a.get("description", "")).strip(),
                system_prompt=str(a.get("system_prompt", "")).strip(),
                user_prompt_template=str(a.get("user_prompt_template", "{input_text}")).strip(),
                default_model=str(a.get("default_model", st.session_state["default_model"])).strip(),
                default_max_tokens=int(a.get("default_max_tokens", st.session_state["default_max_tokens"])),
                default_temperature=float(a.get("default_temperature", st.session_state["default_temperature"])),
            )
        )
    # Bugfix: if YAML loads empty or malformed, fallback safely
    return agents or default_agents()


def refresh_agents() -> None:
    try:
        agents = load_agents_from_yaml_text(st.session_state.get("agents_yaml_text", ""))
        st.session_state["agents_loaded"] = agents
        if not st.session_state.get("agent_selected_name") and agents:
            st.session_state["agent_selected_name"] = agents[0].name
    except Exception as e:
        log_event("agents", "error", "agents_load_failed", str(e))
        st.session_state["agents_loaded"] = default_agents()


# initial load
if not st.session_state.get("agents_loaded"):
    # Try to read local agents.yaml if present
    if os.path.exists("agents.yaml"):
        try:
            with open("agents.yaml", "r", encoding="utf-8") as f:
                st.session_state["agents_yaml_text"] = f.read()
        except Exception as e:
            log_event("agents", "warn", "agents_yaml_read_failed", str(e))
    refresh_agents()


# -----------------------------
# Sidebar: Global Settings + Keys
# -----------------------------
with st.sidebar:
    st.markdown(f"<div class='wow-panel'><div class='wow-accent'>{t('app_title')}</div><div class='wow-badge'>v{APP_VERSION}</div></div>", unsafe_allow_html=True)
    st.markdown("")

    st.subheader(t("global_settings"))

    c1, c2 = st.columns(2)
    with c1:
        st.session_state["theme"] = st.selectbox(t("theme"), THEMES, index=THEMES.index(st.session_state["theme"]))
    with c2:
        st.session_state["language"] = st.selectbox(t("language"), list(I18N.keys()), index=list(I18N.keys()).index(st.session_state["language"]))

    # Painter style + jackpot
    st.session_state["style_locked"] = st.checkbox(t("lock_style"), value=st.session_state["style_locked"])
    style_names = list(PAINTER_STYLES.keys())
    current_style = st.session_state["painter_style"]

    style_col1, style_col2 = st.columns([2, 1])
    with style_col1:
        st.session_state["painter_style"] = st.selectbox(t("style"), style_names, index=style_names.index(current_style) if current_style in style_names else 0)
    with style_col2:
        if st.button(t("jackpot")) and not st.session_state["style_locked"]:
            # Bugfix: make deterministic per click; still random-like
            idx = int(time.time() * 1000) % len(style_names)
            st.session_state["painter_style"] = style_names[idx]

    apply_wow_css(st.session_state["theme"], st.session_state["painter_style"])

    st.markdown("---")

    st.subheader(t("models"))
    st.session_state["default_model"] = st.selectbox(t("default_model"), ALL_MODELS, index=ALL_MODELS.index(st.session_state["default_model"]) if st.session_state["default_model"] in ALL_MODELS else 0)
    st.session_state["default_max_tokens"] = st.number_input(t("max_tokens"), min_value=256, max_value=64000, value=int(st.session_state["default_max_tokens"]), step=256)
    st.session_state["default_temperature"] = st.slider(t("temperature"), min_value=0.0, max_value=1.0, value=float(st.session_state["default_temperature"]), step=0.05)

    st.markdown("---")
    st.subheader(t("provider_keys"))

    def key_panel(provider: str, label: str) -> None:
        env_var = env_key_for_provider(provider)
        key, source = get_api_key(provider)
        st.caption(f"{label} ({provider}) — env: {env_var or 'N/A'}")
        if source == "env":
            st.success(t("managed_env"))
        elif source == "session":
            st.info("Session key set")
            if st.button(f"{t('clear_key')} — {provider}", key=f"clear_{provider}"):
                st.session_state["session_keys"].pop(provider, None)
                log_event("keys", "info", "session_key_cleared", f"Cleared session key for {provider}")
        else:
            st.warning(t("missing_key"))
            new_key = st.text_input(t("enter_key"), type="password", key=f"key_{provider}")
            # Bugfix: only set when user actually enters something non-empty
            if new_key and new_key.strip():
                st.session_state["session_keys"][provider] = new_key.strip()
                log_event("keys", "info", "session_key_set", f"Session key set for {provider}")

    key_panel("openai", "OpenAI")
    key_panel("gemini", "Gemini")
    key_panel("anthropic", "Anthropic")
    key_panel("grok", "Grok / xAI")

    st.markdown("---")
    with st.expander("agents.yaml (optional override)", expanded=False):
        st.caption("If empty, built-in defaults are used. You can paste or upload YAML content.")
        upload = st.file_uploader("Upload agents.yaml", type=["yaml", "yml"], accept_multiple_files=False)
        if upload is not None:
            try:
                st.session_state["agents_yaml_text"] = upload.read().decode("utf-8", errors="replace")
                refresh_agents()
                st.success("Loaded agents.yaml from upload.")
            except Exception as e:
                st.error(f"Failed to load upload: {e}")

        st.session_state["agents_yaml_text"] = st.text_area("agents.yaml text", value=st.session_state["agents_yaml_text"], height=220)
        if st.button("Reload agents"):
            refresh_agents()
            st.success("Agents reloaded.")


# -----------------------------
# Header / WOW Indicator
# -----------------------------
def wow_indicator() -> None:
    active = st.session_state.get("active_run_id")
    if active:
        st.markdown(f"<div class='wow-panel'><span class='wow-badge'>RUNNING</span> <span class='wow-accent'>run_id</span>: <code>{active}</code></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='wow-panel'><span class='wow-badge'>IDLE</span> <span class='wow-accent'>{t('app_title')}</span></div>", unsafe_allow_html=True)


wow_indicator()


# -----------------------------
# Shared UI Helpers
# -----------------------------
def artifact_editor(title: str, raw_key: str, effective_key: str) -> None:
    st.markdown(f"### {title}")

    raw = st.session_state.get(raw_key, "") or ""
    effective = st.session_state.get(effective_key, "") or raw

    # Two widget states (do NOT write both tabs into the same key on every rerun)
    md_widget_key = f"{effective_key}__md_widget"
    txt_widget_key = f"{effective_key}__txt_widget"

    # Initialize widgets only if not present (prevents old empty widget values from overriding)
    if md_widget_key not in st.session_state:
        st.session_state[md_widget_key] = effective
    if txt_widget_key not in st.session_state:
        st.session_state[txt_widget_key] = effective

    tab_md, tab_txt = st.tabs([t("markdown_view"), t("text_view")])

    with tab_md:
        st.caption(t("edit_output"))
        st.text_area("Markdown", key=md_widget_key, height=420)
        st.markdown("**Preview**")
        st.markdown(st.session_state[md_widget_key], unsafe_allow_html=True)

    with tab_txt:
        st.caption(t("edit_output"))
        st.text_area("Text", key=txt_widget_key, height=420)

    # Decide which one should become the effective output (simple rule: prefer markdown widget)
    st.session_state[effective_key] = st.session_state[md_widget_key]


def download_buttons(label_prefix: str, content: str, filename_base: str) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"{label_prefix} .md",
            data=(content or "").encode("utf-8"),
            file_name=f"{filename_base}.md",
            mime="text/markdown",
        )
    with col2:
        st.download_button(
            label=f"{label_prefix} .txt",
            data=(content or "").encode("utf-8"),
            file_name=f"{filename_base}.txt",
            mime="text/plain",
        )


def save_artifact(name: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Artifact name is empty.")
    st.session_state["artifacts"][name] = content or ""
    st.session_state["artifact_meta"][name] = meta or {}
    log_event("artifacts", "info", "artifact_saved", f"Saved artifact: {name}", extra={"meta": meta or {}})


def list_artifacts() -> List[str]:
    return sorted(st.session_state.get("artifacts", {}).keys())


# -----------------------------
# Prompt Builders (510k + Note + Magics)
# -----------------------------
def run_agent_like(
    module: str,
    title: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    run_id = begin_run(module=module, title=title, model=model, params={"max_tokens": max_tokens, "temperature": temperature})
    t0 = time.time()
    try:
        log_event(module, "info", "preflight", "Preflight OK", run_id=run_id, extra={"provider": model_to_provider(model)})
        out = call_llm(model, system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature)
        dt_s = time.time() - t0
        end_run(run_id, "success", metrics={"duration_s": round(dt_s, 2)})
        return out
    except Exception as e:
        dt_s = time.time() - t0
        log_event(module, "error", "exception", str(e), run_id=run_id)
        end_run(run_id, "error", metrics={"duration_s": round(dt_s, 2)})
        raise


def build_note_magic_prompts() -> Dict[str, Dict[str, str]]:
    """
    9 magics total (6 original + 3 new). Each returns {system,user_template}
    """
    coral = PAINTER_STYLES.get(st.session_state["painter_style"], PAINTER_STYLES[DEFAULT_STYLE])["coral"]
    kw_style = f"<span style='color:{coral};font-weight:700'>{{kw}}</span>"

    base_system = (
        "You are a precise assistant. Do not invent facts. Keep original meaning. "
        "Output Markdown. Highlight key terms inline using HTML spans in coral color."
    )

    return {
        "Executive Summary Builder": {
            "system": base_system,
            "user": "Create an executive summary (1 page max) + key points + next steps from the note:\n\n---\n{note}\n---",
        },
        "Action Items Extractor": {
            "system": base_system,
            "user": "Extract action items with fields: Task, Owner (if stated), Due date (if stated), Priority, Source line/section. Use Markdown:\n\n---\n{note}\n---",
        },
        "Risk & Mitigation Draft": {
            "system": base_system,
            "user": "Identify risks and propose mitigations. Label uncertainty explicitly. Output Markdown with a small risk table:\n\n---\n{note}\n---",
        },
        "Meeting Minutes Formatter": {
            "system": base_system,
            "user": "Format as meeting minutes: Attendees (if stated), Agenda, Discussion, Decisions, Action items, Open questions:\n\n---\n{note}\n---",
        },
        "Regulatory Checklist Generator": {
            "system": base_system,
            "user": "Convert note into a practical checklist. Include evidence expectations if mentioned; do not invent. Output Markdown:\n\n---\n{note}\n---",
        },
        "Keyword Highlighter/Refiner": {
            "system": base_system,
            "user": f"Refine and highlight keywords inline using coral spans like {kw_style}. Also include a 'Keywords' section listing them.\n\n---\n{{note}}\n---",
        },
        # New 3 (from 4.2)
        "Traceability Matrix Builder (Notes → Evidence Map)": {
            "system": base_system,
            "user": "Create a traceability matrix mapping claim/requirement/question to suggested evidence type and status (unknown/needs confirmation/ready). Do not fabricate evidence.\n\n---\n{note}\n---",
        },
        "Contradiction & Ambiguity Detector": {
            "system": base_system,
            "user": "Identify contradictions, ambiguities, and missing definitions. Provide clarifying questions. Output Markdown:\n\n---\n{note}\n---",
        },
        "Regulatory-Ready Rewrite (Localized Tone)": {
            "system": base_system,
            "user": "Produce two rewrites: (1) Regulatory formal, (2) Internal actionable. Preserve facts. Output Markdown:\n\n---\n{note}\n---",
        },
    }


# -----------------------------
# Main Tabs
# -----------------------------
tab_dashboard, tab_log, tab_builder, tab_agent, tab_note = st.tabs(
    [t("dashboard"), t("live_log"), t("builder"), t("agent_studio"), t("note_keeper")]
)


# -----------------------------
# Dashboard Tab
# -----------------------------
with tab_dashboard:
    st.markdown("<div class='wow-panel'>", unsafe_allow_html=True)
    st.subheader(t("dashboard"))

    runs = st.session_state.get("runs", [])
    events = st.session_state.get("events", [])

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Total runs", len(runs))
    colB.metric("Success", sum(1 for r in runs if r.get("status") == "success"))
    colC.metric("Errors", sum(1 for r in runs if r.get("status") == "error"))
    colD.metric("Warnings (events)", sum(1 for e in events if e.get("severity") == "warn"))

    st.markdown("#### Run Timeline (table)")
    if runs:
        df_runs = pd.DataFrame(runs)
        # Bugfix: ensure columns exist even if missing
        show_cols = [c for c in ["ts_start_utc", "ts_end_utc", "module", "title", "model", "provider", "status"] if c in df_runs.columns]
        st.dataframe(df_runs[show_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No runs yet.")

    st.markdown("#### Model / Provider Mix")
    if runs:
        df = pd.DataFrame(runs)
        mix_model = df["model"].value_counts().reset_index()
        mix_model.columns = ["model", "count"]
        mix_provider = df["provider"].value_counts().reset_index()
        mix_provider.columns = ["provider", "count"]
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(mix_model, use_container_width=True, hide_index=True)
        with c2:
            st.dataframe(mix_provider, use_container_width=True, hide_index=True)

    st.markdown("#### Artifact Quick Access")
    arts = list_artifacts()
    if arts:
        pick = st.selectbox(t("select_artifact"), arts, index=0)
        st.caption(f"Artifact: {pick}")
        st.text_area("Artifact content (read-only preview)", value=st.session_state["artifacts"].get(pick, ""), height=220, disabled=True)
    else:
        st.info("No artifacts saved yet.")

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Live Log Tab
# -----------------------------
with tab_log:
    st.markdown("<div class='wow-panel'>", unsafe_allow_html=True)
    st.subheader(t("live_log"))

    events = st.session_state.get("events", [])
    if not events:
        st.info("No events yet.")
    else:
        df = pd.DataFrame(events)

        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            st.session_state["log_filter_run_id"] = st.text_input("Filter by run_id", value=st.session_state["log_filter_run_id"])
        with f2:
            mods = ["All"] + sorted(list(set(df["module"].tolist())))
            st.session_state["log_filter_module"] = st.selectbox("Module", mods, index=mods.index(st.session_state["log_filter_module"]) if st.session_state["log_filter_module"] in mods else 0)
        with f3:
            sevs = ["All", "info", "warn", "error"]
            st.session_state["log_filter_severity"] = st.selectbox("Severity", sevs, index=sevs.index(st.session_state["log_filter_severity"]) if st.session_state["log_filter_severity"] in sevs else 0)

        filt = df
        if st.session_state["log_filter_run_id"].strip():
            filt = filt[filt["run_id"].str.contains(st.session_state["log_filter_run_id"].strip(), na=False)]
        if st.session_state["log_filter_module"] != "All":
            filt = filt[filt["module"] == st.session_state["log_filter_module"]]
        if st.session_state["log_filter_severity"] != "All":
            filt = filt[filt["severity"] == st.session_state["log_filter_severity"]]

        st.dataframe(filt[["ts_utc", "run_id", "module", "severity", "event_type", "message"]], use_container_width=True, hide_index=True)

        # Export buttons
        jsonl = "\n".join(json.dumps(ev, ensure_ascii=False) for ev in events)
        txt = "\n".join(f"[{ev['ts_utc']}] {ev['severity'].upper()} {ev['module']} {ev['event_type']}: {ev['message']}" for ev in events)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(t("export_jsonl"), data=jsonl.encode("utf-8"), file_name="live_log.jsonl", mime="application/jsonl")
        with c2:
            st.download_button(t("export_txt"), data=txt.encode("utf-8"), file_name="live_log.txt", mime="text/plain")

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# 510(k) Guidance Builder Tab
# -----------------------------
with tab_builder:
    st.markdown("<div class='wow-panel'>", unsafe_allow_html=True)
    st.subheader(t("builder"))

    # Input document
    st.markdown("#### 1) Paste 510(k) submission summary / review note / guidance (TXT/Markdown)")
    st.session_state["k510_input_doc"] = st.text_area(
        "510(k) input",
        value=st.session_state["k510_input_doc"],
        height=220,
        placeholder="Paste here...",
    )

    # Controls for step A
    st.markdown("#### Controls (Step A)")
    a1, a2, a3 = st.columns(3)
    with a1:
        model_A = st.selectbox("Model (A)", ALL_MODELS, index=ALL_MODELS.index(st.session_state["default_model"]) if st.session_state["default_model"] in ALL_MODELS else 0, key="model_A")
    with a2:
        max_tokens_A = st.number_input("Max tokens (A)", min_value=256, max_value=64000, value=int(st.session_state["default_max_tokens"]), step=256, key="max_tokens_A")
    with a3:
        temp_A = st.slider("Temperature (A)", min_value=0.0, max_value=1.0, value=float(st.session_state["default_temperature"]), step=0.05, key="temp_A")

    # Run Step A
    if st.button(t("generate_organized")):
        try:
            if not st.session_state["k510_input_doc"].strip():
                st.error("Input doc is empty.")
            else:
                agent = next(a for a in st.session_state["agents_loaded"] if a.name == "k510-organize-doc")
                user_prompt = agent.user_prompt_template.format(input_text=st.session_state["k510_input_doc"])
                out = run_agent_like(
                    module="510k",
                    title="510(k) Organized Document (A)",
                    model=model_A,
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=int(max_tokens_A),
                    temperature=float(temp_A),
                )
                st.session_state["k510_output_A_raw"] = out
                st.session_state["k510_output_A_effective"] = out
                st.session_state["k510_output_A_effective__md_widget"] = out
                st.session_state["k510_output_A_effective__txt_widget"] = out
                st.rerun()
                save_artifact("510k_organized_doc_A.md", out, meta={"type": "510k_output_A", "model": model_A})
                attach_artifact_to_run(st.session_state["runs"][-1]["run_id"], "510k_organized_doc_A.md")
                st.success("Generated Output A.")
        except Exception as e:
            st.error(str(e))

    st.markdown("---")
    artifact_editor(
        title=t("organized_doc"),
        raw_key="k510_output_A_raw",
        effective_key="k510_output_A_effective",
    )
    download_buttons(t("download"), st.session_state.get("k510_output_A_effective", ""), "510k_organized_doc_A")

    st.markdown("---")
    st.markdown("#### 2) Choose or paste review guidance template")

    mode = st.radio(
        t("template"),
        options=["default", "paste", "describe"],
        index=["default", "paste", "describe"].index(st.session_state["k510_template_mode"]),
        horizontal=True,
        key="k510_template_mode",
    )

    if mode == "default":
        st.info("Using default template (provided).")
        st.session_state["k510_template_paste"] = DEFAULT_TEMPLATE_ZH
        template_text = DEFAULT_TEMPLATE_ZH
    elif mode == "paste":
        st.session_state["k510_template_paste"] = st.text_area(
            t("paste_template"),
            value=st.session_state["k510_template_paste"],
            height=220,
        )
        template_text = st.session_state["k510_template_paste"]
    else:
        st.session_state["k510_template_desc"] = st.text_area(
            t("describe_template"),
            value=st.session_state["k510_template_desc"],
            height=160,
        )
        template_text = st.session_state["k510_template_desc"]

    # Template normalization controls
    st.markdown("#### Controls (Template Outline)")
    o1, o2, o3 = st.columns(3)
    with o1:
        model_T = st.selectbox("Model (Template)", ALL_MODELS, index=ALL_MODELS.index("gpt-4o-mini") if "gpt-4o-mini" in ALL_MODELS else 0, key="model_T")
    with o2:
        max_tokens_T = st.number_input("Max tokens (Template)", min_value=256, max_value=64000, value=4096, step=256, key="max_tokens_T")
    with o3:
        temp_T = st.slider("Temperature (Template)", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="temp_T")

    if st.button("Generate/Refresh Template Outline"):
        try:
            agent = next(a for a in st.session_state["agents_loaded"] if a.name == "k510-normalize-template")
            prompt = agent.user_prompt_template.format(input_text=template_text)
            outline = run_agent_like(
                module="510k",
                title="Template Outline",
                model=model_T,
                system_prompt=agent.system_prompt,
                user_prompt=prompt,
                max_tokens=int(max_tokens_T),
                temperature=float(temp_T),
            )
            st.session_state["k510_template_outline"] = outline
            save_artifact("510k_template_outline.md", outline, meta={"type": "template_outline", "model": model_T, "mode": mode})
            attach_artifact_to_run(st.session_state["runs"][-1]["run_id"], "510k_template_outline.md")
            st.success("Template outline created.")
        except Exception as e:
            st.error(str(e))

    st.markdown("#### Template Outline (editable)")
    st.session_state["k510_template_outline"] = st.text_area(
        "Template outline",
        value=st.session_state["k510_template_outline"],
        height=220,
        placeholder="Generate outline or paste/edit here...",
    )

    # Controls for step B
    st.markdown("#### Controls (Step B)")
    b1, b2, b3 = st.columns(3)
    with b1:
        model_B = st.selectbox("Model (B)", ALL_MODELS, index=ALL_MODELS.index(st.session_state["default_model"]) if st.session_state["default_model"] in ALL_MODELS else 0, key="model_B")
    with b2:
        max_tokens_B = st.number_input("Max tokens (B)", min_value=256, max_value=64000, value=int(st.session_state["default_max_tokens"]), step=256, key="max_tokens_B")
    with b3:
        temp_B = st.slider("Temperature (B)", min_value=0.0, max_value=1.0, value=float(st.session_state["default_temperature"]), step=0.05, key="temp_B")

    if st.button(t("generate_guidance")):
        try:
            organized = st.session_state.get("k510_output_A_effective", "").strip()
            outline = st.session_state.get("k510_template_outline", "").strip()
            if not organized:
                st.error("Output A is empty. Generate or paste Organized Document first.")
            elif not outline:
                st.error("Template Outline is empty. Generate or paste an outline first.")
            else:
                agent = next(a for a in st.session_state["agents_loaded"] if a.name == "k510-generate-review-guidance")
                user_prompt = agent.user_prompt_template.format(template_outline=outline, organized_doc=organized)
                outB = run_agent_like(
                    module="510k",
                    title="510(k) Review Guidance (B)",
                    model=model_B,
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=int(max_tokens_B),
                    temperature=float(temp_B),
                )
                st.session_state["k510_output_B_raw"] = outB
                st.session_state["k510_output_B_effective"] = outB
                save_artifact("510k_review_guidance_B.md", outB, meta={"type": "510k_output_B", "model": model_B})
                attach_artifact_to_run(st.session_state["runs"][-1]["run_id"], "510k_review_guidance_B.md")
                st.success("Generated Output B.")
        except Exception as e:
            st.error(str(e))

    st.markdown("---")
    artifact_editor(
        title=t("review_guidance"),
        raw_key="k510_output_B_raw",
        effective_key="k510_output_B_effective",
    )
    download_buttons(t("download"), st.session_state.get("k510_output_B_effective", ""), "510k_review_guidance_B")

    st.markdown("---")
    st.markdown("#### 3) Generate SKILL.md (skill-creator style)")

    c1, c2, c3 = st.columns(3)
    with c1:
        model_C = st.selectbox("Model (C)", ALL_MODELS, index=ALL_MODELS.index("gpt-4o-mini") if "gpt-4o-mini" in ALL_MODELS else 0, key="model_C")
    with c2:
        max_tokens_C = st.number_input("Max tokens (C)", min_value=256, max_value=64000, value=8192, step=256, key="max_tokens_C")
    with c3:
        temp_C = st.slider("Temperature (C)", min_value=0.0, max_value=1.0, value=0.2, step=0.05, key="temp_C")

    if st.button(t("generate_skill")):
        try:
            guidance = st.session_state.get("k510_output_B_effective", "").strip()
            if not guidance:
                st.error("Output B is empty. Generate Review Guidance first.")
            else:
                agent = next(a for a in st.session_state["agents_loaded"] if a.name == "skill-md-generator")
                user_prompt = agent.user_prompt_template.format(input_text=guidance)
                skill_md = run_agent_like(
                    module="skill",
                    title="SKILL.md generation",
                    model=model_C,
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=int(max_tokens_C),
                    temperature=float(temp_C),
                )
                st.session_state["k510_skill_md_raw"] = skill_md
                st.session_state["k510_skill_md_effective"] = skill_md
                save_artifact("SKILL.md", skill_md, meta={"type": "skill_md", "model": model_C})
                attach_artifact_to_run(st.session_state["runs"][-1]["run_id"], "SKILL.md")
                st.success("Generated SKILL.md.")
        except Exception as e:
            st.error(str(e))

    st.markdown("#### SKILL.md (editable)")
    st.session_state["k510_skill_md_effective"] = st.text_area(
        t("skill_md"),
        value=st.session_state.get("k510_skill_md_effective", ""),
        height=420,
    )
    download_buttons(t("download"), st.session_state.get("k510_skill_md_effective", ""), "SKILL")

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Agent Studio Tab
# -----------------------------
with tab_agent:
    st.markdown("<div class='wow-panel'>", unsafe_allow_html=True)
    st.subheader(t("agent_studio"))

    agents = st.session_state.get("agents_loaded", []) or default_agents()
    agent_names = [a.name for a in agents]
    selected = st.selectbox("Select agent", agent_names, index=agent_names.index(st.session_state["agent_selected_name"]) if st.session_state["agent_selected_name"] in agent_names else 0)
    st.session_state["agent_selected_name"] = selected
    agent = next(a for a in agents if a.name == selected)

    st.caption(agent.description)

    # Input selection
    st.markdown("#### Input")
    artifacts = list_artifacts()
    left, right = st.columns([2, 1])
    with right:
        input_source = st.radio("Input source", ["Paste", "Artifact"], horizontal=True)
    with left:
        if input_source == "Artifact" and artifacts:
            pick = st.selectbox(t("select_artifact"), artifacts, index=0)
            input_text = st.session_state["artifacts"].get(pick, "")
        elif input_source == "Artifact" and not artifacts:
            st.warning("No artifacts available; paste instead.")
            input_text = st.text_area("Agent input", value="", height=180)
        else:
            input_text = st.text_area("Agent input", value="", height=180)

    # Prompt editors (system + user template)
    st.markdown("#### Prompt (editable)")
    overrides = st.session_state["agent_prompt_overrides"].get(agent.name, {})
    sys_prompt = st.text_area("System prompt", value=overrides.get("system", agent.system_prompt), height=120)
    user_tmpl = st.text_area("User prompt template", value=overrides.get("user", agent.user_prompt_template), height=220)
    st.session_state["agent_prompt_overrides"][agent.name] = {"system": sys_prompt, "user": user_tmpl}

    # Model/params
    st.markdown("#### Execution controls")
    p1, p2, p3 = st.columns(3)
    with p1:
        model = st.selectbox("Model", ALL_MODELS, index=ALL_MODELS.index(agent.default_model) if agent.default_model in ALL_MODELS else ALL_MODELS.index(st.session_state["default_model"]))
    with p2:
        max_tokens = st.number_input("Max tokens", min_value=256, max_value=64000, value=int(agent.default_max_tokens), step=256)
    with p3:
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(agent.default_temperature), step=0.05)

    # Run agent
    if st.button(t("run")):
        try:
            # Bugfix: format placeholders robustly
            try:
                user_prompt = user_tmpl.format(input_text=input_text)
            except KeyError:
                # If template expects different fields, fallback to append
                user_prompt = user_tmpl + "\n\n---\n" + input_text + "\n---"

            out = run_agent_like(
                module="agent_studio",
                title=f"Agent: {agent.name}",
                model=model,
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                max_tokens=int(max_tokens),
                temperature=float(temperature),
            )
            st.session_state["agent_output_raw"][agent.name] = out
            st.session_state["agent_output_effective"][agent.name] = out
            st.success("Agent completed.")
        except Exception as e:
            st.error(str(e))

    # Output editor
    st.markdown("#### Output (editable chaining)")
    raw_out = st.session_state["agent_output_raw"].get(agent.name, "")
    eff_out = st.session_state["agent_output_effective"].get(agent.name, raw_out)

    out_tab_md, out_tab_txt = st.tabs([t("markdown_view"), t("text_view")])
    with out_tab_md:
        st.session_state["agent_output_effective"][agent.name] = st.text_area("Markdown output", value=eff_out, height=320)
        st.markdown("**Preview**")
        st.markdown(st.session_state["agent_output_effective"][agent.name], unsafe_allow_html=True)
    with out_tab_txt:
        st.session_state["agent_output_effective"][agent.name] = st.text_area("Text output", value=eff_out, height=320)

    st.markdown("#### Save output as artifact")
    an1, an2 = st.columns([2, 1])
    with an1:
        artifact_name = st.text_input(t("artifact_name"), value=f"{agent.name}_output.md")
    with an2:
        if st.button(t("save_as_artifact")):
            try:
                save_artifact(artifact_name, st.session_state["agent_output_effective"].get(agent.name, ""))
                st.success(f"Saved artifact: {artifact_name}")
            except Exception as e:
                st.error(str(e))

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# AI Note Keeper Tab
# -----------------------------
with tab_note:
    st.markdown("<div class='wow-panel'>", unsafe_allow_html=True)
    st.subheader(t("note_keeper"))

    st.markdown("#### Note input")
    st.session_state["note_input"] = st.text_area(
        t("note_input"),
        value=st.session_state["note_input"],
        height=220,
        placeholder="Paste notes here...",
    )

    st.markdown("#### Controls")
    n1, n2, n3 = st.columns(3)
    with n1:
        note_model = st.selectbox("Model (note)", ALL_MODELS, index=ALL_MODELS.index("gpt-4o-mini") if "gpt-4o-mini" in ALL_MODELS else 0)
    with n2:
        note_max_tokens = st.number_input("Max tokens (note)", min_value=256, max_value=64000, value=4096, step=256)
    with n3:
        note_temp = st.slider("Temperature (note)", min_value=0.0, max_value=1.0, value=0.2, step=0.05)

    # Organize note
    if st.button(t("organize_note")):
        try:
            if not st.session_state["note_input"].strip():
                st.error("Note input is empty.")
            else:
                agent = next(a for a in st.session_state["agents_loaded"] if a.name == "note-organizer")
                user_prompt = agent.user_prompt_template.format(input_text=st.session_state["note_input"])
                out = run_agent_like(
                    module="note_keeper",
                    title="Note organization",
                    model=note_model,
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=int(note_max_tokens),
                    temperature=float(note_temp),
                )
                st.session_state["note_output_raw"] = out
                st.session_state["note_output_effective"] = out
                save_artifact("note_organized.md", out, meta={"type": "note", "model": note_model})
                attach_artifact_to_run(st.session_state["runs"][-1]["run_id"], "note_organized.md")
                st.success("Note organized.")
        except Exception as e:
            st.error(str(e))

    st.markdown("#### Note output (editable)")
    note_tab_md, note_tab_txt = st.tabs([t("markdown_view"), t("text_view")])
    with note_tab_md:
        st.session_state["note_output_effective"] = st.text_area("Markdown note", value=st.session_state.get("note_output_effective", ""), height=320)
        st.markdown("**Preview**")
        st.markdown(st.session_state["note_output_effective"], unsafe_allow_html=True)
    with note_tab_txt:
        st.session_state["note_output_effective"] = st.text_area("Text note", value=st.session_state.get("note_output_effective", ""), height=320)

    download_buttons(t("download"), st.session_state.get("note_output_effective", ""), "note_organized")

    st.markdown("---")
    st.markdown(f"#### {t('ai_magics')} (9)")

    magics = build_note_magic_prompts()
    magic_names = list(magics.keys())

    m1, m2 = st.columns([2, 1])
    with m1:
        magic_name = st.selectbox("Select magic", magic_names, index=0)
    with m2:
        magic_model = st.selectbox("Model (magic)", ALL_MODELS, index=ALL_MODELS.index(st.session_state["default_model"]) if st.session_state["default_model"] in ALL_MODELS else 0)

    mm1, mm2, mm3 = st.columns(3)
    with mm1:
        magic_max_tokens = st.number_input("Max tokens (magic)", min_value=256, max_value=64000, value=4096, step=256)
    with mm2:
        magic_temp = st.slider("Temperature (magic)", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
    with mm3:
        export_magic_as = st.text_input("Save magic as artifact name", value=f"note_magic_{re.sub(r'[^a-zA-Z0-9_]+','_', magic_name)[:40]}.md")

    if st.button(t("apply_magic")):
        try:
            note = st.session_state.get("note_output_effective") or st.session_state.get("note_input") or ""
            if not note.strip():
                st.error("No note content available.")
            else:
                p = magics[magic_name]
                sys_p = p["system"]
                user_p = p["user"].format(note=note)
                out = run_agent_like(
                    module="note_keeper",
                    title=f"Magic: {magic_name}",
                    model=magic_model,
                    system_prompt=sys_p,
                    user_prompt=user_p,
                    max_tokens=int(magic_max_tokens),
                    temperature=float(magic_temp),
                )
                st.markdown("#### Magic output")
                st.text_area("Magic output (editable)", value=out, height=260)
                save_artifact(export_magic_as, out, meta={"type": "note_magic", "magic": magic_name, "model": magic_model})
                attach_artifact_to_run(st.session_state["runs"][-1]["run_id"], export_magic_as)
                st.success("Magic applied and saved as artifact.")
        except Exception as e:
            st.error(str(e))

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Footer: Quick Tips / Safety
# -----------------------------
st.markdown(
    "<div class='wow-panel'>"
    "<div class='wow-accent'>Operational Notes</div>"
    "<ul>"
    "<li>API keys are environment-first; UI keys are session-only and never shown if managed by environment.</li>"
    "<li>Constraints (tables/entities/length) are validated heuristically; use regeneration hints when needed.</li>"
    "<li>For confidential content, download artifacts promptly—HF Spaces may restart and clear session state.</li>"
    "</ul>"
    "</div>",
    unsafe_allow_html=True,
)
