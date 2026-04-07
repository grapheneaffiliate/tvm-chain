#!/usr/bin/env python3
"""
test_chain.py — Standalone tests for TVM-Chain verification programs
=====================================================================

Tests block_verify.c and ledger_state.c by compiling them with gcc
and feeding valid/tampered inputs. Does NOT require the TVM backend —
these tests verify the C logic independently.

Usage:
    python3 tests/test_chain.py
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
VERIFIED_DIR = REPO_ROOT / "olympus" / "wasm_tools" / "verified"

passed = 0
failed = 0


def compile_c(src_path: Path, out_path: Path) -> bool:
    """Compile a C file with gcc."""
    result = subprocess.run(
        ["gcc", "-o", str(out_path), str(src_path), "-lm"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  COMPILE ERROR: {result.stderr}")
        return False
    return True


def run_program(exe_path: Path, stdin_data: str) -> str:
    """Run a compiled program with stdin input."""
    result = subprocess.run(
        [str(exe_path)],
        input=stdin_data,
        capture_output=True, text=True,
        timeout=10,
    )
    return result.stdout.strip()


def test(name: str, exe_path: Path, stdin_data: str, expected_prefix: str):
    """Run a test and check the output prefix."""
    global passed, failed
    output = run_program(exe_path, stdin_data)
    if output.startswith(expected_prefix):
        print(f"  ✓ {name}")
        print(f"    Output: {output}")
        passed += 1
    else:
        print(f"  ✗ {name}")
        print(f"    Expected prefix: {expected_prefix}")
        print(f"    Got: {output}")
        failed += 1


def main():
    global passed, failed

    print("=" * 60)
    print("  TVM-Chain Verification Program Tests")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # -------------------------------------------------------
        # Compile block_verify.c
        # -------------------------------------------------------
        print("\n--- block_verify.c ---")
        bv_src = VERIFIED_DIR / "block_verify.c"
        bv_exe = tmpdir / "block_verify"

        if not bv_src.exists():
            print(f"  ERROR: {bv_src} not found")
            sys.exit(1)

        if not compile_c(bv_src, bv_exe):
            sys.exit(1)

        print("  Compiled successfully.\n")

        # Test 1: Valid block with 2 transactions
        # 3 accounts: [50, 30, 20], supply=100
        # tx1: account 0 -> account 1, amount 10
        # tx2: account 1 -> account 2, amount 5
        # final: [40, 35, 25]
        test(
            "Valid block (2 txs, supply=100)",
            bv_exe,
            "100 3 50 30 20 2 0 1 10 1 2 5 40 35 25",
            "VALID",
        )

        # Test 2: Tampered final balance
        # Same as above but claim final[0] = 45 instead of 40
        test(
            "Tampered final balance (should detect mismatch)",
            bv_exe,
            "100 3 50 30 20 2 0 1 10 1 2 5 45 35 25",
            "INVALID state_mismatch_account_0",
        )

        # Test 3: Insufficient balance
        # account 2 has 20, tries to send 50
        test(
            "Insufficient balance (should reject)",
            bv_exe,
            "100 3 50 30 20 1 2 0 50 50 30 0",
            "INVALID insufficient_balance",
        )

        # Test 4: Zero-transaction block (valid)
        # No transactions, final = initial
        test(
            "Empty block (0 transactions, valid)",
            bv_exe,
            "100 3 50 30 20 0 50 30 20",
            "VALID",
        )

        # Test 5: Supply mismatch (tampered supply claim)
        # Claim supply is 200 but balances sum to 100
        test(
            "Supply mismatch (initial sum ≠ claimed supply)",
            bv_exe,
            "200 3 50 30 20 0 50 30 20",
            "INVALID initial_supply_mismatch",
        )

        # Test 6: Negative amount
        test(
            "Negative transfer amount (should reject)",
            bv_exe,
            "100 3 50 30 20 1 0 1 -5 50 30 20",
            "INVALID non_positive_amount",
        )

        # Test 7: Fee expansion — sender pays amount + fee via two transfers
        # 3 accounts: Alice(100), Bob(50), Validator(50), supply=200
        # tx1: Alice -> Bob, 30 (the payment)
        # tx2: Alice -> Validator, 5 (the fee)
        # final: Alice=65, Bob=80, Validator=55
        test(
            "Fee expansion (2 transfers for 1 logical tx)",
            bv_exe,
            "200 3 100 50 50 2 0 1 30 0 2 5 65 80 55",
            "VALID",
        )

        # Test 8: Bad account index
        test(
            "Invalid sender index (out of bounds)",
            bv_exe,
            "100 3 50 30 20 1 5 1 10 50 30 20",
            "INVALID bad_sender_index",
        )

        # -------------------------------------------------------
        # Compile ledger_state.c
        # -------------------------------------------------------
        print("\n--- ledger_state.c ---")
        ls_src = VERIFIED_DIR / "ledger_state.c"
        ls_exe = tmpdir / "ledger_state"

        if not ls_src.exists():
            print(f"  ERROR: {ls_src} not found")
            sys.exit(1)

        if not compile_c(ls_src, ls_exe):
            sys.exit(1)

        print("  Compiled successfully.\n")

        # Test 9: Valid genesis state
        test(
            "Valid genesis (supply=100, 3 accounts)",
            ls_exe,
            "100 3 50 30 20",
            "VALID",
        )

        # Test 10: Supply mismatch
        # Balances sum to 99 but claim supply=100
        test(
            "Supply mismatch (sum=99, claimed=100)",
            ls_exe,
            "100 3 50 30 19",
            "INVALID supply_mismatch",
        )

        # Test 11: Negative balance
        test(
            "Negative balance in genesis (should reject)",
            ls_exe,
            "100 3 50 60 -10",
            "INVALID negative_balance",
        )

        # Test 12: Single account (valid)
        test(
            "Single account genesis (valid)",
            ls_exe,
            "2100000000 1 2100000000",
            "VALID",
        )

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------
    print(f"\n{'=' * 60}")
    total = passed + failed
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f", {failed} FAILED")
    else:
        print(" — ALL PASSED ✓")
    print("=" * 60)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
