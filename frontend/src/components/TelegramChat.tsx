// Telegram card: one surface, channel header, scrolling messages, the file row and the primary action (UI_LAYOUT.md section 2)
// Strictly SIMULATED. No connection to Telegram.

import React, { useEffect, useRef } from 'react';
import { Discovery } from '../types/contract';
import { formatNumber, formatBytes } from '../utils/format';
import { formatDay } from '../utils/names';
import Icon from './Icon';

interface TelegramChatProps {
  discovery: Discovery;
  scenario_id: string;
  busy: boolean;
  offlineReplay: boolean;
  onExportAndTrace: (message_id: number) => void;
}

export const TelegramChat: React.FC<TelegramChatProps> = ({
  discovery,
  scenario_id: _scenario_id,
  busy,
  offlineReplay,
  onExportAndTrace,
}) => {
  const { channel, messages, leak_message_id } = discovery;
  const listRef = useRef<HTMLOListElement | null>(null);
  const leakRef = useRef<HTMLLIElement | null>(null);

  // Start with the post that carries the file in view, so Export and trace is visible without scrolling
  useEffect(() => {
    if (listRef.current && leakRef.current) listRef.current.scrollTop = leakRef.current.offsetTop; // the list is position: relative, so offsetTop is measured from it
  }, [leak_message_id]);

  return (
    <section aria-label="Simulated Telegram channel" className="flex min-h-0 flex-col rounded-card border border-line bg-surface">
      <div className="flex items-center gap-3 border-b border-line px-4 py-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-tint text-accent">
          <Icon name="send" />
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-ink">{channel.name}</div>
          <div className="truncate text-xs text-ink-3">
            {channel.handle} · {formatNumber(channel.members)} subscribers
          </div>
          <div className="text-xs text-inferred-text">Simulated channel, no real Telegram connection</div>
        </div>
      </div>

      <ol ref={listRef} className="relative min-h-0 flex-1 divide-y divide-line overflow-y-auto">
        {messages.map((msg) => {
          const isLeak = msg.id === leak_message_id;
          return (
            <li key={msg.id} ref={isLeak ? leakRef : undefined} className={`px-4 py-3 ${isLeak ? 'bg-surface-2' : ''}`}>
              <div className="flex items-baseline justify-between gap-2 text-xs">
                <span className="font-medium text-ink-2">{msg.sender}</span>
                <span className="text-ink-3 tabular">{formatDay(msg.ts)}</span>
              </div>
              <p className="mt-1 text-sm text-ink whitespace-pre-wrap">{msg.text}</p>

              {msg.attachment && (
                <div className="mt-3 space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-ctl bg-leak-tint text-leak">
                      <Icon name="document" size={20} />
                    </span>
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-ink">{msg.attachment.file_name}</div>
                      <div className="text-xs text-ink-3 tabular">
                        {formatBytes(msg.attachment.size_bytes)} · about {formatNumber(msg.attachment.rows_hint)} rows
                      </div>
                    </div>
                  </div>
                  {isLeak && (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => onExportAndTrace(msg.id)}
                      title={offlineReplay ? 'Offline replay: traces the bundled demo case.' : undefined}
                      className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-ctl bg-accent px-4 text-sm font-semibold text-white transition-colors duration-150 hover:bg-accent-hover disabled:opacity-50"
                    >
                      <Icon name="search" />
                      Export and trace
                    </button>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
};

export default TelegramChat;
