import uvicorn

from app.core.logging import uvicorn_log_config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        access_log=False,
        log_config=uvicorn_log_config(),
    )
