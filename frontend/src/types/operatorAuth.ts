/** Mirrors backend `/auth/me` (`StaffMeResponse`). */
export interface OperatorMe {
  id: number;
  email: string;
  can_moderate: boolean;
  can_run_pipeline: boolean;
}

export interface OperatorTokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface OperatorLoginCredentials {
  email: string;
  password: string;
}
