from fastapi import FastAPI

from moviely.movies.router import router as movies_router

app = FastAPI(
    title="Moviely",
    description="An open-source Movie REST API",
    version="0.1.0",
)

app.include_router(movies_router)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moviely",
    }
