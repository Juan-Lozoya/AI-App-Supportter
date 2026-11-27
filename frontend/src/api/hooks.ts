import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type { HoldingReviewRequest, ListParams, ReviewRequest } from "./types";

const POLL_MS = 2000;

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboardStats,
    refetchInterval: 15_000,
  });
}

export function useAnalyses(params: ListParams = {}) {
  return useQuery({
    queryKey: ["analyses", params],
    queryFn: () => api.listAnalyses(params),
  });
}

export function useEventTypes() {
  return useQuery({
    queryKey: ["event-types"],
    queryFn: api.eventTypes,
    staleTime: Infinity,
  });
}

// Consulta cada 2 s mientras el análisis está en proceso y se detiene al terminar.
export function useAnalysis(id: string) {
  return useQuery({
    queryKey: ["analysis", id],
    queryFn: () => api.getAnalysis(id),
    refetchInterval: (query) =>
      query.state.data?.status === "processing" ? POLL_MS : false,
  });
}

// Una por sección de la interfaz. `enabled` evita pedirlas antes de que el análisis termine.
export function useOverview(id: string, enabled = true) {
  return useQuery({
    queryKey: ["analysis", id, "overview"],
    queryFn: () => api.overview(id),
    enabled,
  });
}
export function useKeyDates(id: string, enabled = true) {
  return useQuery({
    queryKey: ["analysis", id, "dates"],
    queryFn: () => api.keyDates(id),
    enabled,
  });
}
export function useHoldings(id: string, enabled = true) {
  return useQuery({
    queryKey: ["analysis", id, "holdings"],
    queryFn: () => api.holdings(id),
    enabled,
  });
}
export function useAlerts(id: string, enabled = true) {
  return useQuery({
    queryKey: ["analysis", id, "alerts"],
    queryFn: () => api.alerts(id),
    enabled,
  });
}
export function useProcessing(id: string) {
  return useQuery({
    queryKey: ["analysis", id, "processing"],
    queryFn: () => api.processing(id),
    refetchInterval: (query) =>
      query.state.data?.status === "processing" ? POLL_MS : false,
  });
}

export function useCreateAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createAnalysis,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
  });
}

export function useRetryAnalysis(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.retryAnalysis(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["analysis", id] }),
  });
}

export function useSubmitReview(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ReviewRequest) => api.submitReview(id, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["analysis", id] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["analyses"] });
    },
  });
}

export function useUpdateHolding(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      matchId,
      body,
    }: {
      matchId: string;
      body: HoldingReviewRequest;
    }) => api.updateHolding(id, matchId, body),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["analysis", id] }),
  });
}
