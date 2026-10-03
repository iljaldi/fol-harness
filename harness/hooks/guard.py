#!/usr/bin/env python3
"""PreToolUse 훅: 기준 문서·판정 기록·에이전트 폴더를 보호한다.

Claude Code가 stdin으로 넘기는 JSON(tool_name, tool_input, cwd, 에이전트 정보)을 읽고,
막아야 하면 이유를 stderr에 쓰고 종료 코드 2로 끝낸다. 허용이면 종료 코드 0.

규칙 (harness/r7-orchestrator.md)
  1. 기준 문서·harness/·.claude/·CLAUDE.md 수정 금지 (harness/.unlock이 있으면 허용)
  2. runs/*/gates.json 직접 수정 금지 (check.py만 쓴다)
  3. harness/.unlock 생성·삭제 금지 (사람이 `!` 명령으로만)
  4. 작업 에이전트는 자기 runs/*/sN/ 밖에 쓰기 금지
  5. gate-judge는 쓰기 금지
에이전트 정보가 입력에 없으면 4·5번은 건너뛴다. Bash 검사는 문자열 기반이라 완벽하지 않다.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2]).resolve()
UNLOCK = ROOT / "harness" / ".unlock"
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
STAGE_AGENTS = {
    "ref-collector": "s1",
    "ref-analyst": "s2",
    "screen-planner": "s3",
    "keyscreen-maker": "s4",
    "ui-designer": "s5",
}
JUDGE = "gate-judge"
# Bash 문자열 검사에 쓰는 보호 대상 표시
PROTECTED_MARKS = ["fol-PRD.md", "fol-DESIGN.md", "fol-story-service.md", "fol-story-workflow.md",
                   "CLAUDE.md", "harness/", ".claude/"]
# python -c / node -e / perl -e 안에서 파일을 쓰거나 지우는 표시. 없으면 읽기로 본다.
INLINE_WRITE = re.compile(
    r"open\([^)]*['\"][wax+]|write_text|write_bytes|\.write\(|json\.dump\(|"
    r"os\.(remove|unlink|rename|replace|rmdir)|shutil\.|unlink\(|rmtree|writeFile|appendFile|"
    r"open\([^)]*['\"][<>+]")


def block(reason):
    print(f"[guard] 차단: {reason}", file=sys.stderr)
    sys.exit(2)


def rel(path_str, cwd):
    """프로젝트 루트 기준 상대 경로. 프로젝트 밖이면 None."""
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(cwd or ROOT) / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def is_protected_doc(r):
    return (
        r in {"fol-PRD.md", "fol-DESIGN.md", "fol-story-service.md", "fol-story-workflow.md", "CLAUDE.md"}
        or r.startswith("harness/")
        or r.startswith(".claude/")
    )


def is_gates_json(r):
    return re.fullmatch(r"runs/[^/]+/gates\.json", r) is not None


def agent_of(data):
    return data.get("agent_type") or data.get("agent_name") or (data.get("agent") or {}).get("type")


def check_write(r, agent):
    if r == "harness/.unlock":
        block("harness/.unlock은 사람만 `! touch` / `! rm`으로 다룰 수 있습니다")
    if is_gates_json(r):
        block(f"{r}은 check.py만 쓸 수 있습니다")
    if is_protected_doc(r) and not UNLOCK.exists():
        block(f"{r}은 기준 문서입니다. 고치려면 사람이 `! touch harness/.unlock`을 먼저 실행해야 합니다")
    if agent == JUDGE:
        block("gate-judge는 파일을 쓸 수 없습니다 (읽기 전용 판정자)")
    if agent in STAGE_AGENTS:
        folder = STAGE_AGENTS[agent]
        if re.fullmatch(rf"runs/[^/]+/{folder}/.+", r) is None:
            block(f"{agent}는 runs/<화면>/{folder}/ 안에만 쓸 수 있습니다 (시도: {r})")


def strip_outside_paths(cmd, cwd):
    """프로젝트 밖을 가리키는 절대 경로(~/… 포함)를 지운다. 홈의 .claude/ 같은 경로를 보호 대상으로 착각하지 않게."""
    def repl(m):
        tok = m.group(0)
        p = os.path.expanduser(tok.strip("'\""))
        if not os.path.isabs(p) or rel(p, cwd) is not None:
            return tok
        return " "
    return re.sub(r"\"[^\"]*\"|'[^']*'|[^\s;|&<>]+", repl, cmd)


def check_bash(cmd, cwd, agent):
    if agent == JUDGE and "harness/gates/check.py" not in cmd:
        block("gate-judge는 check.py 실행만 할 수 있습니다")
    # 출력 정리용 리다이렉트는 쓰기로 보지 않는다
    cleaned = re.sub(r"\d?>&\d|\d?>\s*/dev/null", "", cmd)
    write_cmd = re.search(
        r"\b(tee|rm|mv|cp|touch|truncate|ln|chmod|install|dd)\b|\bsed\s+(-[A-Za-z]*i|--in-place)", cleaned)
    # 인라인 스크립트는 쓰기 표시가 있을 때만 쓰기로 본다 (읽기 전용 python -c는 허용)
    py_inline = re.search(r"\bpython3?\s+-c\b|\bnode\s+-e\b|\bperl\s+-e\b", cleaned) and INLINE_WRITE.search(cleaned)
    targets = re.findall(r">>?\s*([^\s;|&]+)", cleaned)
    cleaned = strip_outside_paths(cleaned, cwd)

    if ".unlock" in cleaned and (write_cmd or py_inline or targets):
        block("harness/.unlock은 사람만 `! touch` / `! rm`으로 다룰 수 있습니다")
    for t in targets:
        r = rel(t, cwd)
        if r is not None:
            check_write(r, None)
    if "gates.json" in cleaned and (write_cmd or py_inline):
        block("gates.json은 check.py만 쓸 수 있습니다")
    if not UNLOCK.exists() and (write_cmd or py_inline):
        hits = [m for m in PROTECTED_MARKS if m in cleaned]
        if hits:
            block(f"기준 문서를 바꿀 수 있는 명령입니다 ({', '.join(hits)}). "
                  "고치려면 사람이 `! touch harness/.unlock`을 먼저 실행해야 합니다")


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool = data.get("tool_name")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd")
    agent = agent_of(data)

    if tool in WRITE_TOOLS:
        path = ti.get("file_path") or ti.get("notebook_path")
        if path:
            r = rel(path, cwd)
            if r is not None:
                check_write(r, agent)
            elif agent in STAGE_AGENTS or agent == JUDGE:
                block(f"{agent}는 프로젝트 밖에 쓸 수 없습니다 (시도: {path})")
    elif tool == "Bash":
        check_bash(ti.get("command", ""), cwd, agent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
