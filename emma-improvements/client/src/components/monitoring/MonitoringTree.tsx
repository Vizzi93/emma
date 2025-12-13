import { useEffect, useMemo } from 'react';
import { ChevronRight, ChevronDown, Server, Layers, MapPin } from 'lucide-react';
import { useMonitoringHierarchy } from '@/hooks/useMonitoringHierarchy';
import { useMonitoringStore } from '@/stores/monitoringStore';
import type { TreeSelection, Region, Verfahren, Host } from '@/types/monitoring';

interface MonitoringTreeProps {
  onSelect?: (selection: TreeSelection) => void;
  className?: string;
}

// Status-Dot Komponente
const StatusDot = ({ status }: { status: string }) => {
  const colorClass = {
    healthy: 'bg-green-500',
    online: 'bg-green-500',
    degraded: 'bg-yellow-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500',
    offline: 'bg-red-500',
    unknown: 'bg-gray-500',
  }[status] || 'bg-gray-500';

  return (
    <span className={`w-2 h-2 rounded-full ${colorClass} flex-shrink-0`} />
  );
};

// Skeleton Loading
const TreeSkeleton = () => (
  <div className="space-y-2 p-2">
    {[1, 2, 3].map((i) => (
      <div key={i} className="space-y-2">
        <div className="flex items-center gap-2 p-2">
          <div className="w-4 h-4 bg-gray-700 rounded animate-pulse" />
          <div className="w-2 h-2 bg-gray-700 rounded-full animate-pulse" />
          <div className="h-4 bg-gray-700 rounded animate-pulse w-24" />
        </div>
        <div className="pl-6 space-y-1">
          {[1, 2].map((j) => (
            <div key={j} className="flex items-center gap-2 p-2">
              <div className="w-4 h-4 bg-gray-700/50 rounded animate-pulse" />
              <div className="w-2 h-2 bg-gray-700/50 rounded-full animate-pulse" />
              <div className="h-4 bg-gray-700/50 rounded animate-pulse w-32" />
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

// Host-Item Komponente
const HostItem = ({
  host,
  isSelected,
  onSelect,
}: {
  host: Host;
  isSelected: boolean;
  onSelect: () => void;
}) => {
  const hostStatus = host.status === 'online' ? 'healthy' :
                     host.status === 'warning' ? 'degraded' :
                     host.status === 'offline' ? 'critical' : 'unknown';

  return (
    <button
      onClick={onSelect}
      className={`
        w-full flex items-center gap-2 px-2 py-1.5 pl-12 rounded-md
        transition-colors duration-150 text-left
        ${isSelected
          ? 'bg-blue-900/50 border-l-2 border-blue-500'
          : 'hover:bg-gray-800 border-l-2 border-transparent'
        }
      `}
    >
      <Server size={14} className="text-gray-500 flex-shrink-0" />
      <StatusDot status={hostStatus} />
      <span className={`text-sm truncate ${isSelected ? 'text-white' : 'text-gray-300'}`}>
        {host.name}
      </span>
      <span className="text-xs text-gray-500 ml-auto">{host.ip}</span>
    </button>
  );
};

// Verfahren-Item Komponente
const VerfahrenItem = ({
  verfahren,
  regionId,
  isExpanded,
  isSelected,
  selection,
  onToggle,
  onSelect,
  onHostSelect,
}: {
  verfahren: Verfahren;
  regionId: string;
  isExpanded: boolean;
  isSelected: boolean;
  selection: TreeSelection | null;
  onToggle: () => void;
  onSelect: () => void;
  onHostSelect: (host: Host, path: string[]) => void;
}) => {
  const path = [regionId, verfahren.id];

  return (
    <div>
      <button
        onClick={onSelect}
        className={`
          w-full flex items-center gap-2 px-2 py-1.5 pl-8 rounded-md
          transition-colors duration-150 text-left group
          ${isSelected
            ? 'bg-blue-900/50 border-l-2 border-blue-500'
            : 'hover:bg-gray-800 border-l-2 border-transparent'
          }
        `}
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className="p-0.5 hover:bg-gray-700 rounded transition-colors"
        >
          {isExpanded ? (
            <ChevronDown size={14} className="text-gray-400" />
          ) : (
            <ChevronRight size={14} className="text-gray-400" />
          )}
        </button>
        <Layers size={14} className="text-gray-500 flex-shrink-0" />
        <StatusDot status={verfahren.aggregatedStatus} />
        <span className={`text-sm truncate ${isSelected ? 'text-white' : 'text-gray-300'}`}>
          {verfahren.code}
        </span>
        <span className="text-xs text-gray-500 hidden group-hover:inline truncate">
          {verfahren.name}
        </span>
        <span className="ml-auto px-1.5 py-0.5 text-xs bg-gray-700 text-gray-400 rounded">
          {verfahren.hosts.length}
        </span>
      </button>

      {/* Hosts */}
      <div
        className={`
          overflow-hidden transition-all duration-200 ease-in-out
          ${isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'}
        `}
      >
        {verfahren.hosts.map((host) => (
          <HostItem
            key={host.id}
            host={host}
            isSelected={selection?.type === 'host' && selection.id === host.id}
            onSelect={() => onHostSelect(host, [...path, host.id])}
          />
        ))}
      </div>
    </div>
  );
};

// Region-Item Komponente
const RegionItem = ({
  region,
  isExpanded,
  isSelected,
  expandedNodes,
  selection,
  onToggle,
  onSelect,
  onVerfahrenToggle,
  onVerfahrenSelect,
  onHostSelect,
}: {
  region: Region;
  isExpanded: boolean;
  isSelected: boolean;
  expandedNodes: Set<string>;
  selection: TreeSelection | null;
  onToggle: () => void;
  onSelect: () => void;
  onVerfahrenToggle: (verfahrenId: string) => void;
  onVerfahrenSelect: (verfahren: Verfahren, path: string[]) => void;
  onHostSelect: (host: Host, path: string[]) => void;
}) => {
  return (
    <div>
      <button
        onClick={onSelect}
        className={`
          w-full flex items-center gap-2 px-2 py-2 rounded-md
          transition-colors duration-150 text-left group
          ${isSelected
            ? 'bg-blue-900/50 border-l-2 border-blue-500'
            : 'hover:bg-gray-800 border-l-2 border-transparent'
          }
        `}
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className="p-0.5 hover:bg-gray-700 rounded transition-colors"
        >
          {isExpanded ? (
            <ChevronDown size={16} className="text-gray-400" />
          ) : (
            <ChevronRight size={16} className="text-gray-400" />
          )}
        </button>
        <MapPin size={16} className="text-gray-500 flex-shrink-0" />
        <StatusDot status={region.aggregatedStatus} />
        <span className={`text-sm font-medium ${isSelected ? 'text-white' : 'text-gray-200'}`}>
          {region.name}
        </span>
        <span className="ml-auto px-1.5 py-0.5 text-xs bg-gray-700 text-gray-400 rounded">
          {region.verfahren.length}
        </span>
      </button>

      {/* Verfahren */}
      <div
        className={`
          overflow-hidden transition-all duration-200 ease-in-out
          ${isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}
        `}
      >
        {region.verfahren.map((verfahren) => (
          <VerfahrenItem
            key={verfahren.id}
            verfahren={verfahren}
            regionId={region.id}
            isExpanded={expandedNodes.has(verfahren.id)}
            isSelected={selection?.type === 'verfahren' && selection.id === verfahren.id}
            selection={selection}
            onToggle={() => onVerfahrenToggle(verfahren.id)}
            onSelect={() => onVerfahrenSelect(verfahren, [region.id, verfahren.id])}
            onHostSelect={onHostSelect}
          />
        ))}
      </div>
    </div>
  );
};

export function MonitoringTree({ onSelect, className = '' }: MonitoringTreeProps) {
  const { data, isLoading, error } = useMonitoringHierarchy();
  const { expandedNodes, selection, toggleNode, setSelection } = useMonitoringStore();

  // Handle expand all special case
  const effectiveExpandedNodes = useMemo(() => {
    if (expandedNodes.has('__all__') && data?.regions) {
      const allIds = new Set<string>();
      data.regions.forEach((region) => {
        allIds.add(region.id);
        region.verfahren.forEach((v) => allIds.add(v.id));
      });
      return allIds;
    }
    return expandedNodes;
  }, [expandedNodes, data]);

  // Notify parent on selection change
  useEffect(() => {
    if (selection && onSelect) {
      onSelect(selection);
    }
  }, [selection, onSelect]);

  const handleRegionSelect = (region: Region) => {
    setSelection('region', region.id, [region.id]);
  };

  const handleVerfahrenSelect = (verfahren: Verfahren, path: string[]) => {
    setSelection('verfahren', verfahren.id, path);
  };

  const handleHostSelect = (host: Host, path: string[]) => {
    setSelection('host', host.id, path);
  };

  if (isLoading) {
    return (
      <div className={`bg-gray-900 rounded-lg ${className}`}>
        <TreeSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-gray-900 rounded-lg p-4 ${className}`}>
        <p className="text-red-400 text-sm">Fehler beim Laden der Hierarchie</p>
      </div>
    );
  }

  if (!data?.regions || data.regions.length === 0) {
    return (
      <div className={`bg-gray-900 rounded-lg p-4 ${className}`}>
        <p className="text-gray-500 text-sm">Keine Regionen gefunden</p>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-lg ${className}`}>
      <div className="p-2 space-y-0.5">
        {data.regions.map((region) => (
          <RegionItem
            key={region.id}
            region={region}
            isExpanded={effectiveExpandedNodes.has(region.id)}
            isSelected={selection?.type === 'region' && selection.id === region.id}
            expandedNodes={effectiveExpandedNodes}
            selection={selection}
            onToggle={() => toggleNode(region.id)}
            onSelect={() => handleRegionSelect(region)}
            onVerfahrenToggle={toggleNode}
            onVerfahrenSelect={handleVerfahrenSelect}
            onHostSelect={handleHostSelect}
          />
        ))}
      </div>
    </div>
  );
}
