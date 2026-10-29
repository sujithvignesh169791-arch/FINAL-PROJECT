import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class HighCourtMetadataService:
    """
    Service for inspecting, filtering, and navigating Indian High Court metadata
    including court codes, benches, jurisdictions, and standard case type dropdowns.
    """
    def __init__(self, dataset_root: Optional[str] = None):
        self.dataset_root = Path(dataset_root or settings.DATASET_ROOT_PATH)
        self._loaded = False
        self._courts: Dict[str, Dict[str, Any]] = {}
        self._benches: List[Dict[str, Any]] = []
        self._case_types: List[Dict[str, Any]] = []
        self._state_map: Dict[str, str] = {}

    def _resolve_file(self, relative_candidates: List[str]) -> Optional[Path]:
        for candidate in relative_candidates:
            path = self.dataset_root / candidate
            if path.exists():
                return path
        return None

    def load(self, force: bool = False) -> None:
        if self._loaded and not force:
            return

        # 1. Load ecourts courts.csv for state mapping
        ecourts_path = self._resolve_file([
            "ecourts-main/ecourts-main/courts.csv",
            "ecourts-main/courts.csv"
        ])
        if ecourts_path:
            try:
                with open(ecourts_path, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get("name", "")
                        state = row.get("state_name", "")
                        if name and state:
                            # Normalize court name to state
                            for key_fragment in ["Allahabad", "Bombay", "Calcutta", "Delhi", "Gujarat", 
                                                 "Karnataka", "Kerala", "Madras", "Patna", "Rajasthan"]:
                                if key_fragment.lower() in name.lower():
                                    self._state_map[key_fragment.lower()] = state
            except Exception as e:
                logger.warning(f"Could not parse ecourts courts.csv: {e}")

        # 2. Load court-codes.json
        court_codes_path = self._resolve_file([
            "indian-high-court-judgments-main/indian-high-court-judgments-main/court-codes.json",
            "indian-high-court-judgments-main/court-codes.json"
        ])
        if court_codes_path:
            try:
                with open(court_codes_path, mode="r", encoding="utf-8") as f:
                    codes = json.load(f)
                    for code_str, court_name in codes.items():
                        s3_code = code_str.replace("~", "_")
                        # Infer state
                        state = "India"
                        for frag, st in self._state_map.items():
                            if frag in court_name.lower():
                                state = st
                                break

                        self._courts[code_str] = {
                            "court_code": code_str,
                            "s3_court_code": s3_code,
                            "court_name": court_name,
                            "state_name": state,
                            "benches": [],
                            "case_types_count": 0
                        }
            except Exception as e:
                logger.warning(f"Could not parse court-codes.json: {e}")

        # 3. Load bench-codes.json
        bench_codes_path = self._resolve_file([
            "indian-high-court-judgments-main/indian-high-court-judgments-main/bench-codes.json",
            "indian-high-court-judgments-main/bench-codes.json"
        ])
        if bench_codes_path:
            try:
                with open(bench_codes_path, mode="r", encoding="utf-8") as f:
                    benches = json.load(f)
                    for bench_key, s3_code in benches.items():
                        # Find parent court
                        court_code = s3_code.replace("_", "~")
                        court_info = self._courts.get(court_code)
                        court_name = court_info["court_name"] if court_info else f"High Court ({s3_code})"

                        bench_item = {
                            "bench_key": bench_key,
                            "s3_court_code": s3_code,
                            "court_code": court_code,
                            "court_name": court_name
                        }
                        self._benches.append(bench_item)
                        if court_info:
                            court_info["benches"].append(bench_key)
            except Exception as e:
                logger.warning(f"Could not parse bench-codes.json: {e}")

        # 4. Load case types CSV
        case_types_path = self._resolve_file([
            "indian-high-court-judgments-main/indian-high-court-judgments-main/highcourt_case_type_dropdown_full.csv",
            "indian-high-court-judgments-main/highcourt_case_type_dropdown_full.csv"
        ])
        if case_types_path:
            try:
                with open(case_types_path, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        r_code = row.get("repo_court_code", "")
                        c_type = {
                            "court_code": r_code,
                            "s3_court_code": row.get("s3_court_code", ""),
                            "court_name": row.get("repo_court_name", ""),
                            "bench_name": row.get("portal_bench_name", ""),
                            "case_type_code": row.get("title_prefix_candidate", "") or row.get("case_type_option_value", ""),
                            "case_type_label": row.get("case_type_option_label", ""),
                            "description": row.get("case_type_description_candidate", "")
                        }
                        self._case_types.append(c_type)
                        if r_code in self._courts:
                            self._courts[r_code]["case_types_count"] += 1
            except Exception as e:
                logger.warning(f"Could not parse highcourt_case_type_dropdown_full.csv: {e}")

        self._loaded = True
        logger.info(
            f"HighCourtMetadataService initialized with {len(self._courts)} courts, "
            f"{len(self._benches)} benches, and {len(self._case_types)} case types."
        )

    def get_all_high_courts(self) -> List[Dict[str, Any]]:
        self.load()
        return [
            {
                "court_code": c["court_code"],
                "s3_court_code": c["s3_court_code"],
                "court_name": c["court_name"],
                "state_name": c["state_name"],
                "bench_count": len(c["benches"]),
                "case_types_count": c["case_types_count"]
            }
            for c in sorted(self._courts.values(), key=lambda x: x["court_name"])
        ]

    def get_benches(self, court_code: Optional[str] = None) -> List[Dict[str, Any]]:
        self.load()
        if not court_code:
            return self._benches

        norm = court_code.strip().replace("_", "~")
        return [b for b in self._benches if b["court_code"] == norm or b["s3_court_code"] == court_code]

    def get_case_types(
        self,
        court_code: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        self.load()
        res = self._case_types
        if court_code:
            norm = court_code.strip().replace("_", "~")
            res = [c for c in res if c["court_code"] == norm or c["s3_court_code"] == court_code]

        if q and q.strip():
            query_term = q.strip().lower()
            res = [
                c for c in res
                if query_term in c["case_type_code"].lower()
                or query_term in c["case_type_label"].lower()
                or query_term in c["description"].lower()
            ]

        return res[:limit]

    def search_courts(self, query: str) -> List[Dict[str, Any]]:
        self.load()
        term = query.strip().lower()
        if not term:
            return self.get_all_high_courts()

        matches = []
        for c in self._courts.values():
            if (term in c["court_name"].lower() or
                term in c["state_name"].lower() or
                term in c["court_code"].lower() or
                any(term in b.lower() for b in c["benches"])):
                matches.append({
                    "court_code": c["court_code"],
                    "s3_court_code": c["s3_court_code"],
                    "court_name": c["court_name"],
                    "state_name": c["state_name"],
                    "bench_count": len(c["benches"]),
                    "case_types_count": c["case_types_count"]
                })
        return sorted(matches, key=lambda x: x["court_name"])

# Global singleton
_high_court_service: Optional[HighCourtMetadataService] = None

def get_high_court_service() -> HighCourtMetadataService:
    global _high_court_service
    if _high_court_service is None:
        _high_court_service = HighCourtMetadataService()
        _high_court_service.load()
    return _high_court_service
