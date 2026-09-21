# Terpsi — web presence

**Status:** domain + Squarespace secured (date: 2026-08-03). **Fill in the hostname below.**

## Public site (Squarespace)

- **Domain:** `<!-- YOUR DOMAIN HERE -->`
- **Registrar / site:** Squarespace
- **Purpose:** marketing, program story, contact, link-out to GitHub (`Die-Namic-Systems/terpsi-music`) — **no** roster, guardian, or student flows on this host.

## Product (not Squarespace)

The application hub is **on-prem** (see `ARCHITECTURE.md` §2–§3): plaintext stays in Zone A; guardians use the narrow relay (Zone B), not the marketing site. Do not point Squarespace forms or embeds at live program data without an explicit architecture review.

## Fleet parallels

| Product | Public face | App / data |
|---------|-------------|------------|
| UTETY | `utety.pages.dev` | `utety-chat` / campus |
| Terpsi | Squarespace + this domain | `terpsi-music` hub on org hardware |

## GitHub

- Repo target: `github.com/Die-Namic-Systems/terpsi-music`
- Optional: org **Verified domains** in GitHub Settings for the same hostname.

## DNS checklist (when you wire Squarespace)

- [ ] Apex + `www` (or chosen canonical) → Squarespace
- [ ] Document canonical URL in org `.github/profile/README.md` when profile is written
- [ ] No accidental CNAME of app/API hostnames to Squarespace unless that host is intentionally static-only
