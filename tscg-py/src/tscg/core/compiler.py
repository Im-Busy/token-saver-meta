"""
TSCG Compiler — pipeline orchestrator with safety guards.

Applies transforms from tscg.core.transforms in order based on:
  - Profile gating (conservative / balanced / aggressive)
  - Safety guard 1: non-Claude model → CFL+SAD disabled
  - Safety guard 2: >=30 tools → CFL+CFO disabled
  - Safety guard 3: auto-profile by tool count
  - Thinking model exclusion: o1, o3, R1 → CFL+SAD disabled
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .transforms import ToolDef, ParamDef, optimize_tool_definitions


# ── CompiledSchema ───────────────────────────────────────────────


@dataclass
class CompiledSchema:
    """Result of a compilation pass.

    Attributes:
        compressed_text: The compressed tool schema text.
        savings_pct: Estimated token savings percentage (0.0-100.0).
        active_transforms: Names of transforms applied, in pipeline order.
        tool_count: Number of tools compressed.
    """

    compressed_text: str
    savings_pct: float
    active_transforms: list[str]
    tool_count: int


# ── Pipeline order ───────────────────────────────────────────────

_PIPELINE_ORDER: tuple[str, ...] = (
    "sdm", "cas", "cfo", "dro", "tas", "cfl", "ccp", "sad",
)

# Profile → transform enable map.
_PROFILE_TRANSFORMS: dict[str, set[str]] = {
    "conservative": {"sdm"},
    "balanced": {"sdm", "cas", "cfo", "dro", "tas"},
    "aggressive": {"sdm", "cas", "cfo", "dro", "tas", "cfl", "ccp", "sad"},
}


# ══════════════════════════════════════════════════════════════════
# TSCGCompiler
# ══════════════════════════════════════════════════════════════════


class TSCGCompiler:
    """Pipeline orchestrator with 3 critical safety guards.

    Usage:
        compiler = TSCGCompiler(model="claude-3.5-sonnet", profile="balanced")
        result = compiler.compile(tools)
        restored = compiler.decompile(result.compressed_text)
    """

    def __init__(
        self,
        model: str = "auto",
        profile: str | None = None,
    ) -> None:
        """Create a compiler for the given model.

        Args:
            model: Model identifier string. "auto" defaults to Claude-like behavior
                   (CFL+SAD supported). Used to detect model family for safety guards.
            profile: Explicit profile name ("conservative", "balanced", "aggressive").
                     When None (default), auto-detects based on tool count
                     (safety guard 3).
        """
        self.model = model
        self._profile_arg = profile  # None → auto-detect
        self._last_active_transforms: list[str] = []
        self._last_savings: float = 0.0

    # ── Public API ──────────────────────────────────────────────

    def compile(self, tools: list[ToolDef]) -> CompiledSchema:
        """Compress tool definitions through the transform pipeline.

        Args:
            tools: List of tool definitions to compress.

        Returns:
            CompiledSchema with compressed text, savings, active transforms, and count.
        """
        tool_count = len(tools)
        if tool_count == 0:
            self._last_active_transforms = []
            self._last_savings = 0.0
            return CompiledSchema("", 0.0, [], 0)

        profile = self._resolve_profile(tool_count)
        transform_flags = self._resolve_transforms(profile, tool_count)

        result = optimize_tool_definitions(
            tools,
            useSDM=transform_flags["sdm"],
            useCAS=transform_flags["cas"],
            useCFO=transform_flags["cfo"],
            useDRO=transform_flags["dro"],
            useTAS=transform_flags["tas"],
            useCFL=transform_flags["cfl"],
            useCCP=transform_flags["ccp"],
            useSAD=transform_flags["sad"],
        )

        active = [t for t in _PIPELINE_ORDER if transform_flags[t]]
        self._last_active_transforms = active
        self._last_savings = result.savingsPercent

        return CompiledSchema(
            compressed_text=result.text,
            savings_pct=result.savingsPercent,
            active_transforms=active,
            tool_count=tool_count,
        )

    def decompile(self, text: str) -> list[ToolDef]:
        """Parse compressed DRO-format text back to tool definitions.

        Best-effort recovery: descriptions are compressed by SDM and cannot
        be restored to original verbatim form.

        Strips CFL ([ANSWER:function_call]), CCP ([CLOSURE:...]),
        and SAD ([ANCHOR:...]) markers before parsing.

        Args:
            text: Compressed text from a previous compile() call.

        Returns:
            List of ToolDef objects recovered from the compressed text.
        """
        if not text.strip():
            return []

        # Strip CFL / CCP / SAD markers (safety: handle any order)
        cleaned = text
        cleaned = re.sub(r"^\[ANSWER:function_call\]\n", "", cleaned)
        cleaned = re.sub(r"\n\[CLOSURE:[^\]]*\]$", "", cleaned)
        cleaned = re.sub(r"\n\[ANCHOR:[^\]]*\]$", "", cleaned)

        tools: list[ToolDef] = []
        lines = cleaned.split("\n")
        current_block: list[str] = []

        for line in lines:
            # Tool blocks start with "Name: " at column 0 (no leading whitespace)
            if re.match(r"^\w[\w.]*:", line) and not line.startswith(" "):
                if current_block:
                    tools.append(self._parse_tool_block(current_block))
                current_block = [line]
            elif current_block:
                current_block.append(line)

        if current_block:
            tools.append(self._parse_tool_block(current_block))

        return tools

    @property
    def active_transforms(self) -> list[str]:
        """Names of transforms applied by the last compile(), in pipeline order.
        Returns empty list if compile() has not been called.
        """
        return list(self._last_active_transforms)

    @property
    def estimated_savings(self) -> float:
        """Token savings percentage from the last compile().
        Returns 0.0 if compile() has not been called.
        """
        return self._last_savings

    # ── Profile resolution ──────────────────────────────────────

    def _resolve_profile(self, tool_count: int) -> str:
        """Resolve profile: manual override wins, else auto-detect by tool count.

        Safety guard 3: auto-profile by tool count.
          - <=20: conservative
          - <=40: balanced
          - >40 : conservative (too many tools → keep it simple)
        """
        if self._profile_arg is not None:
            return self._profile_arg
        # Auto-detect
        if tool_count <= 20:
            return "conservative"
        if tool_count <= 40:
            return "balanced"
        return "conservative"

    def _resolve_transforms(
        self, profile: str, tool_count: int
    ) -> dict[str, bool]:
        """Build transform enable map with all safety guards applied.

        Guards applied in order:
          1. Profile-gated baseline
          2. Guard 1: non-Claude model → CFL+SAD disabled
          3. Thinking model exclusion → CFL+SAD disabled
          4. Guard 2: >=30 tools → CFL+CFO disabled
        """
        enabled = _PROFILE_TRANSFORMS.get(profile, _PROFILE_TRANSFORMS["conservative"])
        transforms: dict[str, bool] = {t: t in enabled for t in _PIPELINE_ORDER}

        # ── Guard 1: non-Claude model → CFL+SAD disabled ───────
        # Guard 1 also covers thinking model exclusion (o1, o3, R1)
        supports_cfl, supports_sad = self._get_model_support()
        if not supports_cfl:
            transforms["cfl"] = False
        if not supports_sad:
            transforms["sad"] = False

        # ── Guard 2: >=30 tools → CFL+CFO disabled ─────────────
        if tool_count >= 30:
            transforms["cfl"] = False
            transforms["cfo"] = False

        return transforms

    def _get_model_support(self) -> tuple[bool, bool]:
        """Return (supports_cfl, supports_sad) for the configured model.

        Safety guard 1: Only Claude models get CFL+SAD. All other families
        (GPT, Gemini, LLama, DeepSeek, etc.) get CFL+SAD disabled regardless
        of what their Profile says — the guard is a hard override.

        "auto" model → treated as Claude-like (True, True).
        Thinking models (o1, o3, R1) → always (False, False).
        """
        if self.model == "auto":
            # "auto" defaults to Claude-like: full CFL+SAD support
            return True, True

        from .profiles import detect_model_family, is_thinking_model, ModelFamily

        if is_thinking_model(self.model):
            return False, False

        family = detect_model_family(self.model)
        if family == ModelFamily.CLAUDE:
            return True, True

        # Safety guard 1: non-Claude → CFL+SAD disabled
        return False, False

    # ── Decompile helpers ───────────────────────────────────────

    @staticmethod
    def _parse_tool_block(lines: list[str]) -> ToolDef:
        """Parse a single DRO-format tool block into a ToolDef.

        First line: "Name: description"
        Subsequent lines: "  param* (type): desc | param (type): desc"
        """
        first = lines[0]
        m = re.match(r"^(\w[\w.]*):\s*(.*)", first)
        if not m:
            return ToolDef(name="unknown", description="")
        name = m.group(1)
        description = m.group(2).strip()

        params: list[ParamDef] = []
        param_text = "\n".join(lines[1:])

        if param_text.strip():
            # Each param field: name*? (type_abbrev[:enum|...]): description
            # Fields separated by " | " (TAS-normalized). Match boundaries
            # by looking ahead for the next param start pattern.
            param_re = (
                r"(\w[\w.]*)(\*?)\s*\(([^)]+)\):\s*"
                r"(.+?)"  # non-greedy description
                r"(?=\s*\|\s*\w[\w.]*\*?\s*\(|$)"  # lookahead: next param or end
            )
            for pm in re.finditer(param_re, param_text, re.DOTALL):
                pname = pm.group(1)
                required = pm.group(2) == "*"
                type_raw = pm.group(3).strip()
                desc = pm.group(4).strip()

                # Parse type annotation: may have enum after ":"
                enum: list[str] | None = None
                full_type: str = type_raw
                if ":" in type_raw:
                    abbrev, _, enum_raw = type_raw.partition(":")
                    # TAS normalizes enum pipes to " | " — split on that
                    enum_parts = [v.strip() for v in enum_raw.split("|") if v.strip()]
                    if enum_parts:
                        enum = enum_parts
                    full_type = abbrev.strip()

                # Reverse type abbreviations from DRO
                _type_reverse: dict[str, str] = {
                    "str": "string",
                    "num": "number",
                    "bool": "boolean",
                    "arr": "array",
                    "obj": "object",
                }
                full_type = _type_reverse.get(full_type, full_type)

                params.append(ParamDef(
                    name=pname,
                    type=full_type,
                    description=desc,
                    required=required,
                    enum=enum if enum else None,
                ))

        return ToolDef(name=name, description=description, parameters=params)
