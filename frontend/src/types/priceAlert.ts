// Matches the backend price_alerts table and /price-alerts endpoints.

export type AlertType = "flight" | "hotel";

export type NotificationStatus =
  | "pending"
  | "triggered"
  | "notified"
  | "unavailable";

export interface PriceAlert {
  id: number;
  user_id: number;
  alert_type: AlertType;
  target_price: number;
  is_active: boolean;
  saved_flight_id: number | null;
  saved_hotel_id: number | null;
  last_checked_at: string | null;
  last_notified_at: string | null;
  notification_status: NotificationStatus;
  created_at: string;
  updated_at: string;
}

export interface PriceAlertResponse {
  results: PriceAlert[];
}