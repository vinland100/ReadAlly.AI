import React from 'react';
import Link from 'next/link';

export default function ReadingLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className={`font-display min-h-screen flex flex-col overflow-x-hidden text-slate-900 dark:text-[#e2e8f0] selection:bg-[#137fec] selection:text-white dark bg-white dark:bg-[#111a22]`}>
            <header className="sticky top-0 z-50 w-full border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-[#111a22]/90 backdrop-blur-md transition-colors duration-300">
                <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3 cursor-pointer">
                        <div className="size-8 text-[#137fec]">
                            <span className="material-symbols-outlined text-3xl">auto_stories</span>
                        </div>
                        <h2 className="text-slate-900 dark:text-white text-lg font-bold tracking-tight">ReadAlly.AI</h2>
                    </div>
                    {/* Progress Bar (Mock) */}
                    <div className="hidden md:flex items-center gap-4 flex-1 justify-center max-w-md">
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 whitespace-nowrap">Chapter 3: The Digital Age</span>
                        <div className="h-1.5 w-32 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div className="h-full bg-[#137fec] w-[45%] rounded-full"></div>
                        </div>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">45%</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard" className="flex items-center justify-center gap-2 rounded-lg h-9 px-4 bg-[#137fec] hover:bg-blue-600 text-white text-sm font-semibold transition-colors shadow-sm shadow-blue-500/20">
                            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                            <span>Library</span>
                        </Link>
                        <div className="bg-center bg-no-repeat bg-cover rounded-full size-9 ring-2 ring-slate-100 dark:ring-slate-800" style={{backgroundImage: 'url("https://api.dicebear.com/9.x/adventurer/svg?seed=Cookie")'}}></div>
                    </div>
                </div>
            </header>
            <main className="flex-1 w-full max-w-[800px] mx-auto px-6 py-10 lg:py-14 relative z-10">
                {children}
            </main>
            {/* Full Text TTS Toggle Button (Global) */}
            <div className="fixed bottom-8 right-8 z-50">
                <button className="size-12 rounded-full bg-slate-800 dark:bg-slate-700 text-white shadow-lg hover:bg-[#137fec] transition-colors flex items-center justify-center">
                    <span className="material-symbols-outlined text-[24px]">question_mark</span>
                </button>
            </div>
        </div>
    )
}
