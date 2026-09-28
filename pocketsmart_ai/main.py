"""
PocketSmart AI: Main Entry Point
Allows starting the FastAPI application with `python main.py` or `uvicorn main:app`.
"""

from app import app

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  PocketSmart AI: Your Smart Budget & Recommendation Assistant")
    print("  Starting FastAPI server on http://127.0.0.1:8000")
    print("="*60 + "\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
