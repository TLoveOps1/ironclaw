from fastapi import FastAPI, Request
import uvicorn
import time
import json

app = FastAPI()

CALL_COUNT = 0

@app.post("/v1/chat/completions")
async def completions(request: Request):
    global CALL_COUNT
    CALL_COUNT += 1
    data = await request.json()
    print(f"Mock received request: {data}")
    
    return {
        "id": "mock-res",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "ACK from mock model"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }

@app.get("/calls")
async def get_calls():
    return {"count": CALL_COUNT}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8099)
