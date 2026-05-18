/** Reader (app user) JWT session — optional; separate from operator/staff auth. */

export interface ReaderTokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ReaderMe {
  id: number;
  email: string;
}

export interface ReaderRegisterCredentials {
  email: string;
  password: string;
}

export interface ReaderLoginCredentials {
  email: string;
  password: string;
}
