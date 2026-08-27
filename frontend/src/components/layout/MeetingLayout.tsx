import React from 'react';
import { Outlet } from 'react-router-dom';

export const MeetingLayout: React.FC = () => {
  return (
    <div className="h-screen w-screen bg-[#080911] text-gray-100 flex flex-col overflow-hidden select-none">
      <main className="flex-1 relative overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
};

export default MeetingLayout;
