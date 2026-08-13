export interface CatalogItem {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface Equipment {
  id: string;
  tracking_code: string;
  asset_number: string | null;
  serial_number: string | null;
  equipment_type: CatalogItem;
  category: CatalogItem;
  origin_sector: CatalogItem;
  brand: string;
  model: string;
  description: string | null;
  initial_condition: string;
  current_status: string;
  collection_date: string;
  collection_notes: string | null;
  is_archived: boolean;
  archived_at: string | null;
  archive_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface EquipmentListResponse {
  items: Equipment[];
  total: number;
  limit: number;
  offset: number;
}

export interface EquipmentEvent {
  id: string;
  equipment_id: string;
  event_type: string;
  previous_status: string | null;
  new_status: string | null;
  timestamp: string;
  user_id: string | null;
  location: string | null;
  description: string;
  metadata: Record<string, unknown>;
}

export interface WorkflowStatus {
  code: string;
  label: string;
  stage: string;
  terminal: boolean;
}

export interface TraceabilityEvent extends EquipmentEvent {
  tracking_code: string;
  equipment_description: string;
  status_label: string | null;
}

export interface TraceabilityFeedResponse {
  items: TraceabilityEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface EquipmentCreatePayload {
  asset_number: string | null;
  serial_number: string | null;
  equipment_type_id: string;
  category_id: string;
  origin_sector_id: string;
  brand: string;
  model: string;
  description: string | null;
  initial_condition: string;
  collection_date: string;
  collection_notes: string | null;
}

export type EquipmentUpdatePayload = Partial<
  Omit<EquipmentCreatePayload, "collection_date">
>;
