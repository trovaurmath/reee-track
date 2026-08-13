import type { TokenResponse } from "../types/auth";
import type {
  CatalogItem,
  Equipment,
  EquipmentCreatePayload,
  EquipmentEvent,
  EquipmentListResponse,
  EquipmentUpdatePayload,
  TraceabilityFeedResponse,
  WorkflowStatus,
} from "../types/equipment";
import type {
  StorageDashboard,
  StorageLocation,
  StorageLocationPayload,
  StorageMovement,
  StorageOccupancy,
} from "../types/storage";
import type {
  AnswerValue,
  Triage,
  TriageClassification,
  TriageCompletePayload,
  TriageCriterion,
  TriageQueueResponse,
} from "../types/triage";

const apiOrigin = import.meta.env.VITE_API_ORIGIN?.replace(/\/$/, "");

export const API_URL = apiOrigin
  ? `${apiOrigin}/api/v1`
  : (import.meta.env.VITE_API_URL ?? "/api/v1");

interface ApiErrorPayload {
  message?: string;
  detail?: string;
}

export async function readError(response: Response): Promise<string> {
  const fallback = `Falha na requisição (${response.status})`;
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.message ?? payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function loginRequest(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({ username, password });
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<TokenResponse>;
}

export async function refreshRequest(): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<TokenResponse>;
}

