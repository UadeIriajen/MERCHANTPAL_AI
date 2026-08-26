export type MockProduct = {
  id: string;
  name: string;
  category: string;
  price: number;
  cost: number;
  stock: number;
  unit: string;
};

export type MockTransaction = {
  id: string;
  item: string;
  quantity: number;
  total: number;
  customer: string;
  date: string;
  status: 'paid' | 'pending';
};

export type MockUser = {
  name: string;
  business: string;
  identifier: string;
  category?: string;
  description?: string;
  isNew?: boolean;
};

export const defaultProducts: MockProduct[] = [
  { id: 'p1', name: 'Jollof Rice', category: 'Prepared food', price: 2500, cost: 1400, stock: 18, unit: 'plate' },
  { id: 'p2', name: 'Grilled Chicken', category: 'Prepared food', price: 3500, cost: 1900, stock: 7, unit: 'piece' },
  { id: 'p3', name: 'Bottled Water', category: 'Drinks', price: 500, cost: 250, stock: 36, unit: 'bottle' },
  { id: 'p4', name: 'Chapman', category: 'Drinks', price: 1800, cost: 850, stock: 12, unit: 'glass' },
];

export const defaultTransactions: MockTransaction[] = [
  { id: 't1', item: 'Jollof Rice + Chicken', quantity: 2, total: 12000, customer: 'Walk-in customer', date: 'Today, 2:42 PM', status: 'paid' },
  { id: 't2', item: 'Chapman', quantity: 3, total: 5400, customer: 'Walk-in customer', date: 'Today, 1:18 PM', status: 'paid' },
  { id: 't3', item: 'Jollof Rice', quantity: 4, total: 10000, customer: 'Adaeze N.', date: 'Yesterday, 6:05 PM', status: 'paid' },
];

/** Replace this module with an API client when MerchantPal gets a backend. */
export function readLocal<T>(key: string, fallback: T): T {
  try {
    const value = localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function writeLocal(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // The app remains usable if browser storage is unavailable.
  }
}