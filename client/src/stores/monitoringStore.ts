import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { TreeSelection, SelectionType } from '@/types/monitoring';

interface MonitoringState {
  // Expanded nodes in tree (Set of node IDs)
  expandedNodes: Set<string>;

  // Currently selected item
  selection: TreeSelection | null;

  // Actions
  toggleNode: (nodeId: string) => void;
  expandNode: (nodeId: string) => void;
  collapseNode: (nodeId: string) => void;
  expandAll: () => void;
  collapseAll: () => void;
  setSelection: (type: SelectionType, id: string, path: string[]) => void;
  clearSelection: () => void;
}

export const useMonitoringStore = create<MonitoringState>()(
  persist(
    (set, get) => ({
      expandedNodes: new Set<string>(),
      selection: null,

      toggleNode: (nodeId: string) => {
        const { expandedNodes } = get();
        const newExpanded = new Set(expandedNodes);

        if (newExpanded.has(nodeId)) {
          newExpanded.delete(nodeId);
        } else {
          newExpanded.add(nodeId);
        }

        set({ expandedNodes: newExpanded });
      },

      expandNode: (nodeId: string) => {
        const { expandedNodes } = get();
        const newExpanded = new Set(expandedNodes);
        newExpanded.add(nodeId);
        set({ expandedNodes: newExpanded });
      },

      collapseNode: (nodeId: string) => {
        const { expandedNodes } = get();
        const newExpanded = new Set(expandedNodes);
        newExpanded.delete(nodeId);
        set({ expandedNodes: newExpanded });
      },

      expandAll: () => {
        // Will be populated by the component with all node IDs
        set({ expandedNodes: new Set(['__all__']) });
      },

      collapseAll: () => {
        set({ expandedNodes: new Set() });
      },

      setSelection: (type: SelectionType, id: string, path: string[]) => {
        set({ selection: { type, id, path } });
      },

      clearSelection: () => {
        set({ selection: null });
      },
    }),
    {
      name: 'emma-monitoring',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Convert Set to Array for JSON serialization
        expandedNodes: Array.from(state.expandedNodes),
        selection: state.selection,
      }),
      merge: (persisted: any, current) => ({
        ...current,
        // Convert Array back to Set when loading
        expandedNodes: new Set(persisted?.expandedNodes || []),
        selection: persisted?.selection || null,
      }),
    }
  )
);
