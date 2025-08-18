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

    def ask(self, query: str, query_type: str, inputs: list = None,  max_new_tokens: int = 256,
            temperature: float = 0.3, top_p: float = 0.95) -> str:
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
        extra_context = ""
        if inputs:
            # filter out None values
            valid_inputs = [str(x) for x in inputs if x is not None]
            if valid_inputs:
                extra_context = "\nAdditional context: " + ", ".join(valid_inputs)

        if query_type == "agriculture":
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an agriculture expert for Madhya Pradesh, India. "
                        "You give clear, concise, and practical advice on crops like wheat, millets, lentils, sorghum, and maize. "
                        "Always provide actionable recommendations with numeric details in Indian context (₹, kg, acres, etc.). "
                        "Never repeat instructions or examples, just answer the farmer’s query directly."
                        "Also you will access to the farmer's predicted profits, loss and recommendations. So if there is a query about it you can read the extra information given to you."
                    )
                },
                {"role": "user", "content": "I have 2 acres of wheat. How much fertilizer should I apply?"},
                {"role": "assistant", "content": "For 2 acres of wheat in MP, apply about 100 kg nitrogen, 60 kg phosphorus, and 40 kg potassium. Split nitrogen into two doses: half at sowing, half at tillering."},
                {"role": "user", "content": "When should I irrigate my maize crop during the Kharif season?"},
                {"role": "assistant", "content": "For maize in MP during Kharif, irrigate every 7–10 days depending on rainfall. Critical stages are vegetative growth and flowering. Provide 1–2 inches of water per irrigation, preferably in early morning."},
                
                # 🔑 now insert the real farmer's query
                {"role": "user", "content": query}
            ]
        elif query_type == "finance":
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an agriculture debt management expert with 10+ years of experience "
                        "advising farmers in Madhya Pradesh, India. "
                        "You are friendly, concise, and practical. "
                        "Always provide actionable advice on loan repayment, subsidies, insurance, "
                        "and financial planning for farmers. "
                        "If numeric recommendations are given, use Indian formatting (₹12,345.00, 2 acres, 50 kg). "
                        "If the farmer’s question is unclear, ask for clarification politely. "
                        "Never repeat the instructions or examples in your response—just answer the query directly."
                    ),
                },
                # Example 1
                {"role": "user", "content": "I have a loan of ₹50,000 and expect a yield of 2 tons of wheat. How should I plan my repayment?"},
                {"role": "assistant", "content": "If your wheat sells at ₹20 per kg, 2 tons = ₹40,000. After deducting input costs, set aside at least ₹25,000–₹30,000 for loan repayment this season. The rest can cover family expenses and savings. If repayment pressure is high, request your bank for restructuring or partial rollover."},
                
                # Example 2
                {"role": "user", "content": "My KCC loan is overdue. What can I do?"},
                {"role": "assistant", "content": "If your Kisan Credit Card loan is overdue, visit the branch immediately. Explain your crop situation and request rescheduling or one-time settlement. Many banks offer interest waivers or restructuring for genuine cases. Delaying further will increase penalties."},
                
                # Example 3
                {"role": "user", "content": "How can I reduce my debt burden as a small farmer?"},
                {"role": "assistant", "content": "To reduce debt: diversify crops for steady income, use government subsidies for seeds and fertilizers, and apply for crop insurance under PMFBY. Deposit small savings into a recurring deposit. Even ₹500 per month builds a safety net and reduces loan dependence."},

                # 🔑 now insert the farmer's real query
                {"role": "user", "content": query + extra_context},
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