export async function logoutRequest(): Promise<void> {
  await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function getHealth(): Promise<{ status: string; database: string }> {
  const response = await fetch(`${API_URL}/health/ready`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<{ status: string; database: string }>;
}

async function authorizedRequest<T>(
  path: string,
  accessToken: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getEquipments(
  accessToken: string,
  options: { query?: string; status?: string; limit?: number; offset?: number } = {},
): Promise<EquipmentListResponse> {
  const params = new URLSearchParams();
  if (options.query) params.set("query", options.query);
  if (options.status) params.set("status", options.status);
  params.set("limit", String(options.limit ?? 50));
  params.set("offset", String(options.offset ?? 0));
  return authorizedRequest(`/equipments?${params.toString()}`, accessToken);
}

export function getEquipmentByCode(accessToken: string, trackingCode: string): Promise<Equipment> {
  return authorizedRequest(`/equipments/by-code/${encodeURIComponent(trackingCode)}`, accessToken);
}

export function createEquipment(
  accessToken: string,
  payload: EquipmentCreatePayload,
): Promise<Equipment> {
  return authorizedRequest("/equipments", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateEquipment(
  accessToken: string,
  equipmentId: string,
  payload: EquipmentUpdatePayload,
): Promise<Equipment> {
  return authorizedRequest(`/equipments/${equipmentId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteEquipment(
  accessToken: string,
  equipmentId: string,
  reason: string,
): Promise<Equipment> {
  return authorizedRequest(`/equipments/${equipmentId}`, accessToken, {
    method: "DELETE",
    body: JSON.stringify({ reason }),
  });
}

export function getStorageDashboard(accessToken: string): Promise<StorageDashboard> {
  return authorizedRequest("/storage/dashboard", accessToken);
}

export function getStorageLocations(
  accessToken: string,
  includeInactive = false,
): Promise<StorageLocation[]> {
  return authorizedRequest(
    `/storage/locations?include_inactive=${includeInactive}`,
    accessToken,
  );
}

export function createStorageLocation(
  accessToken: string,
  payload: StorageLocationPayload,
): Promise<StorageLocation> {
  return authorizedRequest("/storage/locations", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateStorageLocation(
  accessToken: string,
  locationId: string,
  payload: Partial<StorageLocationPayload> & { is_active?: boolean },
): Promise<StorageLocation> {
  return authorizedRequest(`/storage/locations/${locationId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteStorageLocation(
  accessToken: string,
  locationId: string,
): Promise<void> {
  return authorizedRequest(`/storage/locations/${locationId}`, accessToken, {
    method: "DELETE",
  });
}

export function getStorageOccupancies(accessToken: string): Promise<StorageOccupancy[]> {
  return authorizedRequest("/storage/occupancies", accessToken);
}

export function getStorageMovements(accessToken: string): Promise<StorageMovement[]> {
  return authorizedRequest("/storage/movements?limit=50", accessToken);
}

export function moveEquipment(
  accessToken: string,
  payload: { equipment_id: string; to_location_id: string | null; notes?: string },
): Promise<StorageMovement> {
  return authorizedRequest("/storage/movements", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getEquipmentTimeline(
  accessToken: string,
  equipmentId: string,
): Promise<EquipmentEvent[]> {
  return authorizedRequest(`/equipments/${equipmentId}/timeline`, accessToken);
}

export function getWorkflowOptions(
  accessToken: string,
  equipmentId: string,
): Promise<WorkflowStatus[]> {
  return authorizedRequest(`/equipments/${equipmentId}/workflow-options`, accessToken);
}

export function transitionEquipment(
  accessToken: string,
  equipmentId: string,
  payload: { new_status: string; description: string; location?: string },
): Promise<Equipment> {
  return authorizedRequest(`/equipments/${equipmentId}/transitions`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addTimelineNote(
  accessToken: string,
  equipmentId: string,
  payload: { description: string; location?: string },
): Promise<EquipmentEvent> {
  return authorizedRequest(`/equipments/${equipmentId}/timeline-notes`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTraceabilityFeed(
  accessToken: string,
  options: {
    query?: string;
    eventType?: string;
    status?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<TraceabilityFeedResponse> {
  const params = new URLSearchParams();
  if (options.query) params.set("query", options.query);
  if (options.eventType) params.set("event_type", options.eventType);
  if (options.status) params.set("status", options.status);
  params.set("limit", String(options.limit ?? 50));
  params.set("offset", String(options.offset ?? 0));
  return authorizedRequest(`/traceability/events?${params.toString()}`, accessToken);
}

export async function getProtectedFile(
  accessToken: string,
  path: string,
): Promise<Blob> {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.blob();
}

export async function getCatalogs(
  accessToken: string,
): Promise<{ categories: CatalogItem[]; equipmentTypes: CatalogItem[]; sectors: CatalogItem[] }> {
  const [categories, equipmentTypes, sectors] = await Promise.all([
    authorizedRequest<CatalogItem[]>("/catalogs/equipment-categories", accessToken),
    authorizedRequest<CatalogItem[]>("/catalogs/equipment-types", accessToken),
    authorizedRequest<CatalogItem[]>("/catalogs/sectors", accessToken),
  ]);
  return { categories, equipmentTypes, sectors };
}

export function getTriageQueue(accessToken: string): Promise<TriageQueueResponse> {
  return authorizedRequest("/triages/queue", accessToken);
}

export function getTriage(accessToken: string, triageId: string): Promise<Triage> {
  return authorizedRequest(`/triages/${triageId}`, accessToken);
}

export function getEquipmentTriages(
  accessToken: string,
  trackingCode: string,
): Promise<Triage[]> {
  return authorizedRequest(
    `/equipments/${encodeURIComponent(trackingCode)}/triages`,
    accessToken,
  );
}

export function startTriage(accessToken: string, trackingCode: string): Promise<Triage> {
  return authorizedRequest(
    `/equipments/${encodeURIComponent(trackingCode)}/triages`,
    accessToken,
    { method: "POST" },
  );
}

export function saveTriageAnswers(
  accessToken: string,
  triageId: string,
  answers: Array<{ criterion_id: string; value: AnswerValue; notes?: string }>,
): Promise<Triage> {
  return authorizedRequest(`/triages/${triageId}/answers`, accessToken, {
    method: "PUT",
    body: JSON.stringify({ answers }),
  });
}

export function completeTriage(
  accessToken: string,
  triageId: string,
  payload: TriageCompletePayload,
): Promise<Triage> {
  return authorizedRequest(`/triages/${triageId}/complete`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function cancelTriage(accessToken: string, triageId: string): Promise<Triage> {
  return authorizedRequest(`/triages/${triageId}/cancel`, accessToken, { method: "POST" });
}

export async function getTriageConfiguration(
  accessToken: string,
  includeInactive = false,
): Promise<{ criteria: TriageCriterion[]; classifications: TriageClassification[] }> {
  const suffix = includeInactive ? "?include_inactive=true" : "";
  const [criteria, classifications] = await Promise.all([
    authorizedRequest<TriageCriterion[]>(`/triage-config/criteria${suffix}`, accessToken),
    authorizedRequest<TriageClassification[]>(
      `/triage-config/classifications${suffix}`,
      accessToken,
    ),
  ]);
  return { criteria, classifications };
}

export function createTriageCriterion(
  accessToken: string,
  payload: {
    code: string;
    question: string;
    help_text?: string;
    answer_type: string;
    options: string[];
    is_required: boolean;
    display_order: number;
  },
): Promise<TriageCriterion> {
  return authorizedRequest("/triage-config/criteria", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createTriageClassification(
  accessToken: string,
  payload: {
    code: string;
    name: string;
    description?: string;
    target_status: string;
    display_order: number;
  },
): Promise<TriageClassification> {
  return authorizedRequest("/triage-config/classifications", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
