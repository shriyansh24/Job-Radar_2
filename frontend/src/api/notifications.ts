import apiClient from "./client";

export interface Notification {
  id: string;
  title: string;
  body: string | null;
  read: boolean;
  notification_type: string | null;
  link: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  unread_count: number;
  total: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export const notificationsApi = {
  list: (unreadOnly = false, limit = 50) =>
    apiClient
      .get<NotificationListResponse>("/notifications", {
        params: { unread_only: unreadOnly, limit },
      })
      .then((r) => r.data),

  unreadCount: () =>
    apiClient
      .get<UnreadCountResponse>("/notifications/unread-count")
      .then((r) => r.data),

  markRead: (id: string) =>
    apiClient.patch(`/notifications/${id}/read`),

  markAllRead: () =>
    apiClient.patch("/notifications/read-all"),

  delete: (id: string) =>
    apiClient.delete(`/notifications/${id}`),
};
