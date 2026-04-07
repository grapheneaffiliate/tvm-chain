/*
 * block_verify.c — TVM Block Verification Program
 * =================================================
 *
 * Verifies an entire block's state transition through the Transformer VM.
 * This is the mathematical core of TVM-Chain consensus.
 *
 * Input format (flat integers via stdin/args):
 *   SUPPLY N_ACCOUNTS bal₁ bal₂ ... balₙ N_TX s₁ r₁ a₁ s₂ r₂ a₂ ... final₁ final₂ ... finalₙ
 *
 * Where:
 *   SUPPLY      = total monetary supply (must be conserved)
 *   N_ACCOUNTS  = number of accounts
 *   bal₁..balₙ  = initial balances (ordered by account index)
 *   N_TX        = number of transactions (fees already expanded into explicit transfers)
 *   s₁ r₁ a₁   = sender_index, receiver_index, amount for each transaction
 *   final₁..ₙ   = claimed final balances
 *
 * Output:
 *   "VALID txs=K supply=S"                     — block is correct
 *   "INVALID <reason>"                          — block is incorrect
 *
 * Five Invariants Checked Per Transaction:
 *   1. Account indices are valid (0 ≤ index < N_ACCOUNTS)
 *   2. Transfer amount is positive (amount > 0)
 *   3. Sender has sufficient balance (balance[sender] ≥ amount)
 *   4. No balance goes negative after any transaction
 *   5. Computed final state matches claimed final state exactly
 *
 * Plus global invariant:
 *   sum(final_balances) == sum(initial_balances) == SUPPLY
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

    /* Read initial balances */
    int bal[MAX_ACCOUNTS];
    int initial_sum = 0;

    for (int i = 0; i < n_accts; i++) {
        scanf("%d", &bal[i]);

        if (bal[i] < 0) {
            printf("INVALID negative_initial_balance_account_%d", i);
            return 1;
        }

        initial_sum += bal[i];
    }

    /* Verify initial supply matches claimed supply */
    if (initial_sum != supply) {
        printf("INVALID initial_supply_mismatch_expected_%d_got_%d", initial_sum, supply);
        return 1;
    }

    /* Read and apply transactions */
    int n_tx;
    scanf("%d", &n_tx);

    for (int t = 0; t < n_tx; t++) {
        int s, r, a;
        scanf("%d %d %d", &s, &r, &a);

        /* Invariant 1: valid account indices */
        if (s < 0 || s >= n_accts) {
            printf("INVALID bad_sender_index_%d_tx_%d", s, t);
            return 1;
        }
        if (r < 0 || r >= n_accts) {
            printf("INVALID bad_receiver_index_%d_tx_%d", r, t);
            return 1;
        }

        /* Invariant 2: positive amount */
        if (a <= 0) {
            printf("INVALID non_positive_amount_%d_tx_%d", a, t);
            return 1;
        }

        /* Invariant 3: sufficient balance */
        if (bal[s] < a) {
            printf("INVALID insufficient_balance_account_%d_has_%d_needs_%d_tx_%d", s, bal[s], a, t);
            return 1;
        }

        /* Apply transfer */
        bal[s] -= a;
        bal[r] += a;

        /* Invariant 4: no negative balances after transfer */
        if (bal[s] < 0) {
            printf("INVALID negative_balance_after_tx_%d_account_%d", t, s);
            return 1;
        }
    }

    /* Read claimed final balances and verify */
    int final_sum = 0;

    for (int i = 0; i < n_accts; i++) {
        int claimed;
        scanf("%d", &claimed);

        /* Invariant 4 (final check): no negative computed balances */
        if (bal[i] < 0) {
            printf("INVALID negative_final_balance_account_%d", i);
            return 1;
        }

        /* Invariant 5: computed state matches claimed state */
        if (bal[i] != claimed) {
            printf("INVALID state_mismatch_account_%d_computed_%d_claimed_%d", i, bal[i], claimed);
            return 1;
        }

        final_sum += bal[i];
    }

    /* Global invariant: supply conservation */
    if (final_sum != supply) {
        printf("INVALID supply_mismatch_expected_%d_got_%d", supply, final_sum);
        return 1;
    }

    /* All invariants hold — block is mathematically proven correct */
    printf("VALID txs=%d supply=%d", n_tx, supply);
    return 0;
}
