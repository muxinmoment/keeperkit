import { API_BASE_URL, getErrorMessage } from "./rules";

export type ModuleSummary = {
  id: string;
  title: string;
  system: string;
  language: string;
  keeper_notes?: string | null;
  spoiler_level: string;
  has_documents: boolean;
  document_count: number;
  index_ready: boolean;
};

export type ModuleCreateRequest = {
  id: string;
  title: string;
  system?: string;
  language?: string;
  keeper_notes?: string;
  spoiler_level?: string;
};

export type ModuleSource = {
  knowledge_base: string;
  module_id: string;
  source: string;
  title_path: string[];
  content_type: string;
  spoiler_level: string;
  score?: number;
  content_preview: string;
};

export type ModuleAskRequest = {
  question: string;
  top_k?: number;
  rerank_top_k?: number;
};

export type ModuleAskResponse = {
  answer: string;
  sources: ModuleSource[];
};

export type ModuleIngestResponse = {
  module_id: string;
  document_count: number;
  chunk_count: number;
  index_dir: string;
};

export type ModuleStructureItem = {
  label: string;
  source: string;
  title_path: string[];
  content_type: string;
  preview: string;
};

export type ModuleStructureGroup = {
  content_type: string;
  label: string;
  items: ModuleStructureItem[];
};

export type ModuleStructureResponse = {
  module_id: string;
  groups: ModuleStructureGroup[];
};

export async function listModules(): Promise<ModuleSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/modules`);
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json();
}

export async function createModule(request: ModuleCreateRequest): Promise<ModuleSummary> {
  const response = await fetch(`${API_BASE_URL}/api/v1/modules`, {
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

export async function uploadModuleDocument(moduleId: string, file: File): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/v1/modules/${moduleId}/upload`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
}

export async function ingestModule(moduleId: string): Promise<ModuleIngestResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/modules/${moduleId}/ingest`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json();
}

export async function askModule(moduleId: string, request: ModuleAskRequest): Promise<ModuleAskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/modules/${moduleId}/ask`, {
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

export async function getModuleStructure(moduleId: string): Promise<ModuleStructureResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/modules/${moduleId}/structure`);
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json();
}
