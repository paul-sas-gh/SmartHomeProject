import { ProcessResponse, SparqlResponse, PredefinedQueryResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export const apiService = {
  async processText(text: string, upload: boolean = true): Promise<ProcessResponse> {
    const response = await fetch(`${API_BASE_URL}/process/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, upload }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  },

  async processFile(file: File, upload: boolean = true): Promise<ProcessResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/process?upload=${upload}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  },

  async runSparqlQuery(query: string, repository?: string): Promise<SparqlResponse> {
    const response = await fetch(`${API_BASE_URL}/sparql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, repository }),
    });

    if (!response.ok) {
      throw new Error(`SPARQL Error: ${response.statusText}`);
    }

    return response.json();
  },

  async runPredefinedQuery(queryId: number): Promise<PredefinedQueryResponse> {
    const response = await fetch(`${API_BASE_URL}/sparql/predefined/${queryId}`);

    if (!response.ok) {
      throw new Error(`Query Error: ${response.statusText}`);
    }

    return response.json();
  },

  async getEntities() {
    const response = await fetch(`${API_BASE_URL}/entities`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
  },

  async getRelations() {
    const response = await fetch(`${API_BASE_URL}/relations`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
  },
};
