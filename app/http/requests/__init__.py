from app.http.requests.auth_request import LoginRequest, RegisterRequest, ChangePasswordRequest
from app.http.requests.message_request import CreateMessageRequest
from app.http.requests.project_request import CreateProjectRequest, UpdateProjectRequest, RenameProjectRequest
from app.http.requests.task_request import CreateTaskRequest, UpdateTaskRequest, RenameTaskRequest
from app.http.requests.user_request import CreateUserRequest, UpdateUserRequest
from app.http.requests.template_request import CreateTemplateRequest, UpdateTemplateRequest
from app.http.requests.chat_request import ChatRequest

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "ChangePasswordRequest",
    "CreateMessageRequest",
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "RenameProjectRequest",
    "CreateTaskRequest",
    "UpdateTaskRequest",
    "RenameTaskRequest",
    "CreateUserRequest",
    "UpdateUserRequest",
    "CreateTemplateRequest",
    "UpdateTemplateRequest",
    "ChatRequest",
]
