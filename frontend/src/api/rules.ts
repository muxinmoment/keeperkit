export type Source = {
  source: string;
  title_path: string[];
  score?: number;
  content_preview: string;
};

export type RuleAskResponse = {
  answer: string;
  sources: Source[];
};

export type RuleAskRequest = {
  question: string;
  top_k?: number;
  rerank_top_k?: number;
};

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function askRules(request: RuleAskRequest): Promise<RuleAskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/rules/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json();
}

async function getErrorMessage(response: Response): Promise<string> {
  const fallback = `Request failed: ${response.status}`;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return fallback;
  }

  const body: unknown = await response.json();
  if (isErrorBody(body)) {
    if (typeof body.detail === "string") {
      return body.detail;
    }
    return JSON.stringify(body.detail);
  }
  return fallback;
}

function isErrorBody(value: unknown): value is { detail: unknown } {
  return typeof value === "object" && value !== null && "detail" in value;
}
