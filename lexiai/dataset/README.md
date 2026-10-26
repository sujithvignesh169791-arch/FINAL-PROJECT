# LEXIAI Legal Dataset for Model Training & Fine-Tuning

This dataset directory contains curated, high-quality legal datasets formatted for fine-tuning Large Language Models (e.g. Llama 3, Mistral, Gemini, Nemotron) and evaluating RAG systems.

## Directory Structure

```
dataset/
├── README.md                 # Documentation and training guidelines
├── prepare_dataset.py        # Dataset validation and token counting utility
├── train.jsonl               # Supervised fine-tuning (SFT) training split
├── val.jsonl                 # Evaluation / validation split
├── contracts/                # Benchmark legal contracts in text format
│   ├── master_services_agreement.txt
│   ├── non_disclosure_agreement.txt
│   ├── commercial_lease.txt
│   └── software_saas_agreement.txt
├── risk_clauses/             # Labeled risk clauses with severity ratings
│   └── labeled_clauses.json
└── qa_pairs/                 # Legal comprehension and RAG Q&A pairs
    └── contract_qa.json
```

## Dataset Format

The fine-tuning files (`train.jsonl` and `val.jsonl`) adhere to the standard multi-turn chat format:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are LEXIAI, a specialized legal analysis assistant..."
    },
    {
      "role": "user",
      "content": "Analyze the following indemnification clause: [CLAUSE TEXT]"
    },
    {
      "role": "assistant",
      "content": "{\"clause_type\": \"Indemnity\", \"risk_level\": \"Critical\", \"summary\": \"...\"}"
    }
  ]
}
```

## How to Train / Fine-Tune

### 1. Preprocessing and Validation
Run the dataset preparation script:
```bash
python prepare_dataset.py
```

### 2. Fine-Tuning with Unsloth / Hugging Face SFTTrainer
```python
from datasets import load_dataset
from trl import SFTTrainer

dataset = load_dataset("json", data_files={"train": "train.jsonl", "validation": "val.jsonl"})
# Use SFTTrainer with your base LLM (Llama-3, Mistral, Nemotron)
```

### 3. OpenAI / Gemini Fine-Tuning
Upload `train.jsonl` directly via the OpenAI or Google Cloud GenAI fine-tuning CLI/Console.
