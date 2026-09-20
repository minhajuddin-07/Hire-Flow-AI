from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router


def create_app() -> FastAPI:
    """Factory function for the HireFlow AI FastAPI backend application."""
    app = FastAPI(
        title="HireFlow AI Backend API",
        description="Production AI Candidate Screening & Adaptive Interview Intelligence Engine",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    return app


app = create_app()
