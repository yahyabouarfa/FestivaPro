import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createResource, deleteResource, listResource, updateResource } from "../services/api";
import type { ApiRecord } from "../types/api";

export function useResource(endpoint: string) {
  const queryClient = useQueryClient();
  const key = ["resource", endpoint];
  const query = useQuery({
    queryKey: key,
    queryFn: () => listResource<ApiRecord>(endpoint)
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: key });

  const create = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createResource<ApiRecord>(endpoint, payload),
    onSuccess: invalidate
  });
  const update = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      updateResource<ApiRecord>(endpoint, id, payload),
    onSuccess: invalidate
  });
  const remove = useMutation({
    mutationFn: (id: number) => deleteResource(endpoint, id),
    onSuccess: invalidate
  });

  return { ...query, create, update, remove };
}
