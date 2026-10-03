#!/usr/bin/env python3
"""check.py 검증: fixtures를 하나씩 돌려 예상(PASS/FAIL)과 결과를 비교한다.

사용법: python harness/tests/run.py
통과 기준: 예상과 결과가 다른 fixture가 0개 (종료 코드 0)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE.parent / "gates" / "check.py"
EXIT = {0: "PASS", 1: "FAIL", 2: "실행 불가"}


def run_fixture(path):
    fx = json.loads(path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        for rel, data in fx["files"].items():
            target = Path(tmp) / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(CHECK), fx["gate"], fx["screen"], "--dir", tmp, "--dry-run"],
            capture_output=True, text=True,
        )
    return fx, EXIT.get(proc.returncode, f"코드 {proc.returncode}"), proc.stdout.strip()


def main():
    fixtures = sorted((HERE / "fixtures").glob("*.json"))
    mismatches = 0
    for path in fixtures:
        fx, got, out = run_fixture(path)
        ok = got == fx["expect"]
        mismatches += not ok
        print(f"{'OK ' if ok else 'NG '} {path.stem:24} 예상 {fx['expect']:4} / 결과 {got}")
        if not ok or got == "FAIL":
            for line in out.splitlines()[1:]:
                print(f"      {line.strip()}")
    print(f"\n총 {len(fixtures)}개 중 불일치 {mismatches}개")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
