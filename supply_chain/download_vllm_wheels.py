"""
Supply Chain Script: Download vLLM + Dependencies for Offline Kaggle Install

Run this script LOCALLY (with internet access) to download all the Python
wheels needed to install vLLM on Kaggle's air-gapped H100 environment.

Usage:
    python download_vllm_wheels.py [--output-dir ./vllm_wheels]

After running:
    1. Verify checksums:  python verify_checksums.py
    2. Upload the output directory as a private Kaggle Dataset named 'aimo-vllm-wheels'
"""

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


def download_wheels(output_dir: Path, vllm_version: str = "0.7.2"):
    """Download vLLM and all dependencies as wheel files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Downloading vLLM v{vllm_version} wheels to {output_dir}")
    print("      Target: Python 3.10, Linux x86_64 (Kaggle's environment)")
    print("      This may take several minutes...\n")

    cmd = [
        sys.executable, "-m", "pip", "download",
        f"vllm=={vllm_version}",
        # DEPENDENCY FIXES (2025-02-13):
        # Kaggle's latest image has cuda-python 13.x which breaks cudf (needs <13.0)
        "cuda-python>=12.6.2,<13.0.0",
        # Tensorflow and others need protobuf < 6.0.0 (often < 5.0.0 is safer for older google-cloud libs)
        # We pin to 4.25.3 to be safe against the MessageFactory error
        "protobuf==4.25.3",
        "--dest", str(output_dir),
        "--python-version", "3.10",
        "--only-binary", ":all:",
        "--platform", "manylinux1_x86_64",
        "--platform", "manylinux2014_x86_64",
        "--platform", "manylinux_2_17_x86_64",
        "--platform", "manylinux_2_28_x86_64",
        "--platform", "linux_x86_64",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] pip download failed:\n{result.stderr}")
        print("\n[TIP] If wheels are missing, try downloading with broader platform tags")
        print("      or install vllm locally first: pip install vllm, then use")
        print("      pip download with --no-deps for individual missing packages.")
        sys.exit(1)

    print(f"[OK] Downloaded wheels to {output_dir}\n")
    return output_dir


def generate_checksums(wheels_dir: Path):
    """Generate MD5 checksums for all downloaded files."""
    checksum_file = wheels_dir / "md5_checksums.txt"
    print(f"[2/3] Generating MD5 checksums -> {checksum_file}")

    checksums = []
    for f in sorted(wheels_dir.iterdir()):
        if f.suffix in (".whl", ".tar.gz", ".zip"):
            md5 = hashlib.md5(f.read_bytes()).hexdigest()
            checksums.append(f"{md5}  {f.name}")
            print(f"      {md5}  {f.name}")

    checksum_file.write_text("\n".join(checksums) + "\n")
    print(f"\n[OK] Wrote {len(checksums)} checksums\n")
    return len(checksums)


def print_instructions(wheels_dir: Path, num_files: int):
    """Print next steps for the user."""
    total_size_mb = sum(
        f.stat().st_size for f in wheels_dir.iterdir()
        if f.suffix in (".whl", ".tar.gz", ".zip")
    ) / (1024 * 1024)

    print("=" * 60)
    print("SUPPLY CHAIN READY")
    print("=" * 60)
    print(f"  Files:      {num_files} packages")
    print(f"  Total size: {total_size_mb:.1f} MB")
    print(f"  Location:   {wheels_dir.resolve()}")
    print()
    print("[3/3] NEXT STEPS:")
    print("  1. Verify: python verify_checksums.py")
    print("  2. Go to https://www.kaggle.com/datasets")
    print("  3. Click 'New Dataset' -> name it 'aimo-vllm-wheels'")
    print("  4. Upload the ENTIRE contents of the wheels directory")
    print("  5. Set visibility to 'Private'")
    print()
    print("  In your Kaggle notebook, install with:")
    print("  !pip install --no-index \\")
    print("      --find-links=/kaggle/input/aimo-vllm-wheels/ \\")
    print("      vllm")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Download vLLM wheels for offline Kaggle install"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("supply_chain/vllm_wheels"),
        help="Directory to save wheel files (default: supply_chain/vllm_wheels)",
    )
    parser.add_argument(
        "--vllm-version",
        type=str,
        default="0.10.2",
        help="vLLM version to download (default: 0.10.2)",
    )
    args = parser.parse_args()

    download_wheels(args.output_dir, args.vllm_version)
    num_files = generate_checksums(args.output_dir)
    print_instructions(args.output_dir, num_files)


if __name__ == "__main__":
    main()
