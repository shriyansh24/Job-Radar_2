import type { TokenResponse, User } from "../lib/types";
import apiClient from "./client";

export async function loginApi(
  email: string,
  password: string
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", {
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

export async function refreshApi(
  refreshToken: string
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  return data;
}
