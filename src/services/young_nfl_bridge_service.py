from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.utils.scoring import clamp_score

YOUNG_NFL_BRIDGE_MODEL_VERSION = "young_nfl_bridge_v1_0_0"


@dataclass(frozen=True)
class YoungNFLBridgePrior:
    player_id: str
    player_name: str
    position: str
    experience_bucket: str
    draft_year: int | None
    draft_round: int | None
    draft_overall: int | None
    draft_capital_prior_score: float
    rookie_prior_score: float
    base_decay_weight: float
    nfl_evidence_weight: float
    bridge_weight: float
    source: str
    notes: str


def young_nfl_bridge_prior_from_row(
    row: dict[str, object],
    *,
    season: int | None = None,
) -> YoungNFLBridgePrior:
    resolved_season = season or _int(row.get("season"), 0) or 2026
    draft_year = _int(row.get("draft_year"), None)
    draft_round = _int(row.get("draft_round"), None)
    draft_overall = _int(
        row.get("draft_overall")
        or row.get("draft_ovr")
        or row.get("draft_pick_overall"),
        None,
    )
    years_exp = _int(row.get("years_exp"), None)
    bucket = str(row.get("experience_bucket") or "") or experience_bucket(
        season=resolved_season,
        draft_year=draft_year,
        years_exp=years_exp,
    )
    base_weight = bridge_weight_for_bucket(bucket)
    nfl_evidence = nfl_evidence_weight(row)
    explicit_weight = _manual_bridge_weight(row)
    weight = (
        clamp_score(explicit_weight, 0.0, 1.0)
        if explicit_weight is not None
        else decayed_bridge_weight(bucket=bucket, nfl_evidence_weight=nfl_evidence)
    )
    capital = draft_capital_prior_score(
        position=str(row.get("position") or ""),
        draft_round=draft_round,
        draft_overall=draft_overall,
    )
    explicit_prior = _float(row.get("young_nfl_bridge_prior_score"), None)
    prior = (
        clamp_score(explicit_prior)
        if explicit_prior is not None
        else rookie_prior_score(
            position=str(row.get("position") or ""),
            draft_round=draft_round,
            draft_overall=draft_overall,
            draft_capital_prior=capital,
            rookie_model_grade=_float(row.get("rookie_model_grade"), None),
            prospect_grade=_float(row.get("prospect_grade"), None),
        )
    )
    if not draft_year and prior == 50.0:
        weight = 0.0
    return YoungNFLBridgePrior(
        player_id=str(row.get("player_id") or row.get("sleeper_id") or row.get("gsis_id") or ""),
        player_name=str(row.get("player_name") or row.get("name") or ""),
        position=str(row.get("position") or ""),
        experience_bucket=bucket,
        draft_year=draft_year,
        draft_round=draft_round,
        draft_overall=draft_overall,
        draft_capital_prior_score=round(capital, 2),
        rookie_prior_score=round(prior, 2),
        base_decay_weight=round(base_weight, 3),
        nfl_evidence_weight=round(nfl_evidence, 3),
        bridge_weight=round(weight, 3),
        source=_bridge_source(row),
        notes=_bridge_notes(bucket, weight, nfl_evidence),
    )


def experience_bucket(
    *,
    season: int,
    draft_year: int | None = None,
    years_exp: int | None = None,
) -> str:
    if draft_year:
        year_delta = season - draft_year
        if year_delta <= 0:
            return "true_rookie"
        if year_delta == 1:
            return "year_one_nfl_player"
        if year_delta == 2:
            return "year_two_nfl_player"
        if year_delta == 3:
            return "year_three_nfl_player"
        return "established_veteran"
    if years_exp is not None:
        if years_exp <= 0:
            return "true_rookie"
        if years_exp == 1:
            return "year_one_nfl_player"
        if years_exp == 2:
            return "year_two_nfl_player"
        if years_exp == 3:
            return "year_three_nfl_player"
    return "established_veteran"


def bridge_weight_for_bucket(bucket: str) -> float:
    return {
        "true_rookie": 1.00,
        "year_one_nfl_player": 0.35,
        "year_two_nfl_player": 0.20,
        "year_three_nfl_player": 0.08,
    }.get(bucket, 0.0)


