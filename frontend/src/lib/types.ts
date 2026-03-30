export interface User {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthSessionResponse {
  authenticated: boolean;
  token_type: string;
}
