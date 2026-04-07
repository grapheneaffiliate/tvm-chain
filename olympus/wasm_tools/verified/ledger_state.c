/*
 * ledger_state.c — TVM Ledger State Verification Program
 * ========================================================
 *
 * Verifies a ledger state snapshot in isolation. Used for genesis
 * block verification — confirms that the initial distribution sums
 * to exactly the claimed supply and all balances are non-negative.
 *
 * Input format (flat integers via stdin/args):
 *   SUPPLY N_ACCOUNTS bal₁ bal₂ ... balₙ
 *
 * Where:
 *   SUPPLY      = claimed total monetary supply
 *   N_ACCOUNTS  = number of accounts
 *   bal₁..balₙ  = account balances (ordered by account index)
 *
 * Output:
 *   "VALID supply=S accounts=N"                         — state is correct
 *   "INVALID negative_balance_account_K"                — account K has negative balance
 *   "INVALID supply_mismatch_expected_X_got_Y"          — sum ≠ claimed supply
 *
 * Invariants Checked:
 *   1. All balances are non-negative (bal[i] ≥ 0 for all i)
 *   2. Sum of all balances equals claimed supply exactly
 */

#include <stdio.h>

#define MAX_ACCOUNTS 256

int main() {
    int supply;
    int n_accts;

    scanf("%d", &supply);
    scanf("%d", &n_accts);

    if (n_accts <= 0 || n_accts > MAX_ACCOUNTS) {
        printf("INVALID bad_account_count_%d", n_accts);
        return 1;
    }

    int total = 0;

    for (int i = 0; i < n_accts; i++) {
        int bal;
        scanf("%d", &bal);

        /* Invariant 1: non-negative balance */
        if (bal < 0) {
            printf("INVALID negative_balance_account_%d_value_%d", i, bal);
            return 1;
        }

        total += bal;
    }

    /* Invariant 2: supply conservation */
    if (total != supply) {
        printf("INVALID supply_mismatch_expected_%d_got_%d", total, supply);
        return 1;
    }

    /* State is verified — all balances non-negative and sum to supply */
    printf("VALID supply=%d accounts=%d", supply, n_accts);
    return 0;
}
