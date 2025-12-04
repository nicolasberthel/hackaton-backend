from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import loadcurve, mix, projects, optimization, portfolio

app = FastAPI(
    title="Energy Management API",
    description="API for energy consumption, production, and investment optimization",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(loadcurve.router, tags=["loadcurve"])
app.include_router(mix.router, tags=["mix"])
app.include_router(projects.router, tags=["projects"])
app.include_router(optimization.router, tags=["optimization"])
app.include_router(portfolio.router, tags=["portfolio"])


@app.get("/status")
def get_status():
    return "OK"
