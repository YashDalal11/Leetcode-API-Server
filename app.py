from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from leetcode.routers.connect import router as connect_router
from leetcode.routers.profile import router as profile_router
from leetcode.routers.submission import router as submission_router
from leetcode.routers.problem import router as problem_router
from leetcode.routers.contest import router as contest_router

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


app.include_router(connect_router)
app.include_router(profile_router)
app.include_router(submission_router)
app.include_router(problem_router)
app.include_router(contest_router)
