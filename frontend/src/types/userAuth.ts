/** Unified app account — mirrors backend ``/auth/me``. */

export interface UserMe {
  id: number;
  email: string;
  role: string;
  can_moderate: boolean;
  can_run_pipeline: boolean;
}

export interface UserTokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserLoginCredentials {
  email: string;
  password: string;
}

export interface UserRegisterCredentials {
  email: string;
  password: string;
}

export interface RegisterResponse {
  detail: string;
  dev_verification_link?: string | null;
}
