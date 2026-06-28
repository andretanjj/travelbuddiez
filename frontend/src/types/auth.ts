// Public user data returned by the backend, which matches the backend User model.
export interface AuthUser {
  username: string;
  email: string | null;
  disabled: boolean | null;
}

// Response from POST /auth/token.
// Backend uses snake_case because it follows FastAPI's OAuth2 tutorial.
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Response from failed backend requests.
export interface AuthErrorResponse {
  detail: string;
}