def decayed_bridge_weight(*, bucket: str, nfl_evidence_weight: float) -> float:
    base_weight = bridge_weight_for_bucket(bucket)
    if base_weight <= 0 or bucket == "true_rookie":
        return base_weight
    decay_rate = {
        "year_one_nfl_player": 0.45,
        "year_two_nfl_player": 0.55,
        "year_three_nfl_player": 0.60,
    }.get(bucket, 0.0)
    decayed = base_weight * (1.0 - (clamp_score(nfl_evidence_weight, 0.0, 1.0) * decay_rate))
    return clamp_score(decayed, 0.0, base_weight)


def nfl_evidence_weight(row: dict[str, object]) -> float:
    warnings = {part for part in str(row.get("warnings") or "").split("|") if part}
    evidence_fields = {
        "weighted_recent_lve_ppg_score": {"missing_lve_scoring_history"},
        "expected_lve_points_score": {"missing_projection_features"},
        "lve_projection_value": {"missing_projection_features"},
        "role_security": {"missing_participation_proxy", "missing_role_usage"},
    }
    present = 0
    for field, blocking_warnings in evidence_fields.items():
        if _float(row.get(field), None) is None:
            continue
        if warnings.intersection(blocking_warnings):
            continue
        present += 1
    presence_score = present / len(evidence_fields)
    missing_warning_count = sum(
        1
        for warning in warnings
        if warning.startswith("missing_") or warning.startswith("imputed_")
    )
    warning_penalty = min(0.30, missing_warning_count * 0.08)
    confidence = _float(row.get("confidence"), None)
    confidence_factor = 0.0 if confidence is None else clamp_score(confidence, 0.0, 100.0) / 100.0
    evidence = (presence_score * 0.70) + (confidence_factor * 0.30) - warning_penalty
    return round(clamp_score(evidence, 0.0, 1.0), 3)


def rookie_prior_score(
    *,
    position: str,
    draft_round: int | None,
    draft_overall: int | None,
    draft_capital_prior: float | None = None,
    rookie_model_grade: float | None = None,
    prospect_grade: float | None = None,
) -> float:
    capital = (
        clamp_score(draft_capital_prior)
        if draft_capital_prior is not None
        else draft_capital_prior_score(
            position=position,
            draft_round=draft_round,
            draft_overall=draft_overall,
        )
    )
    evidence: list[tuple[float, float]] = [(capital, 70.0)]
    if rookie_model_grade is not None:
        evidence.append((clamp_score(rookie_model_grade), 25.0))
    if prospect_grade is not None:
        evidence.append((clamp_score(prospect_grade), 15.0))
    total_weight = sum(weight for _, weight in evidence)
    return clamp_score(sum(score * weight for score, weight in evidence) / total_weight)


def draft_capital_prior_score(
    *,
    position: str,
    draft_round: int | None,
    draft_overall: int | None,
) -> float:
    if draft_overall:
        if draft_overall <= 10:
            base = 96.0
        elif draft_overall <= 32:
            base = 90.0
        elif draft_overall <= 64:
            base = 82.0
        elif draft_overall <= 100:
            base = 72.0
        elif draft_overall <= 150:
            base = 60.0
        elif draft_overall <= 224:
            base = 48.0
        else:
            base = 40.0
    elif draft_round:
        base = {
            1: 89.0,
            2: 81.0,
            3: 70.0,
            4: 58.0,
            5: 48.0,
            6: 42.0,
            7: 38.0,
        }.get(draft_round, 35.0)
    else:
        base = 50.0
    position_key = position.upper()
    if position_key == "QB" and base < 90.0:
        base -= 6.0
    elif position_key == "RB":
        if base >= 72.0:
            base += 1.0
        elif base < 58.0:
            base -= 4.0
    elif position_key == "WR":
        if base >= 82.0:
            base += 0.0
        elif base < 58.0:
            base -= 2.0
    elif position_key == "TE":
        if base < 90.0:
            base -= 5.0
    return clamp_score(base)


def blend_with_bridge_prior(
    *,
    nfl_value: float,
    bridge_prior: YoungNFLBridgePrior,
) -> float:
    weight = bridge_prior.bridge_weight
    if weight <= 0:
        return clamp_score(nfl_value)
    return clamp_score(
        (nfl_value * (1.0 - weight))
        + (bridge_prior.rookie_prior_score * weight)
    )


