export interface SearchResultItem {
  entity_type: string;
  entity_id: string;
  title: string;
  snippet?: string;
  url: string;
  score: number;
  matched_field: string;
}

// We will map the array back to the old structure for backwards compatibility,
// or we can just update GlobalSearch to use the new array format. Let's update GlobalSearch.
