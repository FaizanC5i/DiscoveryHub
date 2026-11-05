from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DiscoveryHub API")

# Allow the Next.js dev server (frontend) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
