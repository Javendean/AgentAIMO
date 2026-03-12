"""
Supply Chain Verification: Validate wheel file integrity via MD5 checksums.

Run this AFTER download_vllm_wheels.py and BEFORE uploading to Kaggle.
Catches corrupted downloads that would cause silent failures on the H100.

Usage:
    python verify_checksums.py [--wheels-dir ./vllm_wheels]
"""

import argparse
import hashlib
import sys
from pathlib import Path


def verify(wheels_dir: Path) -> bool:
    """Verify all wheels against their recorded MD5 checksums."""
    checksum_file = wheels_dir / "md5_checksums.txt"

    if not checksum_file.exists():
        print(f"[ERROR] No checksum file found at {checksum_file}")
        print("        Run download_vllm_wheels.py first.")
        return False

    lines = checksum_file.read_text().strip().split("\n")
    total = len(lines)
    passed = 0
    failed = 0

    print(f"Verifying {total} files in {wheels_dir}...\n")

    for line in lines:
        expected_md5, filename = line.split("  ", 1)
        filepath = wheels_dir / filename

        if not filepath.exists():
            print(f"  [MISSING] {filename}")
            failed += 1
            continue

        actual_md5 = hashlib.md5(filepath.read_bytes()).hexdigest()

        if actual_md5 == expected_md5:
            print(f"  [  OK  ] {filename}")
            passed += 1
        else:
            print(f"  [FAIL!] {filename}")
            print(f"          Expected: {expected_md5}")
            print(f"          Got:      {actual_md5}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} passed, {failed} failed")

    if failed == 0:
        print("STATUS: ALL CLEAR — Safe to upload to Kaggle")
        return True
    else:
        print("STATUS: INTEGRITY FAILURE — Do NOT upload!")
        print("        Re-run download_vllm_wheels.py")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Verify vLLM wheel checksums before Kaggle upload"
    )
    parser.add_argument(
        "--wheels-dir",
        type=Path,
        default=Path("supply_chain/vllm_wheels"),
        help="Directory containing wheel files (default: supply_chain/vllm_wheels)",
    )
    args = parser.parse_args()

    success = verify(args.wheels_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
