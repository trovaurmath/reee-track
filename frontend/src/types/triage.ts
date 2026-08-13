export type AnswerType = "BOOLEAN" | "TEXT" | "NUMBER" | "SINGLE_CHOICE" | "MULTIPLE_CHOICE";
export type AnswerValue = boolean | string | number | string[];

export interface TriageClassification {
  id: string;
  code: string;
  name: string;
  description: string | null;
  target_status: string;
  display_order: number;
  is_active: boolean;
}

export interface TriageCriterion {
  id: string;
  code: string;
  question: string;
  help_text: string | null;
  answer_type: AnswerType;
  options: string[];
  is_required: boolean;
  display_order: number;
  is_active: boolean;
}

export interface TriageAnswer {
  id: string;
  criterion_id: string;
  criterion_code: string;
  question: string;
  answer_type: AnswerType;
  value: AnswerValue;
  notes: string | null;
}

export interface Triage {
  id: string;
  equipment_id: string;
  tracking_code: string;
  equipment_description: string;
  evaluator_user_id: string;
  evaluator_name: string;
  status: "IN_PROGRESS" | "COMPLETED" | "CANCELLED";
  classification: TriageClassification | null;
  technical_opinion: string | null;
  observations: string | null;
  defects: string | null;
  reusable_components: string | null;
  started_at: string;
  completed_at: string | null;
  answers: TriageAnswer[];
}

export interface TriageQueueItem {
  equipment_id: string;
  tracking_code: string;
  asset_number: string | null;
  equipment_description: string;
  category_name: string;
  origin_sector_name: string;
  current_status: string;
  collection_date: string;
  active_triage_id: string | null;
  evaluator_name: string | null;
}

export interface TriageQueueResponse {
  items: TriageQueueItem[];
  total: number;
}

export interface TriageCompletePayload {
  classification_id: string;
  technical_opinion: string;
  observations?: string;
  defects?: string;
  reusable_components?: string;
}
