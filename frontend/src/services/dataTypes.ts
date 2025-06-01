
export interface FormPayload {
  date: string;
  first_name: string;
  last_name: string;
}

export interface SubmitSuccessResponse {
  success: true;
  data: Array<{
    date: string;
    name: string;
  }>;
}

export interface SubmitErrorResponse {
  success: false;
  error: Record<string, string[]>;
}

export interface HistoryRecord {
  date: string;
  first_name: string;
  last_name: string;
  count: number;
}
