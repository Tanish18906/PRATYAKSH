// TelegramChat component
// Follows UI_UX_DESIGN.md section 5.2 and FRONTEND.md section 5
// Strictly SIMULATED. No connection to Telegram.

import React from 'react';
import { Discovery } from '../types/contract';
import { formatUtcShort, formatNumber, formatBytes } from '../utils/format';

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

  return (
    <div className="bg-surface-raised rounded-lg border border-border flex flex-col overflow-hidden shadow-lg">
      {/* Header */}
      <div className="bg-surface px-4 py-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-accent-dark border border-accent/40 flex items-center justify-center text-accent font-bold text-sm">
            T
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-semibold text-text-primary">{channel.name}</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-accent-dark text-accent border border-accent/30">
                SIMULATED
              </span>
            </div>
            <div className="text-xs text-text-muted flex items-center space-x-2">
              <span className="font-mono">{channel.handle}</span>
              <span>•</span>
              <span>{formatNumber(channel.members)} subscribers</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Feed */}
      <div className="p-4 space-y-3 max-h-72 overflow-y-auto">
        {messages.map((msg) => {
          const isLeakAttachment = msg.id === leak_message_id;

          return (
            <div
              key={msg.id}
              className={`p-3 rounded-lg border text-xs ${
                isLeakAttachment
                  ? 'bg-surface border-accent/30 shadow-sm'
                  : 'bg-surface/50 border-border'
              }`}
            >
              {/* Message Meta */}
              <div className="flex items-center justify-between text-text-muted mb-1.5">
                <span className="font-semibold text-accent font-mono">{msg.sender}</span>
                <span className="text-[11px] font-mono">{formatUtcShort(msg.ts)}</span>
              </div>

              {/* Message Text */}
              <p className="text-text-primary mb-2 whitespace-pre-wrap">{msg.text}</p>

              {/* Attachment Card */}
              {msg.attachment && (
                <div className="bg-surface-raised p-3 rounded border border-border mt-2 flex flex-col space-y-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-9 h-9 rounded bg-accent-dark/40 border border-accent/30 flex items-center justify-center text-accent text-lg">
                      📄
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-xs font-semibold text-text-primary truncate">
                        {msg.attachment.file_name}
                      </div>
                      <div className="text-[11px] text-text-muted flex items-center space-x-2 font-mono">
                        <span>{formatBytes(msg.attachment.size_bytes)}</span>
                        <span>•</span>
                        <span>~{formatNumber(msg.attachment.rows_hint)} rows</span>
                      </div>
                    </div>
                  </div>

                  {/* Export and trace action */}
                  {isLeakAttachment && (
                    <button
                      type="button"
                      disabled={busy || offlineReplay}
                      onClick={() => onExportAndTrace(msg.id)}
                      className="w-full py-2 px-3 rounded bg-accent hover:bg-accent/90 text-background font-bold text-xs flex items-center justify-center space-x-2 transition-colors disabled:opacity-50 mt-1 shadow-md"
                    >
                      <span>🔍</span>
                      <span>Export and trace</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Disclaimer */}
      <div className="bg-surface/80 px-4 py-2 border-t border-border text-[11px] text-text-muted text-center italic">
        Synthetic scenario. No real Telegram connection.
      </div>
    </div>
  );
};

export default TelegramChat;
