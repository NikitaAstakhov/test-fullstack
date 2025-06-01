import {
  FormPayload,
  SubmitSuccessResponse,
  SubmitErrorResponse,
  HistoryRecord,
} from "@services/dataTypes";

const BASE_URL = "http://localhost:8000";

export async function submitForm(
  payload: FormPayload
): Promise<SubmitSuccessResponse> {
  const response = await fetch(`${BASE_URL}/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (response.ok) {
    const data: SubmitSuccessResponse = await response.json();
    return data;
  }

  if (response.status === 400) {
    const errObj: SubmitErrorResponse = await response.json();
    throw errObj;
  }

  if (response.status === 422) {
    const body = await response.json();
    const detailArr: Array<{ loc: string[]; msg: string }> = body.detail;

    const errorMap: Record<string, string[]> = {};
    for (const errItem of detailArr) {
      const loc = errItem.loc;
      const field = loc[loc.length - 1];
      if (!errorMap[field]) {
        errorMap[field] = [];
      }
      errorMap[field].push(errItem.msg);
    }

    const errorResponse: SubmitErrorResponse = {
      success: false,
      error: errorMap,
    };
    throw errorResponse;
  }

  throw new Error(`Unexpected status ${response.status} on submitForm`);
}

export async function fetchHistory(): Promise<HistoryRecord[]> {
  const response = await fetch(`${BASE_URL}/history`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (response.ok) {
    const data: HistoryRecord[] = await response.json();
    return data;
  } else {
    throw new Error("Failed to fetch history");
  }
}
