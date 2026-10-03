#!/usr/bin/env python3
"""폴 하네스 게이트 판정 스크립트.

사용법:
  python harness/gates/check.py G1 workspace
  python harness/gates/check.py G5 workspace --approve --link <Figma URL>
  python harness/gates/check.py G5 workspace --reject "사유" --return S3
  python harness/gates/check.py status workspace
  python harness/gates/check.py G2 workspace --dir <폴더> --dry-run   (테스트용)

종료 코드: 0 PASS, 1 FAIL, 2 실행 불가(앞 게이트 미통과, 파일 없음, 잘못된 인자)
판정 기준값은 모두 harness/rules.json에서 읽는다. gates.json을 쓰는 건 이 스크립트뿐이다.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "harness" / "rules.json"
ORDER = ["G1", "G2", "G3", "G4", "G5", "G6"]
SCREENS = ["login", "projects", "intake", "workspace", "preview"]
FILES = {
    "s1": "s1/s1-reference.json",
    "s2": "s2/s2-analysis.json",
    "s3": "s3/s3-spec.json",
    "s4": "s4/s4-keyscreen.json",
    "s5": "s5/s5-final.json",
}


class Unrunnable(Exception):
    """판정을 시작할 수 없는 상태 (종료 코드 2)."""


def load_json(path):
    if not path.exists():
        raise Unrunnable(f"파일이 없습니다: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise Unrunnable(f"JSON 형식 오류: {path} ({e})")


def load_stage(run_dir, key):
    return load_json(run_dir / FILES[key])


def load_gates(run_dir, screen):
    path = run_dir / "gates.json"
    if path.exists():
        return load_json(path)
    return {"screen": screen, "lastPassed": None, "gates": {}}


def last_passed(gates):
    """G1부터 연속으로 PASS인 마지막 게이트."""
    last = None
    for g in ORDER:
        if (gates["gates"].get(g) or {}).get("result") == "PASS":
            last = g
        else:
            break
    return last


# ---------- 게이트별 판정: 위반 메시지 목록을 돌려준다 ----------

def check_g1(run_dir, rules, screen):
    v = []
    refs = load_stage(run_dir, "s1").get("references", [])
    want = rules["counts"]["references"]
    if len(refs) != want:
        v.append(f"레퍼런스가 {len(refs)}개입니다 (필요: {want}개)")
    for r in refs:
        if "uibowl" not in str(r.get("url", "")):
            v.append(f"레퍼런스 {r.get('id', '?')}에 uibowl 링크가 없습니다")
    points = load_stage(run_dir, "s2").get("points", [])
    need = rules["counts"]["analysisPointsMin"]
    if len(points) < need:
        v.append(f"반영 포인트가 {len(points)}개입니다 (최소 {need}개)")
    for p in points:
        if not p.get("refIds"):
            v.append(f"포인트 {p.get('id', '?')}에 출처 레퍼런스 id가 없습니다")
    return v


def contains_word(text, word):
    # 영문 금지어는 단어 단위로만 찾는다 (HEADER, ADD는 걸리지 않음)
    if re.fullmatch(r"[A-Za-z]+", word):
        return re.search(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", text) is not None
    return word in text


def check_g2(run_dir, rules, screen):
    v = []
    valid = set(rules["stories"]["ids"])
    banned = rules["ruleB"]["bannedWords"]
    exception = rules["ruleB"]["exceptionTag"]
    excluded = rules["mvpExcluded"]["words"]
    for p in load_stage(run_dir, "s2").get("points", []):
        pid, text = p.get("id", "?"), str(p.get("text", ""))
        ids = p.get("storyIds") or []
        if not ids or any(i not in valid for i in ids):
            v.append(f"포인트 {pid}가 유저스토리(1~6)와 연결되지 않았습니다: {ids}")
        if exception not in (p.get("tags") or []):
            hits = [w for w in banned if contains_word(text, w)]
            if hits:
                v.append(f"[규칙 B] 포인트 {pid}에 금지어 {hits}가 있습니다")
        hits = [w for w in excluded if contains_word(text, w)]
        if hits:
            v.append(f"포인트 {pid}에 MVP 제외 기능 {hits}이 있습니다")
    return v


def find_flow(spec, name):
    for f in spec.get("flows") or []:
        if f.get("name") == name:
            return f
    return None


def check_flow(spec, name, expected, label):
    flow = find_flow(spec, name)
    if flow is None:
        return [f"{label} 이동 흐름 '{name}'이 없습니다"]
    return [
        f"{label} '{name}'의 {k}가 {flow.get(k)}입니다 (필요: {want})"
        for k, want in expected.items()
        if flow.get(k) is not want
    ]


def check_g3(run_dir, rules, screen):
    v = []
    spec = load_stage(run_dir, "s3")
    for key in rules["spec"]["requiredSections"]:
        if not spec.get(key):
            v.append(f"필수 항목 '{key}'가 없습니다")
    for c in spec.get("components") or []:
        if not c.get("pointIds") and not c.get("storyIds"):
            v.append(f"구성 요소 {c.get('name', '?')}가 반영 포인트·유저스토리와 연결되지 않았습니다")
    rule_a = rules["ruleA"]
    if screen in rule_a["screens"]:
        v += check_flow(spec, "backFromPreview", rule_a["backFromPreview"], "[규칙 A]")
    if spec.get("hasProjectSwitcher"):
        v += check_flow(spec, "onProjectSwitch", rule_a["onProjectSwitch"], "[프로젝트 전환]")
    return v


def check_g4(run_dir, rules, screen):
    v = []
    frames = load_stage(run_dir, "s4").get("frames", [])
    lo, hi = rules["counts"]["keyscreens"]["min"], rules["counts"]["keyscreens"]["max"]
    if not lo <= len(frames) <= hi:
        v.append(f"키스크린 프레임이 {len(frames)}개입니다 (필요: {lo}~{hi}개)")
    w, min_h = rules["frame"]["width"], rules["frame"]["minHeight"]
    for f in frames:
        if f.get("width") != w:
            v.append(f"프레임 {f.get('name', '?')}의 너비가 {f.get('width')}입니다 (필요: {w})")
        if (f.get("height") or 0) < min_h:
            v.append(f"프레임 {f.get('name', '?')}의 높이가 {f.get('height')}입니다 (최소 {min_h})")
    layers = {name for f in frames for name in (f.get("layers") or [])}
    for c in load_stage(run_dir, "s3").get("components") or []:
        if c.get("name") not in layers:
            v.append(f"구성 요소 {c.get('name')}가 키스크린 레이어에 없습니다")
    return v


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def check_g6(run_dir, rules, screen):
    v = []
    d = rules["design"]
    colors = {c.upper() for c in d["colors"]["allowed"]}
    for n in load_stage(run_dir, "s5").get("nodes", []):
        name = n.get("name", "?")
        for hexv in as_list(n.get("fills")) + as_list(n.get("strokes")):
            if str(hexv).upper()[:7] not in colors:
                v.append(f"{name}: 토큰에 없는 색 {hexv}")
        if n.get("fontFamily") is not None and n["fontFamily"] not in d["fontFamily"]["allowed"]:
            v.append(f"{name}: 허용되지 않은 폰트 {n['fontFamily']}")
        if n.get("fontSize") is not None and n["fontSize"] not in d["fontSize"]["allowed"]:
            v.append(f"{name}: 타입 스케일에 없는 글자 크기 {n['fontSize']}")
        if n.get("fontWeight") is not None and n["fontWeight"] not in d["fontWeight"]["allowed"]:
            v.append(f"{name}: 허용되지 않은 굵기 {n['fontWeight']}")
        for r in as_list(n.get("radius")):
            if r not in d["radius"]["allowed"]:
                v.append(f"{name}: 허용되지 않은 radius {r}")
        for s in as_list(n.get("padding")) + as_list(n.get("gap")):
            if s not in d["spacing"]["allowed"]:
                v.append(f"{name}: spacing 허용값이 아닌 간격 {s}")
        kind, height = n.get("kind"), n.get("height")
        min_h = d["minHeight"].get(kind)
        if min_h is not None and height is not None and height < min_h:
            v.append(f"{name}: {kind} 높이 {height}px (최소 {min_h}px)")
    return v


CHECKS = {"G1": check_g1, "G2": check_g2, "G3": check_g3, "G4": check_g4, "G6": check_g6}


# ---------- 기록 ----------

def record(gates, gate, passed, violations, extra=None):
    entry = gates["gates"].get(gate) or {}
    failures = entry.get("failures", 0)
    now = datetime.now().isoformat(timespec="seconds")
    entry.update(extra or {})
    entry["result"] = "PASS" if passed else "FAIL"
    # failures = 연속 실패 (3회 STOP 판단용, PASS면 0), totalFailures = 누적 실패 (기록용)
    entry["failures"] = 0 if passed else failures + 1
    entry["totalFailures"] = entry.get("totalFailures", 0) + (0 if passed else 1)
    entry.setdefault("history", []).append({
        "result": entry["result"], "at": now, "violations": len(violations),
        **({"reason": extra["reason"]} if extra and extra.get("reason") else {}),
    })
    entry["violations"] = violations
    entry["checkedAt"] = now
    gates["gates"][gate] = entry
    # 이 게이트 뒤의 결과는 다시 판정해야 하므로 무효로 만든다 (실패 횟수는 유지)
    for later in ORDER[ORDER.index(gate) + 1:]:
        if gates["gates"].get(later):
            gates["gates"][later]["result"] = None
    gates["lastPassed"] = last_passed(gates)
    return entry


def require_previous(gates, gate):
    idx = ORDER.index(gate)
    if idx == 0:
        return
    prev = ORDER[idx - 1]
    if (gates["gates"].get(prev) or {}).get("result") != "PASS":
        raise Unrunnable(f"{prev}가 PASS가 아니어서 {gate}를 판정할 수 없습니다")


def print_status(gates, screen):
    print(f"[{screen}] 마지막 통과 게이트: {gates.get('lastPassed') or '없음'}")
    for g in ORDER:
        e = gates["gates"].get(g) or {}
        print(f"  {g}: {e.get('result') or '-':4}  연속 실패 {e.get('failures', 0)}회 · 누적 실패 {e.get('totalFailures', 0)}회")


def main(argv=None):
    ap = argparse.ArgumentParser(description="폴 하네스 게이트 판정")
    ap.add_argument("gate", choices=ORDER + ["status"])
    ap.add_argument("screen", choices=SCREENS)
    ap.add_argument("--dir", help="runs/<화면> 대신 읽을 폴더 (테스트용)")
    ap.add_argument("--dry-run", action="store_true", help="gates.json에 쓰지 않음")
    ap.add_argument("--approve", action="store_true", help="G5 승인")
    ap.add_argument("--reject", metavar="사유", help="G5 반려 사유")
    ap.add_argument("--return", dest="return_to", choices=["S3", "S4"], help="G5 반려 시 돌아갈 단계")
    ap.add_argument("--link", help="G5 Figma 링크")
    args = ap.parse_args(argv)

    run_dir = Path(args.dir) if args.dir else ROOT / "runs" / args.screen
    try:
        rules = load_json(RULES_PATH)
        gates = load_gates(run_dir, args.screen)

        if args.gate == "status":
            print_status(gates, args.screen)
            return 0

        require_previous(gates, args.gate)

        if args.gate == "G5":
            if args.approve == bool(args.reject):
                raise Unrunnable("G5는 --approve 또는 --reject 중 하나만 지정해야 합니다")
            if args.approve and not args.link:
                raise Unrunnable("G5 승인에는 --link <Figma URL>이 필요합니다")
            if args.reject and not args.return_to:
                raise Unrunnable("G5 반려에는 --return S3|S4가 필요합니다")
            passed = args.approve
            violations = [] if passed else [f"관계자 반려: {args.reject}"]
            extra = {
                "status": "approved" if passed else "rejected",
                "reason": args.reject or "",
                "returnTo": args.return_to,
                "figmaLink": args.link,
                "date": datetime.now().date().isoformat(),
            }
        else:
            violations = CHECKS[args.gate](run_dir, rules, args.screen)
            passed = not violations
            extra = None
    except Unrunnable as e:
        print(f"실행 불가: {e}")
        return 2

    entry = record(gates, args.gate, passed, violations, extra)
    print(f"{args.gate} {args.screen}: {entry['result']}")
    for msg in violations:
        print(f"  - {msg}")
    if not passed and entry["failures"] >= rules["counts"]["maxGateFailures"]:
        print(f"STOP: {args.gate}에서 {entry['failures']}회 실패했습니다. 사람 확인이 필요합니다.")

    if not args.dry_run:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "gates.json").write_text(
            json.dumps(gates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
