
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MAIN_FILE = BASE_DIR / "main.py"
INSTANCES_DIR = BASE_DIR / "instances"


def run_all_tests():
    if not INSTANCES_DIR.exists():
        print(f"❌ Priečinok neexistuje: {INSTANCES_DIR}")
        return

    instance_files = sorted(INSTANCES_DIR.glob("*.in"))

    if not instance_files:
        print("❌ Nenašli sa žiadne .in súbory.")
        return

    print(f"Nájdených {len(instance_files)} testovacích inštancií.")
    print("Spúšťam...\n")

    passed_count = 0
    failed_count = 0

    for filepath in instance_files:
        filename = filepath.name

        expected_unsat = (
            "invalid" in filename.lower()
            or "unsat" in filename.lower()
        )
        expected_code = 20 if expected_unsat else 10

        result = subprocess.run(
            [
                sys.executable,
                str(MAIN_FILE),
                "-i", str(filepath),
                "-v", "1"
            ],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )

        output = result.stdout

        print(f"\n{'=' * 10} VÝSTUP PRE: {filename} {'=' * 10}")

        if output:
            print(output, end="" if output.endswith("\n") else "\n")

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"Return code: {result.returncode}")
        print("=" * 40)

        if result.returncode != 0:
            status = (
                f"❌ ERROR (main.py skončil "
                f"s kódom {result.returncode})"
            )
            failed_count += 1

        else:
            if "UNSATISFIABLE" in output:
                actual_code = 20
            elif "SATISFIABLE" in output:
                actual_code = 10
            else:
                actual_code = -1

            if actual_code == expected_code:
                status = "✅ PASS"
                passed_count += 1
            else:
                expected = "UNSAT" if expected_code == 20 else "SAT"

                if actual_code == 20:
                    actual = "UNSAT"
                elif actual_code == 10:
                    actual = "SAT"
                else:
                    actual = "UNKNOWN"

                status = (
                    f"❌ FAIL (očakávané: {expected} "
                    f"| skutočné: {actual})"
                )
                failed_count += 1

        print(f"  - {filename:<30} -> {status}")

    print("\n" + "=" * 50)
    print(f"Úspešné: {passed_count}, Neúspešné: {failed_count}")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