def load_young_nfl_bridge_priors(
    source_dir: str | Path,
    *,
    season: int = 2026,
) -> dict[str, YoungNFLBridgePrior]:
    source_path = Path(source_dir)
    rows = _rows_from_known_sources(source_path)
    output: dict[str, YoungNFLBridgePrior] = {}
    for row in rows:
        prior = young_nfl_bridge_prior_from_row(row, season=season)
        if prior.bridge_weight <= 0:
            continue
        for key in _candidate_keys(row):
            output.setdefault(key, prior)
    return output


def apply_bridge_metadata_to_rows(
    rows: list[dict[str, object]] | tuple[dict[str, object], ...],
    priors: dict[str, YoungNFLBridgePrior],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        prior = _prior_for_row(row, priors)
        updated = dict(row)
        if prior is not None:
            updated["experience_bucket"] = prior.experience_bucket
            updated["draft_year"] = prior.draft_year or ""
            updated["draft_round"] = prior.draft_round or ""
            updated["draft_overall"] = prior.draft_overall or ""
            updated["young_nfl_bridge_prior_score"] = prior.rookie_prior_score
            updated["young_nfl_bridge_weight"] = prior.bridge_weight
            updated["young_nfl_bridge_source"] = prior.source
            warnings = {
                warning
                for warning in str(updated.get("warnings") or "").split("|")
                if warning
            }
            if prior.bridge_weight > 0:
                warnings.add("young_nfl_bridge_prior_active")
            updated["warnings"] = "|".join(sorted(warnings))
        else:
            updated.setdefault("experience_bucket", "established_veteran")
            updated.setdefault("young_nfl_bridge_prior_score", "")
            updated.setdefault("young_nfl_bridge_weight", "")
            updated.setdefault("young_nfl_bridge_source", "")
        output.append(updated)
    return output


def _prior_for_row(
    row: dict[str, object],
    priors: dict[str, YoungNFLBridgePrior],
) -> YoungNFLBridgePrior | None:
    for key in _candidate_keys(row):
        prior = priors.get(key)
        if prior is not None:
            return prior
    return None


def _candidate_keys(row: dict[str, object]) -> tuple[str, ...]:
    keys: list[str] = []
    for field in ("sleeper_id", "player_id", "gsis_id", "pfr_id"):
        value = str(row.get(field) or "")
        if value:
            keys.append(f"{field}:{value}")
    name = _clean_name(str(row.get("player_name") or row.get("name") or ""))
    position = str(row.get("position") or "")
    if name and position:
        keys.append(f"name_position:{name}|{position}")
    return tuple(keys)


def _rows_from_known_sources(source_path: Path) -> list[dict[str, object]]:
    candidates = (
        source_path / "downloads" / "dynastyprocess_db_playerids.csv",
        source_path / "draft_pool_downloads" / "dynastyprocess_db_playerids.csv",
        source_path / "dynastyprocess_db_playerids.csv",
    )
    for path in candidates:
        if path.exists():
            return _read_csv(path)
    return []


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bridge_source(row: dict[str, object]) -> str:
    if row.get("rookie_model_grade"):
        return "rookie_model_grade_plus_draft_capital"
    if row.get("prospect_grade"):
        return "prospect_grade_plus_draft_capital"
    if row.get("draft_year") or row.get("draft_round") or row.get("draft_ovr"):
        return "draft_capital_prior"
    return "none"


def _manual_bridge_weight(row: dict[str, object]) -> float | None:
    source = str(row.get("young_nfl_bridge_weight_source") or "").strip().lower()
    if source not in {"manual", "manual_override", "approved_override"}:
        return None
    return _float(row.get("young_nfl_bridge_weight"), None)


def _bridge_notes(bucket: str, weight: float, nfl_evidence: float) -> str:
    if weight <= 0:
        return "No young-player bridge applied."
    return (
        f"{bucket}: rookie/draft prior weight is {weight:.3f}; NFL evidence "
        f"weight is {nfl_evidence:.3f}, so the prior decays as production, "
        "role, usage, and injury evidence becomes clearer."
    )


def _clean_name(value: str) -> str:
    lowered = value.lower().strip()
    for suffix in (" jr.", " sr.", " iii", " ii", " iv"):
        lowered = lowered.replace(suffix, "")
    return " ".join(lowered.replace(".", "").split())


def _int(value: object, default: int | None) -> int | None:
    try:
        text = str(value)
        if text in {"", "NA", "nan", "None"}:
            return default
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _float(value: object, default: float | None) -> float | None:
    try:
        text = str(value)
        if text in {"", "NA", "nan", "None"}:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default
