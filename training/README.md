# AI Voice Agent Training & Fine-Tuning Guide 🚀

This directory contains the pipeline for collecting, formatting, training, and evaluating custom fine-tuned LLMs for your Voice Agent.

---

## 📁 Directory Structure
```
ai-agent/training/
├── dataset_collector.py   # Extracts real call logs into OpenAI / ChatML JSONL format
├── evaluate.py            # Automated offline benchmark for voice criteria (latency, tone, memory)
├── datasets/              # Generated JSONL training & evaluation sets (auto-created)
└── README.md              # Complete step-by-step training guide
```

---

## 1. Why Fine-Tune vs Prompt Engineering?
- **Prompt Engineering** (What we currently use):
  - Fast, zero GPU cost, works instantly with Groq/OpenAI.
  - Good for rapid iteration, but uses more tokens and can occasionally drift if instructions get too long.
- **Fine-Tuning (Your Next Big Step)**:
  - Bakes the persona's Hinglish tone, kids curriculum progression, and concise voice style directly into the model's weights.
  - Reduces prompt size (saving cost & latency).
  - Guarantees replies $\le 25$ words and 100% adherence to kids teaching rules.

---

## 2. Step 1: Generate & Curate Datasets

Run the dataset generator to extract real calls or create the initial seed dataset:
```bash
python training/dataset_collector.py
```
This generates `training/datasets/kids_learning_seed.jsonl` with standard ChatML conversation turns:
```json
{
  "messages": [
    {"role": "system", "content": "You are Puruva, an enthusiastic kids educator..."},
    {"role": "user", "content": "Mujhe ABCD padhna hai!"},
    {"role": "assistant", "content": "Yay! Chalo shuru karte hain! Bolo 'A'! A for Apple! Meetha meetha seb! Ab bolo 'A'!"}
  ]
}
```

---

## 3. Step 2: Recommended Base Models for Voice Agents
For real-time voice calls (latency < 400ms), choose lightweight, highly capable models:

| Model | Size | Strengths | Where to Host |
| :--- | :--- | :--- | :--- |
| **Qwen 2.5 7B / 3B** | 3B / 7B | Best multilingual (Hindi + English) open model | vLLM / Ollama / Groq |
| **Llama 3.1 8B Instruct** | 8B | Excellent reasoning & tool calling | Groq Custom Model / RunPod |
| **Mistral NeMo 12B** | 12B | High emotional nuance & natural conversation | vLLM |

---

## 4. Step 3: How to Fine-Tune (Free on Google Colab or Local GPU)

Use **Unsloth** (the fastest, memory-efficient LoRA fine-tuning framework):

1. Open Google Colab (Free T4 GPU or A100).
2. Install Unsloth:
   ```bash
   pip install --no-deps "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
   ```
3. Load base model `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`.
4. Train with `SFTTrainer` using your `training/datasets/train_chatml.jsonl`.
5. Save LoRA adapters or export to GGUF / 16-bit safetensors.

---

## 5. Step 4: Run Offline Benchmarks

Before deploying any model checkpoint to live users, test it against the benchmark suite:
```bash
python training/evaluate.py
```
The evaluator tests:
- **Speech Length**: Reply must be $\le 25$ words so it speaks quickly without boring the listener.
- **Teaching Progression**: Next letter must be introduced sequentially (A $\rightarrow$ B $\rightarrow$ C).
- **Family Entity Recall**: Must remember Mummy/Papa names and never ask *"unka naam kya hai"*.
- **Praise & Positive Reinforcement**: Encourages the child with stars and enthusiastic affirmations.

---

## 6. Step 5: Connect Your Trained Model to `ai-agent`

Once fine-tuned, you can serve it via:
1. **Ollama / vLLM (Local / Cloud GPU)**:
   - Set in `ai-agent/.env`:
     ```env
     LOCAL_LLM_URL=http://localhost:11434/v1
     DEFAULT_VOICE_MODEL=my-trained-qwen-kids
     ```
2. **Groq Cloud Fine-Tuning**:
   - If trained via Groq's custom model program, pass the custom model ID in `GROQ_MODEL`.
