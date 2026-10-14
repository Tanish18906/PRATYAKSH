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
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  onOpenScenario: () => void;
  scenarioButtonRef?: React.Ref<HTMLButtonElement>;
}

// Logo: an eye on an indigo tile. Pratyaksh means "directly evident", seen with one's own eyes.
// Same drawing as public/logo.svg (the favicon).
const LogoMark = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true" className="shrink-0">
    <rect width="32" height="32" rx="8" fill="var(--accent)" />
    <path d="M5 16C9 9.5 23 9.5 27 16C23 22.5 9 22.5 5 16Z" fill="none" stroke="#fff" strokeWidth="2" strokeLinejoin="round" />
    <circle cx="16" cy="16" r="4.5" fill="#fff" />
    <circle cx="16" cy="16" r="2" fill="var(--accent)" />
  </svg>
);

export const Header: React.FC<HeaderProps> = ({
  offlineReplay,
  simulated = true,
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
      <div className="flex min-w-0 items-center gap-2.5">
        <LogoMark />
        <span className="text-xl font-bold leading-none tracking-[0.06em] text-ink">PRATYAKSH</span>
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
