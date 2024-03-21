from transformers import LlamaForCausalLM, LlamaConfig,LlamaTokenizer
from accelerate import init_empty_weights,infer_auto_device_map,load_checkpoint_in_model,dispatch_model
import torch
import os
import socket

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:1024"

def load_model(model_path):
    if not os.path.exists(model_path):
        # before downloading the Llama-2-70b
        model_16bit = LlamaForCausalLM.from_pretrained("meta-llama/Llama-2-70b-chat-hf", torch_dtype=torch.float16)
        tokenizer = LlamaTokenizer.from_pretrained("meta-llama/Llama-2-70b-chat-hf")
        model_16bit.save_pretrained(model_path)
        tokenizer.save_pretrained(model_path)
        config = LlamaConfig.from_pretrained(model_path)
    else:
        config = LlamaConfig.from_pretrained(model_path)
        with init_empty_weights():
            model_16bit = LlamaForCausalLM._from_config(config, torch_dtype=torch.float16) #torch_dtype=torch.float16这个很重要
    cuda_list = '0,1,2'.split(',')
    memory = '60GiB'
    max_memory = {int(cuda):memory for cuda in cuda_list}
    device_map = infer_auto_device_map(model_16bit, max_memory=max_memory,no_split_module_classes=LlamaForCausalLM._no_split_modules) #自动划分每个层的设备
    model_16bit = LlamaForCausalLM.from_pretrained(model_path, config=config, device_map=device_map, torch_dtype=torch.float16)
    tokenizer = LlamaTokenizer.from_pretrained(model_path)
    tokenizer.pad_token_id = tokenizer.eos_token_id
    return model_16bit, tokenizer

def input_and_output(prompt, model, tokenizer):
    inputs = tokenizer(prompt, return_token_type_ids=False, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=max(30, len(inputs)),temperature=0.1)
    results = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    result = results[0][len(prompt):]
    return result

def connect():
    client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    ip_port=('210.28.135.117',45771)
    client.connect(ip_port)
    return client

def send_and_receive(prompt, client):
    client.send(prompt.encode('utf-8'))#将发送的数据进行编码
    result=client.recv(4096)#接受服务端的信息，最大数据为1k
    result = result.decode('utf-8')
    return result
        