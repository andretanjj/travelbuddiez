import type { AuthUser, LoginResponse, AuthErrorResponse } from "../types/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Key used to store the JWT token in browser localStorage.
const TOKEN_STORAGE_KEY = "travelbuddiez_token";

export function saveToken(token: string): void {
  // localStorage keeps the token even after page refresh.
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function getToken(): string | null {
  // Returns null if the user has not logged in yet.
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function removeToken(): void {
  // Used when the user logs out.
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function getErrorMessage(response: Response): Promise<string> {
  // Backend errors usually return { detail: "..." }.
  const errorData = (await response.json().catch(() => null)) as AuthErrorResponse | null;
  return errorData?.detail || "Something went wrong";
}

export async function registerUser(username: string, email: string, password: string): Promise<AuthUser> {
  // Registration uses JSON because it's our own custom endpoint.
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      email,
      password,
    }),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}


export async function loginUser(usernameOrEmail: string, password: string): Promise<LoginResponse> {
  // FastAPI OAuth2PasswordRequestForm expects form data.
  // Field must be called "username", but we can put email inside it.
  const formData = new URLSearchParams();

  formData.append("username", usernameOrEmail);
  formData.append("password", password);

  const response = await fetch(`${API_BASE_URL}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}


export async function getCurrentUser(): Promise<AuthUser> {
  const token = getToken();

  if (token === null) {
    throw new Error("No login token found");
  }

  // Protected route needs Authorization: Bearer <token>.
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}