# Chinese/English Edition Equivalence Audit

## Conclusion

The Chinese- and English-instruction editions of `ecommerce-poster-design` 3.1.0-rc.7 are functionally equivalent. “Chinese/English editions” describes the language of the operating instructions only; it does not introduce Chinese-English bilingual poster output.

## Inventory

- Chinese edition: 188 files.
- English edition: 188 files.
- Relative-path inventories: identical.
- Byte-identical files: 162.
- Localized instruction or documentation-probe files: 26.
- Production configuration, schemas, thresholds, classification assets, scoring formulas, and most routing code are byte-identical.

## Preserved contracts

| Area | Result |
|---|---|
| Skill identity | Both use `ecommerce-poster-design` version `3.1.0-rc.7`. |
| Poster language | Both accept one selected language per poster: Chinese-only or English-only. |
| Protected copy | Neither edition may translate or rewrite confirmed protected copy without authorization. |
| Main workflow | Classification → generation → HC-01–HC-12 → consumer → aesthetic → final-quality arbitration. |
| Consumer gate | Same thresholds, five locks, hard fails, and regression behavior. |
| Aesthetic gate | Same six dimensions, scoring code, and pass thresholds. |
| Final quality | Same `FINAL-QUALITY-3.2` defects and reverse-review rules. |
| Budget | Same global maximum of eight successful redraws. |
| Modules | Consumer 1.5.3; Aesthetic 3.0.0-rc.5; C assets 2.0.1-a.1. |
| rc.7 Logo rules | Same safe-area, visible-container, authoritative-asset, and lockup rules. |

## Translation boundary

Markdown/YAML operating instructions are localized. Production Python and JavaScript behavior remains equivalent; three English-edition integration validators localize only the documentation strings they search for. Chinese content intentionally retained in JSON/CSV cases, fixtures, and classification records is business/test data and is not an untranslated instruction.

## Verification scope

Repository validation covers inventory, syntax, links, language/canvas behavior, classification assets, routing, scoring, final-quality integration, consumer assertions, and Logo contracts. It is deterministic and does not invoke ImageGen or claim a new visual evaluation run.
