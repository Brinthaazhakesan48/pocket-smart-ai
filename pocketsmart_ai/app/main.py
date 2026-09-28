from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .db import init_db
from .routers import auth,recommendations,pages

@asynccontextmanager
async def lifespan(app:FastAPI):
    init_db(); yield

settings=get_settings()
app=FastAPI(title=settings.app_name,version="1.0.0",description="Budget-aware AI recommendation assistant",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.mount("/static",StaticFiles(directory="app/static"),name="static")
app.include_router(pages.router); app.include_router(auth.router); app.include_router(recommendations.router)

@app.get("/health")
def health(): return {"status":"ok","ai_enabled":bool(settings.ai_enabled and settings.gemini_api_key),"model":settings.gemini_model}

@app.get("/startup")
def startup(): return {"status":"initialized"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run("app.main:app",host="127.0.0.1",port=8000,reload=True)
