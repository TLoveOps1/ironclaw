# garrison/co_service/playbooks.py
"""
Mission playbook registry for the CO service.

v0: only a single demo mission type:
    filesystem_agent.call_summary

This module is intentionally lightweight and side-effect free. It provides a
structured place to register mission types without changing core CO logic.
"""

from dataclasses import dataclass
from typing import Dict, Optional


FILESYSTEM_CALL_SUMMARY = "filesystem_agent.call_summary"


@dataclass(frozen=True)
class MissionPlaybook:
  """
  Minimal description of how CO should handle a mission type.

  This is deliberately high-level; the concrete orchestration steps
  (Vault calls, Worker dispatch, etc.) live in the existing CO logic.
  """

  mission_type: str
  description: str
  # For now, Worker mission_type is the same as the incoming mission_type,
  # but this allows CO to remap later if needed.
  worker_mission_type: str


PLAYBOOKS: Dict[str, MissionPlaybook] = {
  FILESYSTEM_CALL_SUMMARY: MissionPlaybook(
    mission_type=FILESYSTEM_CALL_SUMMARY,
    description=(
      "Call transcript → filesystem + bash → summary + action items. "
      "Worker uses a bash tool to explore inputs/ and context/ before answering."
    ),
    worker_mission_type=FILESYSTEM_CALL_SUMMARY,
  ),
}


def get_playbook(mission_type: str) -> Optional[MissionPlaybook]:
  """
  Look up a MissionPlaybook by mission_type.

  v0: single entry for filesystem_agent.call_summary.
  """
  return PLAYBOOKS.get(mission_type)
