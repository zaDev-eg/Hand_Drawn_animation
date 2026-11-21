"""Run the API without PostgreSQL/Redis for a UI-only preview of the login page.

This skips the database startup step so the page, routes and CORS can be tested
in a browser. Real login/registration still requires PostgreSQL and Redis.

    python run_dev.py
"""

import uvicorn

import src.main as main_module


async def skip_db_init():
    pass


main_module.init_db = skip_db_init

if __name__ == "__main__":
    uvicorn.run(
        main_module.app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
