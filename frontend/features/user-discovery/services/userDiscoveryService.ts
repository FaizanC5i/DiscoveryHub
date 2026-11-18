import { apiRequest } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type { ApprovalResult, UserDiscoveryOverview } from "../types/userDiscovery";

export function getUserDiscovery(projectId: number): Promise<UserDiscoveryOverview> {
  return apiRequest<UserDiscoveryOverview>(API_PATHS.userDiscovery.overview(projectId));
}

export function startUserDiscoveryRun(projectId: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(API_PATHS.userDiscovery.runs(projectId), { method: "POST" });
}

export function regenerateCheckpoint(projectId: number, checkpointId: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(API_PATHS.userDiscovery.regenerate(projectId, checkpointId), {
    method: "POST",
  });
}

export function submitOwnerInput(
  projectId: number,
  checkpointId: number,
  text: string,
): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(API_PATHS.userDiscovery.input(projectId, checkpointId), {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function approveProposal(
  projectId: number,
  proposalId: number,
  overrideText?: string,
): Promise<ApprovalResult> {
  return apiRequest<ApprovalResult>(API_PATHS.userDiscovery.approve(projectId, proposalId), {
    method: "POST",
    ...(overrideText !== undefined ? { body: JSON.stringify({ override_text: overrideText }) } : {}),
  });
}