from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
import gc

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:1024"

def load_model(model_path):
    if not os.path.exists(model_path):
        os.mkdir(model_path)
        # before downloading the Llama-2-13b
        model_16bit = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-13b-hf", torch_dtype=torch.float16)
        tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-13b-hf")
        model_16bit.save_pretrained(model_path)
        tokenizer.save_pretrained(model_path)
    else:
        # after downloading the Llama-2-13b
        model_16bit = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
    gc.collect()
    torch.cuda.empty_cache()
    model_16bit = model_16bit.to('cuda:0')
    tokenizer.pad_token_id = tokenizer.eos_token_id
    return model_16bit, tokenizer

def input_and_output(prompt, model, tokenizer):
    inputs = tokenizer(prompt, return_token_type_ids=False, return_tensors="pt").to('cuda:0')
    outputs = model.generate(**inputs, max_new_tokens=max(100, len(inputs)), temperature=0.1)
    results = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    result = results[0][len(prompt):]
    return result