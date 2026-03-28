import type { AuthSessionResponse, User } from "../lib/types";
import apiClient from "./client";

export async function loginApi(
  email: string,
  password: string
): Promise<AuthSessionResponse> {
  const { data } = await apiClient.post<AuthSessionResponse>("/auth/login", {
    email,
    password,
  });
  return data;
}

export async function registerApi(
  email: string,
  password: string,
  displayName?: string
): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", {
    email,
    password,
    display_name: displayName,
  });
  return data;
}

export async function getMeApi(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}

export async function refreshApi(): Promise<AuthSessionResponse> {
  const { data } = await apiClient.post<AuthSessionResponse>("/auth/refresh");
  return data;
}

export async function logoutApi(): Promise<void> {
  await apiClient.post("/auth/logout", {});
}

export async function changePasswordApi(
  currentPassword: string,
  newPassword: string
): Promise<AuthSessionResponse> {
  const { data } = await apiClient.post<AuthSessionResponse>("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return data;
}

export async function deleteAccountApi(): Promise<void> {
  await apiClient.delete("/auth/account");
}
