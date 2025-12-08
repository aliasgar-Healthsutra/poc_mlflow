import os
import json
import time
from google import genai
from google.genai.types import Part, Content, GenerateContentConfig
import mlflow
from mlflow.genai import load_prompt
from mlflow.exceptions import MlflowException

# Let MLflow use its own configured tracking URI (env / defaults)
def _setup_mlflow_with_retry(max_retries=1, initial_delay=0.5):
    """Probe MLflow quickly; if unavailable, fall back to defaults."""
    for attempt in range(max_retries):
        try:
            mlflow.get_experiment_by_name("GenAI_VertexAI_Integration")
            print("✅ MLflow reachable (using default tracking URI)")
            return True
        except (MlflowException, Exception) as e:
            if attempt < max_retries - 1:
                delay = initial_delay
                print(f"⚠️ MLflow attempt {attempt + 1} failed. Retrying in {delay}s... Error: {str(e)[:100]}")
                time.sleep(delay)
            else:
                raise

def generate_vertex_response(query: str):
    try:
        client = genai.Client(
            vertexai=True,
            project="llm-services-450013",
            location="us-central1",
        )
        try:
            # _setup_mlflow_with_retry()
            user_prompt_obj = load_prompt("prompts:/user_prompt@latest")
            system_prompt_obj = load_prompt("prompts:/system_prompt@latest")
            user_prompt = user_prompt_obj.format(user_query=query) 
            system_prompt = str(system_prompt_obj)
        except Exception as mlflow_error:
            print(f"⚠️ MLflow unavailable, using default prompts: {str(mlflow_error)[:100]}")
            user_prompt = query
            system_prompt = "You are a helpful AI assistant."
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[Content(role="user", parts=[Part(text=str(user_prompt))])],
            config=GenerateContentConfig(
                system_instruction=str(system_prompt),
                max_output_tokens=1024,
                temperature=0.2,
            ),
        )

        return {
            "status_code": 200,
            "status": "success",
            "response": response.text,
            "model": "gemini-2.0-flash",
            "user_prompt": user_prompt,
        }
    except Exception as e:
        return {
            "status_code": 500,
            "status": "failure",
            "error": str(e),
        }