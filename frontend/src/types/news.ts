export type UserRole = "owner" | "tenant" | "buyer";

export interface NewsFeedItem {
  id: number;
  title: string;
  subtitle: string;
  read_time_minutes: number;
  created_at: string;
}

export interface ProcessedNews {
  id: number;
  title: string;
  one_sentence_summary: string;
  plain_language: string;
  impact_owner: string;
  impact_tenant: string;
  impact_buyer: string;
  action_items: string;
  bonus_block: string;
  spoiler: string;
  source_url: string;
  confidence_score: number;
  publication_status: string;
  read_time_minutes: number;
  created_at: string;
}

export interface RoleImpact {
  role: UserRole;
  text: string;
}
