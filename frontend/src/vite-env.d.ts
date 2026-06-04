/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_PUBLIC_APP_BASE_URL?: string;
  readonly VITE_LEGAL_OPERATOR_NAME?: string;
  readonly VITE_LEGAL_OPERATOR_STREET?: string;
  readonly VITE_LEGAL_OPERATOR_POSTAL_CITY?: string;
  readonly VITE_LEGAL_CONTACT_EMAIL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
