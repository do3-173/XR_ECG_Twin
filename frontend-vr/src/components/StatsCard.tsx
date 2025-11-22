import React from 'react';

interface StatsCardProps {
  title: string;
  value: number | string;
  unit: string;
  zone: number;
  isZone?: boolean;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, unit, zone, isZone = false }) => {
  return (
    <div className="stat-card">
      <h3>{title}</h3>
      <div className={`stat-value zone-${zone}`}>
        {value} {unit}
      </div>
    </div>
  );
};

export default StatsCard;
