import React from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';

export default function ReadingLayout({ children }: { children: React.ReactNode }) {
    const user = useAuthStore(state => state.user);

    return (
        <div className={`font-lexend min-h-screen flex flex-col overflow-x-hidden text-slate-900 selection:bg-[#137fec] selection:text-white bg-[#f8f9fc]`}>
            <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-[#f8f9fc]/80 backdrop-blur-md px-6 py-3">
                <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/dashboard" className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity">
                        <div className="size-8 text-[#137fec]">
                            <span className="material-symbols-outlined text-3xl">auto_stories</span>
                        </div>
                        <h2 className="text-slate-900 text-xl font-bold tracking-tight">ReadAlly.AI</h2>
                    </Link>
                    {/* Progress Bar (Removed) */}
                    <div className="hidden md:flex items-center gap-4 flex-1 justify-center max-w-md">
                    </div>
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard" className="flex items-center justify-center gap-2 rounded-lg h-9 px-4 bg-[#137fec] hover:bg-blue-600 text-white text-sm font-semibold transition-colors shadow-sm shadow-blue-500/20">
                            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                            <span>Library</span>
                        </Link>
                        <Link href="/profile" className="bg-center bg-no-repeat bg-cover rounded-full size-9 ring-2 ring-white shadow-sm hover:scale-105 transition-transform" style={{ backgroundImage: `url("https://api.dicebear.com/9.x/adventurer/svg?seed=${user?.avatar_seed || 'Cookie'}")` }}></Link>
                    </div>
                </div>
            </header>
            <main className="flex-1 w-full max-w-[800px] mx-auto px-6 py-10 lg:py-14 relative z-10">
                {children}
            </main>
            {/* Help Button (Global) */}
            <div className="fixed bottom-8 right-8 z-50">
                <button className="size-12 rounded-full bg-slate-800 text-white shadow-lg hover:bg-[#137fec] transition-colors flex items-center justify-center">
                    <span className="material-symbols-outlined text-[24px]">question_mark</span>
                </button>
            </div>
        </div>
    )
}
