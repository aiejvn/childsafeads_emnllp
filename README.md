# childsafeads_emnllp
CAL Submission(s) and work for ChildSafeAds@EMNLLP

Get started: 

```
unzip public_data_dev.zip -d public_data_dev
```

* Baselines:
    * zero-shot prompting (public models)
    * ai4law RAG pipeline (for sub-task 3 bc it seems to have a RAG component)
    * (waiting on help from another student) fine-tune a small model, e.g. do LoRA on qwen3.5 or do fine-tuning on BERT. Some base models:
        * roBERTa (BERT but optimized): https://huggingface.co/FacebookAI/roberta-base
        * legal-bert: https://huggingface.co/nlpaueb/legal-bert-base-uncased
        * qwen3.5-4b (there's also 2b and 0.8b): Qwen/Qwen3.5-4B · Hugging Face
        * for LoRA, take the zero-shot prompt template as input + format the gold label as a piece of generated text (e.g. The answer is <gold label>)+ try to train the model over the cross-entropy loss of generating the gold label
        * huggingface has a tutorial here: https://huggingface.co/docs/peft/main/en/conceptual_guides/lora