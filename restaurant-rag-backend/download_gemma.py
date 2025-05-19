import os
from huggingface_hub import login
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 創建模型目錄
os.makedirs('models', exist_ok=True)

# 從環境變數獲取 Hugging Face token
hf_token = os.getenv("HUGGINGFACE_TOKEN")

# 登入 Hugging Face
print("登入 Hugging Face...")
login(token=hf_token)

# 下載 Gemma 2b 模型和分詞器
print("開始下載 Gemma 2b 模型和分詞器...")
model_name = "stvlynn/Gemma-2-2b-Chinese-it"
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("分詞器下載完成。現在下載模型（這可能需要一些時間）...")

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16
)

# 將模型保存到本地以避免重複下載
print("將模型和分詞器保存到本地...")
model.save_pretrained("models/gemma-2b")
tokenizer.save_pretrained("models/gemma-2b")

print("Gemma 2b 模型下載完成！")