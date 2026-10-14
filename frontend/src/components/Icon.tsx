// Inline SVG icon, 1.5px stroke, currentColor (DESIGN_SYSTEM.md section 7). Offline, no icon library.

import React from 'react';

import { ICON_PATHS, IconName } from '../utils/icons';

interface IconProps {
  name: IconName;
  size?: 16 | 20;
  className?: string;
}

export const Icon: React.FC<IconProps> = ({ name, size = 16, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    focusable="false"
    className={className}
  >
    <path d={ICON_PATHS[name]} />
  </svg>
);

export default Icon;
