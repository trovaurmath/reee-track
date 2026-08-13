export interface StorageLocation {
  id: string;
  code: string;
  warehouse: string;
  aisle: string | null;
  rack: string | null;
  shelf: string | null;
  position: string | null;
  capacity: number;
  occupied: number;
  available: number;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StorageLocationPayload {
  code: string;
  warehouse: string;
  aisle?: string;
  rack?: string;
  shelf?: string;
  position?: string;
  capacity: number;
  notes?: string;
}

export interface StorageOccupancy {
  assignment_id: string;
  equipment_id: string;
  tracking_code: string;
  equipment_description: string;
  current_status: string;
  location: StorageLocation;
  entered_at: string;
  dwell_days: number;
  alert: boolean;
}

export interface StorageMovement {
  id: string;
  equipment_id: string;
  tracking_code: string;
  movement_type: "ENTRY" | "TRANSFER" | "EXIT";
  from_location_code: string | null;
  to_location_code: string | null;
  occurred_at: string;
  user_id: string | null;
  notes: string | null;
}

export interface StorageDashboard {
  locations_total: number;
  locations_active: number;
  capacity_total: number;
  occupied_total: number;
  available_total: number;
  dwell_alerts: number;
}
