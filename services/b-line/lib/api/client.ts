/**
 * API Client for Cortex-Prime Services
 * Handles communication with manifest ingestion, runtime executor, and deployment services
 */

// Use environment variables or fallback to localhost
const getBaseUrl = (envVar: string, defaultPort: string) => {
  if (typeof window === 'undefined') {
    // Server-side: use service names
    return envVar;
  }
  // Client-side: use localhost
  return `http://localhost:${defaultPort}`;
};

const MANIFEST_SERVICE_URL = getBaseUrl(
  process.env.NEXT_PUBLIC_MANIFEST_URL || 'http://manifest_ingestion:8082',
  '8082'
);
const RUNTIME_SERVICE_URL = getBaseUrl(
  process.env.NEXT_PUBLIC_RUNTIME_URL || 'http://runtime_executor:8083',
  '8083'
);
const DEPLOYMENT_SERVICE_URL = getBaseUrl(
  process.env.NEXT_PUBLIC_DEPLOYMENT_URL || 'http://deployment_controller:8084',
  '8084'
);

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async post<T>(path: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async put<T>(path: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }
}

export const manifestApi = new ApiClient(MANIFEST_SERVICE_URL);
export const runtimeApi = new ApiClient(RUNTIME_SERVICE_URL);
export const deploymentApi = new ApiClient(DEPLOYMENT_SERVICE_URL);

// Specific API functions
export const api = {
  // Manifest operations
  manifests: {
    listAgents: () => manifestApi.get<any[]>('/registry/agents'),
    listTools: () => manifestApi.get<any[]>('/registry/tools'),
    listRelics: () => manifestApi.get<any[]>('/registry/relics'),
    listWorkflows: () => manifestApi.get<any[]>('/registry/workflows'),
    getAgent: (name: string) => manifestApi.get<any>(`/registry/manifest/Agent/${name}`),
    getTool: (name: string) => manifestApi.get<any>(`/registry/manifest/Tool/${name}`),
    getRelic: (name: string) => manifestApi.get<any>(`/registry/manifest/Relic/${name}`),
    getWorkflow: (name: string) => manifestApi.get<any>(`/registry/manifest/Workflow/${name}`),
    getStatus: () => manifestApi.get<any>('/registry/status'),
    sync: () => manifestApi.post<any>('/registry/sync'),
  },

  // Execution operations
  executions: {
    executeAgent: (name: string, input: any) => 
      runtimeApi.post<any>('/execute/agent', { agent_name: name, input_data: input }),
    executeTool: (name: string, parameters: any) =>
      runtimeApi.post<any>('/execute/tool', { tool_name: name, parameters }),
    listExecutions: () => runtimeApi.get<any[]>('/executions'),
    getExecution: (id: string) => runtimeApi.get<any>(`/executions/${id}`),
  },

  // Deployment operations (future)
  deployments: {
    listRelics: () => deploymentApi.get<any[]>('/deployments/relics'),
    deployRelic: (name: string) => deploymentApi.post<any>('/deployments/relics', { relic: name }),
    getRelicStatus: (name: string) => deploymentApi.get<any>(`/deployments/relics/${name}`),
  },

  // System operations
  system: {
    health: () => manifestApi.get<any>('/health'),
  },
};
