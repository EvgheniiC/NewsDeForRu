export interface UserLibrarySavedItem {
  news_id: number;
  marked_at: number;
}

export interface UserLibraryReadItem {
  news_id: number;
  read_at: number;
}

export interface UserLibrarySnapshot {
  saved: UserLibrarySavedItem[];
  read: UserLibraryReadItem[];
}

export interface UserLibrarySavedDelta {
  news_id: number;
  marked_at: number;
  removed: boolean;
}

export interface UserLibraryPutRequest {
  saved: UserLibrarySavedDelta[];
  read: UserLibraryReadItem[];
}

export interface UserLibraryPutResponse {
  saved_count: number;
  read_count: number;
  skipped_news_ids: number[];
}
