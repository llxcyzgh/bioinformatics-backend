from app.http.requests.auth_request import LoginRequest, RegisterRequest, ChangePasswordRequest
from app.http.requests.message_request import CreateMessageRequest
from app.http.requests.project_request import CreateProjectRequest, UpdateProjectRequest
from app.http.requests.task_request import CreateTaskRequest, UpdateTaskRequest
from app.http.requests.user_request import CreateUserRequest, UpdateUserRequest

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "ChangePasswordRequest",
    "CreateMessageRequest",
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "CreateTaskRequest",
    "UpdateTaskRequest",
    "CreateUserRequest",
    "UpdateUserRequest",
]
