import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from huggingface_hub import login
import os
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


class FineTunedLlama:
    def __init__(self, base_model: str, finetuned_dir: str, merge: bool = False):
        """
        Load base model + fine-tuned LoRA adapter.

        Args:
            base_model (str): Hugging Face model id of base model
            finetuned_dir (str): Path to fine-tuned adapter directory
            merge (bool): Whether to merge LoRA weights into base model.
                          Set to False to fix the KeyError.
        """
        self.base_model_name = base_model
        self.finetuned_dir = finetuned_dir

        # --- Load tokenizer ---
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        # --- Load base model ---

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model,
            device_map="cpu",
            torch_dtype=torch.float32,  # 👈 force fp16 instead of bf16
        )

        # --- Load LoRA adapter onto the base model ---
        # The KeyError is caused by the merge operation, so we only load the adapter.
        # The PeftModel wrapper will handle the inference with the adapter weights.
        model = PeftModel.from_pretrained(base_model, finetuned_dir)

        # --- Optionally merge LoRA ---
        # We set the default to False to fix the KeyError.
        # If the user explicitly sets it to True, it will still attempt the merge.
        if merge:
            model = model.merge_and_unload()

        self.model = model

    def ask(self, query: str, max_new_tokens: int = 256,
            temperature: float = 0.7, top_p: float = 0.9) -> str:
        """
        Generate response from the fine-tuned model.

        Args:
            query (str): User query
            max_new_tokens (int): Max tokens to generate
            temperature (float): Sampling temperature
            top_p (float): Nucleus sampling top_p

        Returns:
            str: Generated response
        """
        messages = [
            {"role": "system", "content": "You are a friendly and knowledgeable agriculture debt manager who advises farmers."},
            {"role": "user", "content": query}
        ]

        # Format input using chat template
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True
            )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


def huggingFaceAuth():
    """
    Authenticate with Hugging Face using the token stored in the environment variable.
    
    Returns:
        bool: True if authentication is successful, False otherwise.
    """
    try:
        token = os.getenv("HUGGINGFACE_TOKEN")
        if not token:
            raise ValueError("HUGGINGFACE_TOKEN environment variable not set.")
        login(token=token)
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False

# --- If run as script ---
if __name__ == "__main__":
    huggingFaceAuth()

    BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    FINETUNED_DIR = str(Path(__file__).resolve().parent / "adapter")


    # Pass merge=False to the constructor to avoid the KeyError
    llama = FineTunedLlama(BASE_MODEL, FINETUNED_DIR, merge=False)

    response = llama.ask("I have a loan of ₹50,000 and expect a yield of 2 tons of wheat. How should I plan my repayment?")
    print("\n--- Model Response ---\n")
    print(response)

