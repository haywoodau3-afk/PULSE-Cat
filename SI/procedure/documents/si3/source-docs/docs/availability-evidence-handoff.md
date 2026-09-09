# Availability-evidence handoff

Populate `data/expansion/pptl/availability-evidence-template.csv` only after candidate identities are frozen. One row represents one supplier observation for one exact InChIKey.

The upstream route-aware identity screen is documented in
`docs/route-aware-pubchem-screen.md`. Its PubChem hits and seed examples are
identity evidence only; they must not be copied into this supplier ledger as
stock evidence. The four route partners are generated from the same frozen
candidate and retained with their method label so a supplier observation can be
traced back to the selected disconnection.

## Required checks

1. Confirm the supplier structure matches the frozen canonical SMILES/InChIKey, including regiochemistry and stereochemistry.
2. Record the destination region, pack size, price/currency, lead time, access timestamp, catalogue number, URL or permitted response, and a page/file hash.
3. Assign E0–E6 using the ladder in the development plan. Do not infer stock from a catalogue listing.
4. Record whether the complete route is chemist-accepted and whether EHS review is complete.
5. A candidate is `Experimentally Eligible` only if the structure passes the chemistry contract, has an accepted route, passes safety review, and has E0/E1 evidence or two independent E2 records.

Synthetic entries in `availability-sample.json` are test fixtures and must never be copied into the real-evidence ledger.
