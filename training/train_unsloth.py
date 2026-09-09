"""
training/train_unsloth.py - Ultra-Fast Low-Memory LoRA Fine-Tuning using Unsloth.
Can be run on Google Colab (Free T4 GPU) or any Linux NVIDIA GPU.
Trains Qwen 2.5 7B Instruct on our custom Hinglish Voice Agent Dataset.
"""

import os
import torch

def train():
    print("=====================================================")
    print("🚀 Starting Unsloth LoRA Fine-Tuning for Voice Agent")
    print("=====================================================")

    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import load_dataset
    except ImportError:
        print("❌ Unsloth not installed! Install via:")
        print("pip install --no-deps 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'")
        print("pip install --no-deps trl peft accelerate bitsandbytes")
        return

    max_seq_length = 2048
    dtype = None # Auto detection (Float16 for T4, Bfloat16 for A100)
    load_in_4bit = True # 4bit quantization fits in 8GB - 16GB VRAM

    # 1. Load Pre-trained Base Model (Qwen 2.5 7B Instruct is ideal for Hinglish)
    model_name = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
    print(f"📦 Loading base model: {model_name}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )

    # 2. Add LoRA Adapters (Targeting key attention & MLP matrices)
    print("🔧 Configuring LoRA parameters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16, # Rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0, # Optimized 0 dropout for Unsloth
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    # 3. Load & Format Dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "datasets", "train_chatml.jsonl")
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found at: {dataset_path}")
        return

    print(f"📖 Loading dataset from {dataset_path}...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    # 4. Initialize SFT Trainer
    output_dir = os.path.join(os.path.dirname(__file__), "output_voice_model")
    print(f"⚙️ Setting up SFT Trainer (output: {output_dir})...")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=60, # ~3 epochs over 80 samples
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=output_dir,
        ),
    )

    # 5. Train!
    print("🔥 Training started...")
    trainer.train()

    # 6. Save Model
    save_path = os.path.join(os.path.dirname(__file__), "lora_voice_agent")
    print(f"💾 Saving trained LoRA adapter to: {save_path}...")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)

    print("\n🎉 TRAINING COMPLETE! Your model is ready to run!")
    print(f"Adapter saved at: {save_path}")

if __name__ == "__main__":
    train()
