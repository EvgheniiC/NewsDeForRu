/** Server copy of the listen queue. Field names match the API. */

export interface UserListeningItem {
  news_id: number;
  chunk_index: number;
  char_offset: number;
  finished: boolean;
}

export interface UserListeningState {
  items: UserListeningItem[];
  current_news_id: number | null;
  auto_next: boolean;
  updated_at: number;
}

export interface UserListeningPutResponse {
  state: UserListeningState;
  applied: boolean;
  skipped_news_ids: number[];
}
