# Source Map — Claude Code v2.1.81 Auto Mode

Minified symbol → purpose mappings extracted from `cli.js`. Facts only.

## Denial tracking state (`oR8`)

- `oR8` — object managing denial tracking state
- `consecutiveDenials` — count of consecutive blocked actions; resets to 0 on any allow
- `totalDenials` — cumulative blocked actions in session; never resets
- Thresholds: `consecutiveDenials >= 3` → escalate to user; `totalDenials >= 20` → abort session
- State key: `sessionId` (matches `session_id` from hook stdin)
- State file: `.automode-state.json` in cwd

## Read-only tool allowlist (`QHY`)

- `QHY` — set of tool names that skip the classifier entirely (read-only, no state modification)
- Extracted set: `Read`, `Glob`, `Grep`, `LS`, `WebFetch`, `WebSearch`, `TodoRead`, `NotebookRead`, `ListMcpResourcesTool`, `ReadMcpResourceTool`

## `classify_result` tool definition (`ie9`)

- `ie9` — tool definition object passed to the Stage 2 classifier
- Tool name: `classify_result`
- Fields: `shouldBlock` (boolean), `reason` (string), `thinking` (string)
- Stage 2 is required to call this tool to produce its decision

## System prompt (`pe9`, `ZZ4`)

- `pe9.exports` — base system prompt text (trust boundary, evaluation criteria, rule format)
- `ZZ4.exports` — rule slot template (inserts deny/allow rule lists into pe9 at runtime)
- Both exports combined form the full system prompt string sent to both Stage 1 and Stage 2

## Transcript loading (`hZ4`, `IZ4`, `CZ4`)

- `hZ4` — loads and parses the conversation transcript from `transcript_path`
- `IZ4` — filters transcript to classifier-relevant entries:
  - From assistant turns: extracts only `tool_use` blocks (strips prose)
  - From user turns: extracts only `text` blocks (strips `tool_result` blocks)
- `CZ4` — formats a single tool call as `"ToolName <json>\n"` for the classifier message

## Auto-mode defaults (`bd6`, `q6_`)

- `bd6` — default soft-deny rules list (30 rules); see `auto-mode-defaults.json`
- `q6_` — default allow rules list (7 rules); see `auto-mode-defaults.json`
- Both are overridable via `autoMode.soft_deny` / `autoMode.allow` in `.claude/settings.json`

## `claude auto-mode defaults` command

Running `claude auto-mode defaults` in the CLI prints the full JSON config:
- `soft_deny`: 30 rule strings
- `allow`: 7 exception rule strings
- `environment`: trust boundary descriptors (repo, orgs, domains, buckets)

Output captured in `auto-mode-defaults.json`.
