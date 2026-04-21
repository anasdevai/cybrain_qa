import React from 'react';
import './StatusBadge.css';

/**
 * StatusBadge Component
 * 
 * A unified badge component for document statuses (SOP, Contract, etc.)
 * 
 * @param {Object} props
 * @param {string} props.status - The status text to display
 * @param {string} props.color - (Optional) Semantic color name: 'error', 'success', 'primary', 'warning', 'muted'
 */
const StatusBadge = ({ status, color }) => {
  // If color is not provided, try to resolve it from the status string (legacy/table compatibility)
  const resolvedColor = color || status.toLowerCase().replace(/\s+/g, '-');
  
  return (
    <span className={`status-badge status-${resolvedColor}`}>
      {status}
    </span>
  );
};

export default StatusBadge;
