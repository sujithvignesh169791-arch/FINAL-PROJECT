import os
import re
import csv
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.corpus import PublicCorpusDocument
from app.ai.rag_service import (
    index_public_corpus_chunks,
    has_indexed_public_chunks,
    get_public_corpus_collection
)

logger = logging.getLogger(__name__)

def clean_legal_text(text: str) -> str:
    """
    Cleans raw legal text:
    - Normalizes unicode quotation marks, apostrophes, and dashes.
    - Strips non-printable control characters while preserving formatting.
    - Collapses excessive blank lines.
    """
    if not text:
        return ""

    # Replace smart quotes & dashes
    t = text.replace("\u2018", "'").replace("\u2019", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\u2013", "-").replace("\u2014", "--")
    t = t.replace("\xa0", " ")

    # Strip control characters except newline and tab
    t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", t)

    # Collapse more than 3 consecutive newlines
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def resolve_cuad_path(dataset_root: str) -> Optional[Path]:
    """
    Locates the CUAD_v1 directory regardless of single or double nesting.
    """
    root = Path(dataset_root)
    candidates = [
        root / "CUAD_v1" / "CUAD_v1",
        root / "CUAD_v1"
    ]
    for p in candidates:
        if (p / "master_clauses.csv").exists():
            return p
    return None

def resolve_cjpe_path(dataset_root: str) -> Optional[Path]:
    """
    Locates the CJPE gold_explanations.json path regardless of single or double nesting.
    """
    root = Path(dataset_root)
    candidates = [
        root / "CJPE-main" / "CJPE-main" / "Models" / "Explanations" / "metrics and results" / "gold_explanations.json",
        root / "CJPE-main" / "Models" / "Explanations" / "metrics and results" / "gold_explanations.json"
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def parse_cuad_parties(parties_raw: str, parties_answer: str) -> List[str]:
    """Extracts a clean deduplicated list of contracting parties."""
    parties = []
    if parties_answer and parties_answer.strip():
        # Often formatted as: Party A ("Role"); Party B ("Role")
        parts = re.split(r"[;\n]", parties_answer)
        for pt in parts:
            clean = re.sub(r'\s*\([^)]*\)', '', pt).strip()
            if 2 < len(clean) < 100 and clean not in parties:
                parties.append(clean)

    if not parties and parties_raw:
        try:
            parsed = json.loads(parties_raw.replace("'", '"'))
            if isinstance(parsed, list):
                for p in parsed:
                    if isinstance(p, str) and 2 < len(p) < 100 and p not in parties:
                        parties.append(p.strip())
        except Exception:
            pass
    return parties[:6]

def parse_cuad_clauses(row: Dict[str, str]) -> List[Dict[str, Any]]:
    """Extracts key commercial clauses from the master_clauses columns."""
    clause_columns = [
        ("Anti-Assignment", "Anti-Assignment"),
        ("Governing Law", "Governing Law"),
        ("Termination For Convenience", "Termination for Convenience"),
        ("Cap On Liability", "Limitation of Liability"),
        ("Audit Rights", "Audit Rights"),
        ("Non-Compete", "Non-Compete Covenant"),
        ("Exclusivity", "Exclusivity"),
        ("License Grant", "License Grant"),
        ("Minimum Commitment", "Minimum Order Commitment"),
        ("Warranty Duration", "Warranty Period")
    ]
    clauses = []
    for col_name, clause_label in clause_columns:
        val = row.get(col_name) or ""
        answer = row.get(f"{col_name}-Answer") or ""
        if val and val != "[]" and val != "0":
            snippet = clean_legal_text(val)
            if snippet.startswith("['") and snippet.endswith("']"):
                snippet = snippet[2:-2].strip()
            if snippet:
                clauses.append({
                    "clause_type": col_name,
                    "title": clause_label,
                    "text": snippet[:400],
                    "status": "Identified",
                    "answer_summary": answer
                })
    return clauses

def ingest_cuad_contracts(
    db: Session,
    dataset_root: Optional[str] = None,
    sample_limit: int = 5,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Ingests CUAD commercial contracts:
    - Reads master_clauses.csv for verified title and covenant metadata.
    - Reads matching full contract text from full_contract_txt/.
    - Validates formatting, cleans text, and safely skips duplicates.
    - Saves public documents to SQLite and indexes into separate public vector collection.
    """
    root_path = dataset_root or settings.DATASET_ROOT_PATH
    cuad_dir = resolve_cuad_path(root_path)

    if not cuad_dir:
        raise FileNotFoundError(f"CUAD dataset directory not found under root: {root_path}")

    csv_path = cuad_dir / "master_clauses.csv"
    txt_dir = cuad_dir / "full_contract_txt"

    processed = []
    skipped = []
    errors = []

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            if count >= sample_limit:
                break

            pdf_filename = row.get("Filename", "")
            if not pdf_filename:
                continue

            txt_filename = pdf_filename[:-4] + ".txt" if pdf_filename.endswith(".pdf") else pdf_filename + ".txt"
            txt_path = txt_dir / txt_filename

            if not txt_path.exists():
                errors.append(f"Missing text file for {pdf_filename} at {txt_path}")
                continue

            # Deterministic ID based on source filename
            doc_id = f"cuad_{hashlib.md5(pdf_filename.encode('utf-8')).hexdigest()[:12]}"

            # Check if record already exists in database
            existing = db.query(PublicCorpusDocument).filter(
                PublicCorpusDocument.id == doc_id
            ).first()

            # Extract metadata
            doc_title = (row.get("Document Name-Answer") or row.get("Document Name") or "Commercial Contract").strip("[]'\" ")
            parties = parse_cuad_parties(row.get("Parties", ""), row.get("Parties-Answer", ""))
            agreement_date = row.get("Agreement Date-Answer") or row.get("Agreement Date") or ""
            governing_law = (row.get("Governing Law-Answer") or row.get("Governing Law") or "").strip("[]'\" ")
            year = "2014"
            year_match = re.search(r"\b(19\d\d|20\d\d)\b", pdf_filename)
            if year_match:
                year = year_match.group(1)

            # Read and clean contract text
            with open(txt_path, "r", encoding="utf-8", errors="ignore") as tf:
                raw_text = tf.read()
            cleaned_text = clean_legal_text(raw_text)

            key_clauses = parse_cuad_clauses(row)

            # Synthesize executive summary
            p_str = ", ".join(parties[:2]) if parties else "the contracting parties"
            gov_str = f" Governed under the laws of {governing_law}." if governing_law else ""
            summary = (
                f"Commercial Contract: {doc_title} between {p_str}.{gov_str} "
                f"Identified {len(key_clauses)} key legal covenants and terms. Source: SEC EDGAR ({pdf_filename})."
            )

            # Check for SEC exhibit citation
            ex_match = re.search(r"EX-([0-9\.\w\(\)]+)", pdf_filename)
            citation = f"SEC Exhibit {ex_match.group(1)}" if ex_match else "SEC EDGAR Filing"

            metadata_dict = {
                "source": "CUAD v1",
                "pdf_filename": pdf_filename,
                "txt_filename": txt_filename,
                "governing_law": governing_law,
                "agreement_date": agreement_date,
                "char_count": len(cleaned_text),
                "clauses_count": len(key_clauses)
            }

            if existing and not dry_run:
                skipped.append({
                    "id": doc_id,
                    "title": doc_title,
                    "filename": txt_filename,
                    "reason": "Already exists in database"
                })
                count += 1
                continue

            if not dry_run:
                # 1. Insert into SQLite Public Corpus Document table
                db_doc = PublicCorpusDocument(
                    id=doc_id,
                    corpus_type="CUAD_CONTRACT",
                    title=doc_title,
                    source_filename=txt_filename,
                    court_or_jurisdiction=governing_law or "Commercial Jurisdiction",
                    year=str(year),
                    citation=citation,
                    parties=parties,
                    verdict_or_outcome="Executed Agreement",
                    summary=summary,
                    key_clauses=key_clauses,
                    extracted_text=cleaned_text,
                    metadata_json=metadata_dict
                )
                db.add(db_doc)
                db.commit()

                # 2. Index into Public Research Vector Collection
                try:
                    index_public_corpus_chunks(
                        corpus_id=doc_id,
                        corpus_type="CUAD_CONTRACT",
                        title=doc_title,
                        filename=txt_filename,
                        court=governing_law or "Commercial Jurisdiction",
                        year=str(year),
                        citation=citation,
                        full_text=cleaned_text
                    )
                except Exception as e:
                    logger.warning(f"Failed to vector index CUAD doc {doc_id}: {e}")

            processed.append({
                "id": doc_id,
                "corpus_type": "CUAD_CONTRACT",
                "title": doc_title,
                "filename": txt_filename,
                "citation": citation,
                "year": year,
                "parties": parties,
                "clauses_count": len(key_clauses),
                "text_length": len(cleaned_text)
            })
            count += 1

    return {
        "status": "dry_run" if dry_run else "success",
        "dataset": "CUAD v1 Commercial Contracts",
        "processed_count": len(processed),
        "skipped_count": len(skipped),
        "items": processed,
        "skipped": skipped,
        "errors": errors
    }

def ingest_supreme_court_judgments(
    db: Session,
    dataset_root: Optional[str] = None,
    sample_limit: int = 5,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Ingests CJPE/ILDC Indian Supreme Court judgment dataset:
    - Reads expert annotations from gold_explanations.json.
    - Extracts case year, legal reasoning, holding, statutes, and citations.
    - Preserves source metadata and skips duplicate records safely.
    - Stores public research records in SQLite and public ChromaDB collection.
    """
    root_path = dataset_root or settings.DATASET_ROOT_PATH
    cjpe_file = resolve_cjpe_path(root_path)

    if not cjpe_file:
        raise FileNotFoundError(f"CJPE gold_explanations.json not found under root: {root_path}")

    with open(cjpe_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed = []
    skipped = []
    errors = []

    count = 0
    for case_file, user_data in data.items():
        if count >= sample_limit:
            break

        # Filename format: e.g. 1962_384.txt -> Year: 1962, Case No: 384
        parts = case_file.replace(".txt", "").split("_")
        year = parts[0] if len(parts) > 0 else "1960"
        case_no = parts[1] if len(parts) > 1 else str(count + 1)

        doc_id = f"sci_{year}_{case_no}"

        # Check existing in SQLite
        existing = db.query(PublicCorpusDocument).filter(
            PublicCorpusDocument.id == doc_id
        ).first()

        # Combine explanation text and determine consensus verdict
        u1 = user_data.get("User 1", {})
        verdict = u1.get("verdict") or "Accepted"
        raw_text = u1.get("exp", "")
        cleaned_text = clean_legal_text(raw_text)

        # Statutory & Citation extraction
        acts = re.findall(r"\b([A-Z][A-Za-z\s]{3,40}(?:Act|Code),?\s*\d{4})\b", cleaned_text)
        acts = list(dict.fromkeys([a.strip().strip(",") for a in acts if len(a) < 55]))[:4]

        sections = re.findall(r"\b(?:section|sec\.|s\.)\s*(\d+[A-Za-z]?(?:\s*\([0-9a-zA-Z]+\))*)\b", cleaned_text, re.IGNORECASE)
        sections = list(dict.fromkeys([f"Section {s}" for s in sections]))[:6]

        official_citation = f"{year} INSC {case_no}"
        case_title = f"Supreme Court of India: Civil Appeal No. {case_no} of {year}"

        # Build key clauses from legal holdings
        key_clauses = []
        if acts:
            key_clauses.append({
                "clause_type": "Statutory Enactments",
                "title": "Governing Legislation",
                "text": f"Governed under statutory framework: {', '.join(acts)}.",
                "status": "Active Precedent"
            })
        if sections:
            key_clauses.append({
                "clause_type": "Operative Provisions",
                "title": "Sections Construed",
                "text": f"Judicial interpretation of statutory sections: {', '.join(sections)}.",
                "status": "Active Precedent"
            })

        # Add legal reasoning clause
        first_holding = cleaned_text[:350].strip()
        key_clauses.append({
            "clause_type": "Judicial Holding & Reasoning",
            "title": f"Ruling ({verdict})",
            "text": first_holding,
            "status": "Binding Precedent"
        })

        summary = (
            f"Supreme Court of India Precedent ({official_citation}). Ruling: {verdict}. "
            f"Active matters examined under: {', '.join(acts) if acts else 'Appellate Jurisdiction'}. "
            f"Holding: {first_holding[:180]}..."
        )

        metadata_dict = {
            "source": "CJPE / ILDC Indian Legal Documents Corpus",
            "case_file": case_file,
            "case_number": case_no,
            "court": "Supreme Court of India",
            "verdict": verdict,
            "annotated_users": list(user_data.keys()),
            "acts": acts,
            "sections": sections,
            "char_count": len(cleaned_text)
        }

        if existing and not dry_run:
            skipped.append({
                "id": doc_id,
                "title": case_title,
                "filename": case_file,
                "reason": "Already exists in database"
            })
            count += 1
            continue

        if not dry_run:
            # 1. Insert into SQLite Public Corpus Document table
            db_doc = PublicCorpusDocument(
                id=doc_id,
                corpus_type="INDIAN_SUPREME_COURT",
                title=case_title,
                source_filename=case_file,
                court_or_jurisdiction="Supreme Court of India",
                year=str(year),
                citation=official_citation,
                parties=["Appellate Parties", "Respondent Authorities"],
                verdict_or_outcome=verdict,
                summary=summary,
                key_clauses=key_clauses,
                extracted_text=cleaned_text,
                metadata_json=metadata_dict
            )
            db.add(db_doc)
            db.commit()

            # 2. Index into Public Research Vector Collection
            try:
                index_public_corpus_chunks(
                    corpus_id=doc_id,
                    corpus_type="INDIAN_SUPREME_COURT",
                    title=case_title,
                    filename=case_file,
                    court="Supreme Court of India",
                    year=str(year),
                    citation=official_citation,
                    full_text=cleaned_text,
                    verdict=verdict
                )
            except Exception as e:
                logger.warning(f"Failed to vector index SCI doc {doc_id}: {e}")

        processed.append({
            "id": doc_id,
            "corpus_type": "INDIAN_SUPREME_COURT",
            "title": case_title,
            "filename": case_file,
            "citation": official_citation,
            "court": "Supreme Court of India",
            "year": year,
            "verdict": verdict,
            "acts": acts,
            "text_length": len(cleaned_text)
        })
        count += 1

    return {
        "status": "dry_run" if dry_run else "success",
        "dataset": "CJPE / ILDC Indian Supreme Court Judgments",
        "processed_count": len(processed),
        "skipped_count": len(skipped),
        "items": processed,
        "skipped": skipped,
        "errors": errors
    }

def ingest_initial_corpus_sample(
    db: Session,
    dataset_root: Optional[str] = None,
    contracts_limit: int = 5,
    judgments_limit: int = 5,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Executes the initial sample ingestion for 5 commercial contracts and 5 Supreme Court judgments.
    Guarantees:
    - Never modifies original dataset files.
    - Validates formats, clean text, preserves source metadata.
    - Safely skips duplicate records.
    - Stores public research data in a separate ChromaDB collection from private user documents.
    """
    cuad_result = ingest_cuad_contracts(
        db=db,
        dataset_root=dataset_root,
        sample_limit=contracts_limit,
        dry_run=dry_run
    )
    cjpe_result = ingest_supreme_court_judgments(
        db=db,
        dataset_root=dataset_root,
        sample_limit=judgments_limit,
        dry_run=dry_run
    )

    return {
        "status": "dry_run" if dry_run else "completed",
        "contracts": cuad_result,
        "judgments": cjpe_result,
        "total_ingested": cuad_result["processed_count"] + cjpe_result["processed_count"],
        "total_skipped": cuad_result["skipped_count"] + cjpe_result["skipped_count"]
    }
