# Agent Validation Prompt — Phase 07a

> Feed this prompt to an AI agent (Claude Code, OpenCode, Cursor) to verify that
> the merged token-saving rules produce correct behavior.
> 
> **How to use**: Copy the `templates/agents_md_section.md` content into the agent's
> instructions file, then give the agent the tasks below. Verify outputs against
> expected behaviors.

---

## Task 1: Code Fix Request

**Prompt to agent:**
"Fix the bug in `src/auth.py` where login returns 500 when the user already exists."

**Expected agent behavior (if rules are working):**

| Rule | Expected | Anti-pattern (fails) |
|------|----------|---------------------|
| Rule 1 (No preamble) | Agent starts with diagnosis or code | "Sure! I'd be happy to help fix that bug..." |
| Rule 12 (YAGNI) | Agent checks: does `src/auth.py` exist? Can stdlib fix it? | Agent imports a new library without checking stdlib |
| Rule 20 (Grep before Read) | Agent greps for "login" or "500" in auth.py first | Agent reads entire auth.py (especially if >500 lines) |
| Rule 5 (Code leads) | Code fix shown first, explanation minimal | Long prose explanation before showing code |
| Rule 2 (No closing filler) | Response ends with code or fix summary | "Hope that helps! Let me know if you need anything else." |
| Rule 26 (Correctness wins) | Agent mentions "this is irreversible" if the fix is destructive | Terse but omits safety warning for destructive operation |

**Pass criteria:** Agent output is terse, code-first, grep-first, no filler.

---

## Task 2: Code Explanation Request

**Prompt to agent:**
"How does the token saving protocol work in AGENTS.md?"

**Expected agent behavior:**

| Rule | Expected | Anti-pattern (fails) |
|------|----------|---------------------|
| Rule 6 (Never restate or explain intent) | Agent answers directly | "Let me look at the AGENTS.md to explain how..." |
| Rule 19 (SubAgent for >3 files) | If answer needs searching >3 files, dispatches Explore subagent | Reads multiple files into main session |
| Rule 21 (Batch independent) | Reads template + injector in one batch | Reads template, waits, reads injector separately |
| Rule 11 (≤60 words prose) | Response under 60 words | Paragraphs of explanation |
| Rule 22 (Never search twice) | If data was already referenced, doesn't re-search | Re-reads the same files mentioned earlier |

**Pass criteria:** Agent is efficient — parallel reads, no preamble, under 60 words.

---

## Task 3: Multi-File Exploration Request

**Prompt to agent:**
"Find all places in the project that reference 'caveman' and summarize how it's used."

**Expected agent behavior:**

| Rule | Expected | Anti-pattern (fails) |
|------|----------|---------------------|
| Rule 19 (SubAgent for exploration) | Dispatches Explore subagent, receives summary | Reads 5+ files individually into main session |
| Rule 25 (Limit SubAgent output) | Subagent prompt includes "under 200 words, file paths + conclusions" | Subagent returns raw grep output |
| Rule 23 (Filter Bash output) | Uses `grep -r "caveman" --include="*.md" | head -30` | Runs unfiltered grep producing >500 lines |
| Rule 24 (Compact after large reads) | If output >500 lines, suggests compaction | Displays all output without suggestion |

**Pass criteria:** Agent delegates exploration, receives compact summary, never reads raw files.

---

## Verification Checklist

After running all 3 tasks, check:

- [ ] **No preamble** in any response (no "Sure!", "Certainly", "Here is", "Let me")
- [ ] **No closing filler** (no "Hope that helps", "Let me know")
- [ ] **Code leads when applicable** (Task 1, Task 3)
- [ ] **SubAgent used for exploration** (Task 3)
- [ ] **Grep before Read** when reading files (Task 1)
- [ ] **Batch calls** for independent operations (Task 2)
- [ ] **Response under 60 words** prose for typical questions (Task 2)
- [ ] **Never restates question** (Task 1, 2, 3)
- [ ] **Safety warnings preserved** for destructive operations
- [ ] **No hedging** ("might", "perhaps", "it seems")

**All 10 must pass for Phase 07a validation to be complete.**
