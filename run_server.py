"""
Development Server Launcher
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  HSK Practice - Online Testing & Analytics Platform")
    print("  Server launching at: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
