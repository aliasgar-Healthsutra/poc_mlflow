from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import mlflow
from mlflow.genai import load_prompt

def generate_langchain_response(query: str):
	try:
		mlflow.set_experiment("LangChain_VertexAI_Experiment")
		mlflow.langchain.autolog()
		try:
			user_prompt_obj = load_prompt("prompts:/user_prompt@latest")
			system_prompt_obj = load_prompt("prompts:/system_prompt@latest")
			user_prompt = user_prompt_obj.format(user_query=query)
			system_prompt = str(system_prompt_obj)
		except Exception as mlflow_error:
			print(f"⚠️ MLflow unavailable, using default prompts: {str(mlflow_error)[:100]}")
			user_prompt = query
			system_prompt = "You are a helpful AI assistant."

		model = ChatVertexAI(
			model="gemini-2.0-flash",
			location="us-central1",
			project="llm-services-450013",
			temperature=0.2,
			max_output_tokens=1024,
		)

		prompt = ChatPromptTemplate.from_messages(
			[
				("system", str(system_prompt)),
				("human", "{question}"),
			]
		)

		chain = prompt | model | StrOutputParser()
		try:
			with mlflow.start_run():
				answer = chain.invoke({"question": str(user_prompt)})

				return {
					"status_code": 200,
					"status": "success",
					"response": answer,
					"model": "gemini-2.0-flash",
					"user_prompt": user_prompt,
				}
		except Exception as mlflow_run_error:
			print(f"⚠️ MLflow run error, proceeding without logging: {str(mlflow_run_error)[:100]}")
			answer = chain.invoke({"question": str(user_prompt)})

			return {
				"status_code": 200,
				"status": "success",
				"response": answer,
				"model": "gemini-2.0-flash",
				"user_prompt": user_prompt,
			}
	except Exception as e:
		return {
			"status_code": 500,
			"status": "failure",
			"error": str(e),
		}
