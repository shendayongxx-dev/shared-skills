# ecommerce-poster-design 3.1.0-rc.7 Chinese/English editions

This repository contains the frozen Chinese and English operational-instruction editions of `ecommerce-poster-design` 3.1.0-rc.7.

The two editions implement the same poster-generation workflow, contracts, modules, thresholds, gates, redraw budget, and stopping conditions. The language of a Skill's operating instructions does not determine the poster-copy language. Poster language continues to be selected by `canvas.language` and the user-approved protected copy.

“Chinese/English editions” refers only to the language of the Skill operating instructions. It does not add a bilingual-poster mode and does not restrict the English-instruction edition to English posters. The frozen rc.7 contract supports one selected poster language per request: Chinese or English.

## Repository layout

```text
skills/
  zh/ecommerce-poster-design/   Frozen Chinese operational instructions
  en/ecommerce-poster-design/   Frozen English operational instructions
docs/                           Freeze records and equivalence audit
tools/                          Deterministic validation entry points
dist/
  zh/                           Packaged Chinese Skill
  en/                           Packaged English Skill
RELEASE-MANIFEST.json           Release identity and package checksums
```

## Release identity

- Skill: `ecommerce-poster-design`
- Version: `3.1.0-rc.7`
- Upstream frozen commit: `c6e3eb80ee2b55ce887ff47b8d03a7766c4a9a05`
- Upstream tag: `ecommerce-poster-design-v3.1.0-rc.7`
- Consumer Agent: `1.5.3`
- Aesthetic Agent: `3.0.0-rc.5`
- C-library assets: `2.0.1-a.1`

## Validate

From the repository root on Windows PowerShell:

```powershell
./tools/validate_release.ps1
```

The validation entry point checks both inventories, JSON and Python syntax, Markdown links, Chinese/English poster-language flow equivalence, classification assets, routing, scoring, final-quality contracts, and the rc.7 Logo pipeline.

## Frozen-release policy

Do not edit either directory under `skills/` in place. Create a new candidate or version for future changes. Translation-only differences are documented in [docs/EDITION-EQUIVALENCE-AUDIT.md](docs/EDITION-EQUIVALENCE-AUDIT.md).

The repository intentionally retains multilingual JSON/CSV fixtures and classification records in both editions. They are test/reference data, not untranslated operating instructions.
