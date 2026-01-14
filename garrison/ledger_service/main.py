from fastapi import FastAPI

app = FastAPI(title="IronClaw Ledger Service")

@app.get("/health")
async def health():
    return {"status": "ok"}
