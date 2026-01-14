# IronClaw Garrison

Purpose: durable, non-Theater state for IronClaw.

This is where long-lived control-plane state will live (MVP-first):
- run/order ledger (SQLite)
- indexes/pointers to Theaters + Orders
- policy snapshots (optional)
- operational logs (optional)

Theaters remain git-durable execution spaces under `~/ironclaw/theaters/`.
