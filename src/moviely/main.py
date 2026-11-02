from fastapi import FastAPI

app = FastAPI(
    title="Moviely",
    description="An open-source Movie REST API",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moviely",
    }
