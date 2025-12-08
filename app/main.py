from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.vertex_resp import generate_vertex_response
from app.langchain_resp import generate_langchain_response

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/vertex-text")
async def vertex_text_post(request: QueryRequest):
    """POST endpoint - send query in request body as JSON"""
    try:
        response = generate_vertex_response(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vertex-text-langchain")
async def vertex_text_langchain_post(request: QueryRequest):
    """POST endpoint powered by LangChain and ChatVertexAI."""
    try:
        response = generate_langchain_response(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
