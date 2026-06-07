import os
from dotenv import load_dotenv
load_dotenv(override=True)

from langfuse import observe
from langfuse import Langfuse

# Verify keys are loaded
if not os.environ.get("LANGFUSE_PUBLIC_KEY"):
    print("❌ LANGFUSE_PUBLIC_KEY not found in environment!")
    exit(1)

print(f"Using LANGFUSE_HOST: {os.environ.get('LANGFUSE_HOST')}")

@observe()
def my_llm_call(prompt: str):
    print(f"Processing prompt: {prompt}")
    # Simulating LLM call
    if "error" in prompt:
        raise ValueError("Simulated LLM error")
    return "This is a mocked response from the LLM."

def main():
    print("Starting Langfuse trace test...")
    try:
        result = my_llm_call("Hello Langfuse, please log this prompt!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Caught error: {e}")
        
    print("Flushing traces to Langfuse Cloud...")
    # Langfuse client flush will ensure the background worker transmits the observation
    lf = Langfuse()
    lf.flush()
    print("Done! Check your Langfuse dashboard.")

if __name__ == "__main__":
    main()
