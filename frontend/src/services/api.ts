import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
  timeout: 15000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("festivapro_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function listResource<T>(endpoint: string): Promise<T[]> {
  const { data } = await api.get<T[]>(endpoint);
  return data;
}

export async function createResource<T>(endpoint: string, payload: Record<string, unknown>): Promise<T> {
  const { data } = await api.post<T>(endpoint, payload);
  return data;
}

export async function updateResource<T>(endpoint: string, id: number, payload: Record<string, unknown>): Promise<T> {
  const { data } = await api.patch<T>(`${endpoint}/${id}`, payload);
  return data;
}

export async function deleteResource(endpoint: string, id: number): Promise<void> {
  await api.delete(`${endpoint}/${id}`);
}
