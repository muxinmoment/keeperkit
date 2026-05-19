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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function askRules(question: string): Promise<RuleAskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/rules/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ question })
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}
