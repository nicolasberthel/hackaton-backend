from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import loadcurve, mix, projects

app = FastAPI()

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


@app.get("/status")
def get_status():
    return "OK"
