import os
import json
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent

def validate_jsonl(file_path: Path):
    if not file_path.exists():
        print(f"[MISSING] {file_path.name}")
        return 0, 0

    valid_lines = 0
    total_tokens_approx = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "messages" in data and isinstance(data["messages"], list):
                    valid_lines += 1
                    # Rough token estimation (4 chars ~ 1 token)
                    char_count = sum(len(m.get("content", "")) for m in data["messages"])
                    total_tokens_approx += char_count // 4
                else:
                    print(f"Line {i} missing 'messages' list")
            except Exception as e:
                print(f"Error parsing line {i}: {e}")

    print(f"[VALID] {file_path.name}: {valid_lines} samples, ~{total_tokens_approx} tokens")
    return valid_lines, total_tokens_approx

def main():
    print("=" * 60)
    print("LEXIAI Legal Dataset Validation & Summary")
    print("=" * 60)

    train_file = DATASET_DIR / "train.jsonl"
    val_file = DATASET_DIR / "val.jsonl"

    train_samples, train_tokens = validate_jsonl(train_file)
    val_samples, val_tokens = validate_jsonl(val_file)

    contracts = list((DATASET_DIR / "contracts").glob("*.txt"))
    print(f"[CONTRACTS] {len(contracts)} raw contract templates found in contracts/")

    labeled_path = DATASET_DIR / "risk_clauses" / "labeled_clauses.json"
    if labeled_path.exists():
        with open(labeled_path, "r", encoding="utf-8") as f:
            labeled = json.load(f)
            print(f"[RISK CLAUSES] {len(labeled)} annotated risk clauses in risk_clauses/labeled_clauses.json")

    qa_path = DATASET_DIR / "qa_pairs" / "contract_qa.json"
    if qa_path.exists():
        with open(qa_path, "r", encoding="utf-8") as f:
            qa = json.load(f)
            print(f"[QA PAIRS] {len(qa)} verified Q&A pairs in qa_pairs/contract_qa.json")

    print("\nDataset ready for LLM fine-tuning and evaluation.")
    print("=" * 60)

if __name__ == "__main__":
    main()
