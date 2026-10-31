import { create } from 'zustand';

interface Reviewer {
  id: string;
  name: string;
  role: string;
  email: string;
}

interface UIState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  
  searchQuery: string;
  setSearchQuery: (query: string) => void;

  currentReviewer: Reviewer;
  setCurrentReviewer: (reviewer: Reviewer) => void;

  notification: { message: string; type: 'success' | 'error' | 'info' | 'warning' } | null;
  showNotification: (message: string, type?: 'success' | 'error' | 'info' | 'warning') => void;
  clearNotification: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),

  currentReviewer: {
    id: 'rev_sarah_chen',
    name: 'Sarah Chen',
    role: 'Lead Verification Specialist',
    email: 'sarah.chen@docuverify.internal',
  },
  setCurrentReviewer: (reviewer) => set({ currentReviewer: reviewer }),

  notification: null,
  showNotification: (message, type = 'info') => {
    set({ notification: { message, type } });
    setTimeout(() => {
      set({ notification: null });
    }, 4500);
  },
  clearNotification: () => set({ notification: null }),
}));

