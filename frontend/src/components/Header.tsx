// Header: 56px, logo and case name, tabs, two status chips and the Scenario button (UI_LAYOUT.md section 1)

import React from 'react';
import StatusBadge from './StatusBadge';
import Icon from './Icon';
import { ActiveTab } from '../state/reducer';

const TABS: Array<{ id: ActiveTab; label: string }> = [
  { id: 'investigation', label: 'Investigation' },
  { id: 'origin', label: 'Origin match' },
  { id: 'report', label: 'Report' },
  { id: 'audit', label: 'Audit' },
  { id: 'benchmark', label: 'Benchmark' },
];

interface HeaderProps {
  offlineReplay: boolean;
  simulated?: boolean;
  caseName?: string | null;
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  onOpenScenario: () => void;
  scenarioButtonRef?: React.Ref<HTMLButtonElement>;
}

const PawMark = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true" className="text-accent" fill="currentColor">
    <ellipse cx="12" cy="16" rx="5" ry="4.2" />
    <ellipse cx="5.2" cy="10.2" rx="2" ry="2.5" />
    <ellipse cx="9.4" cy="6.4" rx="2" ry="2.6" />
    <ellipse cx="14.6" cy="6.4" rx="2" ry="2.6" />
    <ellipse cx="18.8" cy="10.2" rx="2" ry="2.5" />
  </svg>
);

export const Header: React.FC<HeaderProps> = ({
  offlineReplay,
  simulated = true,
  caseName,
  activeTab,
  onTabChange,
  onOpenScenario,
  scenarioButtonRef,
}) => {
  // Arrow keys move between tabs (WAI-ARIA tabs pattern)
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const i = TABS.findIndex((t) => t.id === activeTab);
    const next = TABS[(i + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length];
    onTabChange(next.id);
    document.getElementById(`tab-${next.id}`)?.focus();
  };

  return (
    <header className="h-14 shrink-0 border-b border-line bg-surface px-4 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
      <div className="flex items-center gap-2 min-w-0">
        <PawMark />
        <span className="text-[15px] font-semibold text-ink">PRATYAKSH</span>
        {caseName && <span className="text-[13px] text-ink-3 truncate">{caseName}</span>}
      </div>

      <nav role="tablist" aria-label="Views" className="flex h-14 items-stretch" onKeyDown={onKeyDown}>
        {TABS.map((tab) => {
          const selected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              tabIndex={selected ? 0 : -1}
              onClick={() => onTabChange(tab.id)}
              className={`px-3 text-sm border-b-2 transition-colors duration-150 whitespace-nowrap ${
                selected ? 'border-accent text-ink font-semibold' : 'border-transparent text-ink-3 hover:text-ink'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>

      <div className="flex items-center justify-end gap-2">
        {simulated && <StatusBadge label="Simulated data" kind="simulated" />}
        {offlineReplay && <StatusBadge label="Offline replay" kind="offline" />}
        <button
          ref={scenarioButtonRef}
          type="button"
          onClick={onOpenScenario}
          className="ml-1 inline-flex h-9 items-center gap-1.5 rounded-ctl border border-line-strong bg-surface px-3 text-sm font-medium text-ink hover:bg-surface-2"
        >
          <Icon name="sliders" />
          Scenario
        </button>
      </div>
    </header>
  );
};

export default Header;
