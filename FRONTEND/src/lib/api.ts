const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
import { supabase } from './supabase';

export type ApiProduct = {
  id: string;
  name: string;
  category: string;
  price: string | number;
  cost: string | number;
  stock: number;
  unit: string;
};

export type ApiTransaction = {
  id: string;
  type: 'sale' | 'purchase' | 'expense';
  item: string;
  quantity: number;
  total: string | number;
  counterparty: string;
  status: 'paid' | 'pending';
  product_id?: string | null;
  created_at: string;
};

export type DashboardStats = {
  revenue: string;
  total_sales: string;
  total_purchases: string;
  expenses: string;
  total_expenses: string;
  profit: string;
  net_cash_flow: string;
  total_transactions: number;
  inventory_value: string;
  low_stock_count: number;
  low_stock_threshold: number;
  low_stock_items: string[];
};
export type Profile = { id: string; name: string; business: string; category: string; description: string };
export type Analytics = { stats: DashboardStats; daily_sales: { date: string; amount: string }[] };
export type Notification = { id: string; kind: string; title: string; body: string; created_at: string; read: boolean };

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    const { data } = supabase ? await supabase.auth.getSession() : { data: { session: null } };
    const token = data.session?.access_token;
    response = await fetch(`${API_URL}/api${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init?.headers },
    });
  } catch {
    throw new ApiError(0, 'MerchantPal could not reach the server. Check your connection.');
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, body?.detail || 'The server could not complete that request.');
  }
  return body as T;
}

export const api = {
  products: {
    list: () => request<ApiProduct[]>('/inventory'),
    create: (product: Omit<ApiProduct, 'id'>) => request<ApiProduct>('/inventory', { method: 'POST', body: JSON.stringify(product) }),
    update: (id: string, product: Partial<Omit<ApiProduct, 'id'>>) => request<ApiProduct>(`/inventory/${id}`, { method: 'PATCH', body: JSON.stringify(product) }),
    remove: (id: string) => request<void>(`/inventory/${id}`, { method: 'DELETE' }),
  },
  transactions: {
    list: () => request<ApiTransaction[]>('/transactions'),
    create: (transaction: Omit<ApiTransaction, 'id' | 'created_at'> & { source_transcript?: string }) => request<ApiTransaction>('/transactions', { method: 'POST', body: JSON.stringify(transaction) }),
    remove: (id: string) => request<void>(`/transactions/${id}`, { method: 'DELETE' }),
  },
  dashboard: () => request<DashboardStats>('/dashboard/stats'),
  analytics: () => request<Analytics>('/dashboard/analytics'),
  profile: {
    get: () => request<Profile>('/profile'),
    update: (profile: Omit<Profile, 'id'>) => request<Profile>('/profile', { method: 'PUT', body: JSON.stringify(profile) }),
  },
  notifications: () => request<Notification[]>('/notifications'),
  assistant: (question: string) => request<{ explanation: string; facts: Record<string, unknown> }>('/assistant/answer', { method: 'POST', body: JSON.stringify({ question }) }),
};

export function money(value: string | number): number {
  return Number(value) || 0;
}

export function createRequestKey(): string {
  return `idempotency:${crypto.randomUUID()}`;
}
