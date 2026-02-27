"use client";

import React, { useEffect, useState } from 'react';
import api from '@/lib/api';

interface ReadingRecord {
    id: number;
    user_id: number;
    date: string; // YYYY-MM-DD
    words_read: number;
}

export default function StreakCalendar() {
    // Current date for default state
    const today = new Date();
    // We want to force it to use Beijing time conceptually, but for pure UI date math we can use local JS Date
    // assuming the user's browser is either in Beijing time or we just use their local time for the grid.
    const [currentYear, setCurrentYear] = useState(today.getFullYear());
    const [currentMonth, setCurrentMonth] = useState(today.getMonth() + 1); // 1-12
    const [records, setRecords] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchRecords(currentYear, currentMonth);
    }, [currentYear, currentMonth]);

    const fetchRecords = async (year: number, month: number) => {
        setLoading(true);
        try {
            const res = await api.get(`/users/me/reading-records`, {
                params: { year, month }
            });
            const fetchedRecords = res.data.map((r: ReadingRecord) => r.date);
            setRecords(fetchedRecords);
        } catch (e) {
            console.error("Failed to fetch reading records", e);
        } finally {
            setLoading(false);
        }
    };

    const handlePrevMonth = () => {
        if (currentMonth === 1) {
            setCurrentMonth(12);
            setCurrentYear(prev => prev - 1);
        } else {
            setCurrentMonth(prev => prev - 1);
        }
    };

    const handleNextMonth = () => {
        const now = new Date();
        // Prevent going into the future if desired, but we can allow it or just show blank months
        if (currentYear === now.getFullYear() && currentMonth === now.getMonth() + 1) {
            return; // don't go past current month
        }

        if (currentMonth === 12) {
            setCurrentMonth(1);
            setCurrentYear(prev => prev + 1);
        } else {
            setCurrentMonth(prev => prev + 1);
        }
    };

    // Calendar Math
    // 0 = Sunday, 1 = Monday ... 6 = Saturday
    const getDaysInMonth = (year: number, month: number) => new Date(year, month, 0).getDate();
    const getFirstDayOfMonth = (year: number, month: number) => new Date(year, month - 1, 1).getDay();

    const daysInMonth = getDaysInMonth(currentYear, currentMonth);
    const firstDay = getFirstDayOfMonth(currentYear, currentMonth);

    const isCurrentMonth = currentYear === today.getFullYear() && currentMonth === today.getMonth() + 1;

    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    return (
        <div className="flex-1 flex flex-col gap-4 rounded-2xl p-6 bg-white border border-slate-200 shadow-sm transition-all duration-300">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-orange-100 rounded-lg text-orange-600">
                        <span className="material-symbols-outlined text-sm">calendar_month</span>
                    </div>
                    <p className="text-slate-900 text-base font-bold">Activity</p>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={handlePrevMonth}
                        className="p-1 rounded hover:bg-slate-100 text-slate-500 transition-colors flex items-center justify-center"
                    >
                        <span className="material-symbols-outlined text-sm">chevron_left</span>
                    </button>
                    <span className="text-slate-700 text-sm font-medium w-[100px] text-center">
                        {monthNames[currentMonth - 1]} {currentYear}
                    </span>
                    <button
                        onClick={handleNextMonth}
                        disabled={isCurrentMonth}
                        className="p-1 rounded hover:bg-slate-100 text-slate-500 transition-colors disabled:opacity-30 disabled:hover:bg-transparent flex items-center justify-center"
                    >
                        <span className="material-symbols-outlined text-sm">chevron_right</span>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-7 gap-1 mt-2">
                {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                    <div key={day} className="text-center text-[10px] font-semibold text-slate-400 mb-1">
                        {day}
                    </div>
                ))}

                {/* Empty slots for days before the 1st */}
                {Array.from({ length: firstDay }).map((_, i) => (
                    <div key={`empty-${i}`} className="aspect-square w-full" />
                ))}

                {/* Actual days */}
                {Array.from({ length: daysInMonth }).map((_, i) => {
                    const dayNum = i + 1;
                    const dateStr = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
                    const isCheckedIn = records.includes(dateStr);
                    const isToday = isCurrentMonth && dayNum === today.getDate();

                    return (
                        <div key={dayNum} className="relative aspect-square w-full flex items-center justify-center p-0.5">
                            <div
                                className={`
                                    w-full h-full rounded-md flex items-center justify-center text-xs font-medium transition-all duration-300
                                    ${isCheckedIn
                                        ? 'bg-[#135bec] text-white shadow-sm shadow-blue-500/20'
                                        : isToday
                                            ? 'bg-slate-100 text-[#135bec] font-bold border border-[#135bec]/20'
                                            : 'bg-white text-slate-500 hover:bg-slate-50 border border-slate-100'
                                    }
                                `}
                            >
                                {dayNum}
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="mt-auto pt-4 border-t border-slate-100 flex items-center justify-between">
                <p className="text-xs text-slate-500">
                    <strong className="text-slate-700">{records.length}</strong> days this month
                </p>
                {loading && (
                    <div className="w-3 h-3 border-2 border-[#135bec] border-t-transparent rounded-full animate-spin"></div>
                )}
            </div>
        </div>
    );
}
