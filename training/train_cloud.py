"""
training/train_cloud.py - One-Click Cloud API Fine-Tuning.
Supports OpenAI Fine-Tuning API (gpt-4o-mini) and Together AI Fine-Tuning (Llama-3.1-8B).
"""

import os
import sys
import time
import argparse
import json

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass

DATASET_FILE = os.path.join(os.path.dirname(__file__), "datasets", "train_openai.jsonl")


def train_openai(api_key: str, base_model: str = "gpt-4o-mini-2024-07-18"):
    """Launches fine-tuning on OpenAI cloud."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    print(f"🚀 [1/3] Uploading training dataset: {DATASET_FILE}...")
    with open(DATASET_FILE, "rb") as f:
        file_obj = client.files.create(file=f, purpose="fine-tune")
    file_id = file_obj.id
    print(f"✅ Uploaded file ID: {file_id}")

    print(f"⏳ [2/3] Creating Fine-Tuning job with base model '{base_model}'...")
    job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model=base_model,
        hyperparameters={"n_epochs": 3}
    )
    job_id = job.id
    print(f"✅ Fine-Tuning Job Created: {job_id}")

    print(f"📊 [3/3] Monitoring Training Progress (Press Ctrl+C to detach without stopping)...")
    while True:
        status_obj = client.fine_tuning.jobs.retrieve(job_id)
        status = status_obj.status
        print(f"Status: {status} ... (trained_tokens: {status_obj.trained_tokens or 0})")
        if status in ["succeeded", "failed", "cancelled"]:
            if status == "succeeded":
                ft_model = status_obj.fine_tuned_model
                print(f"\n🎉 SUCCESS! Your fine-tuned model is ready: {ft_model}")
                print(f"To use this in your agent, add to ai-agent/.env:")
                print(f"OPENAI_MODEL={ft_model}")
            else:
                print(f"\n❌ Job ended with status: {status}")
            break
        time.sleep(15)


def train_together(api_key: str, base_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Reference"):
    """Launches fine-tuning on Together AI cloud."""
    import requests

    headers = {"Authorization": f"Bearer {api_key}"}
    print(f"🚀 [1/3] Uploading dataset to Together AI...")
    with open(DATASET_FILE, "rb") as f:
        files = {"file": (os.path.basename(DATASET_FILE), f)}
        resp = requests.post("https://api.together.xyz/v1/files", headers=headers, files=files)
    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.text}")
        return
    file_id = resp.json()["id"]
    print(f"✅ Uploaded file ID: {file_id}")

    print(f"⏳ [2/3] Starting Llama 3.1 8B fine-tuning job...")
    payload = {
        "training_file": file_id,
        "model": base_model,
        "n_epochs": 3,
        "learning_rate": 1e-5
    }
    resp = requests.post("https://api.together.xyz/v1/fine-tunes", headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"❌ Fine-tune start failed: {resp.text}")
        return
    job_id = resp.json()["id"]
    print(f"✅ Job Created: {job_id}")


def main():
    parser = argparse.ArgumentParser(description="Cloud Fine-Tuning CLI")
    parser.add_argument("--provider", choices=["openai", "together"], default="openai")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", ""))
    parser.add_argument("--model", default="gpt-4o-mini-2024-07-18")
    args = parser.parse_args()

    if not os.path.exists(DATASET_FILE):
        print(f"Dataset not found at {DATASET_FILE}. Generating now...")
        from generate_complete_dataset import main as gen_main
        gen_main()

    if not args.api_key:
        print(f"\n⚠️  API Key required!")
        print(f"Usage:")
        print(f"  python training/train_cloud.py --provider openai --api-key YOUR_OPENAI_KEY")
        print(f"  python training/train_cloud.py --provider together --api-key YOUR_TOGETHER_KEY")
        return

    if args.provider == "openai":
        train_openai(args.api_key, args.model)
    elif args.provider == "together":
        train_together(args.api_key, args.model)


if __name__ == "__main__":
    main()
