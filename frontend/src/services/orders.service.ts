import { apiClient } from './api';
import { Order } from '../types';

export interface CreateOrderPayload {
  order_id?: string;
  order_number?: string;
  customer_name: string;
  currency: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  tax: number;
  freight: number;
  grand_total: number;
  destination: string;
  package_count?: number;
  notes?: string;
  is_authoritative?: boolean;
  items: Array<{
    sku: string;
    description: string;
    quantity: number;
    unit: string;
    unit_price: number;
    line_total: number;
  }>;
}

export const ordersService = {
  getOrders: async (): Promise<Order[]> => {
    const res = await apiClient.get<Order[]>('/orders');
    return res.data;
  },

  getOrder: async (orderId: string): Promise<Order> => {
    const res = await apiClient.get<Order>(`/orders/${orderId}`);
    return res.data;
  },

  createOrder: async (payload: CreateOrderPayload): Promise<Order> => {
    const res = await apiClient.post<Order>('/orders', payload);
    return res.data;
  },
};

