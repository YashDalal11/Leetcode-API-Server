from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from auth.router import router as auth_router
from leetcode.routers.connect import router as connect_router
from leetcode.routers.profile import router as profile_router
from leetcode.routers.submission import router as submission_router
from leetcode.routers.problem import router as problem_router
from leetcode.routers.contest import router as contest_router

from model import User, LeetcodeAccount, RefreshToken

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://bnlgkjbjnldljadblkfnbohjacnbpnen"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key="vlIeEfOzgV4u88gBRIkOIUi9g5CVno1KVYG7tq-dMaQ=",
)


app.include_router(auth_router)
app.include_router(connect_router)
app.include_router(profile_router)
app.include_router(submission_router)
app.include_router(problem_router)
app.include_router(contest_router)