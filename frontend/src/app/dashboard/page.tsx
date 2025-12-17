"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import useTheme from '@/lib/useTheme';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function DashboardScreen() {
    useTheme('light');
    const [articles, setArticles] = useState<any[]>([]);
    const [stats, setStats] = useState({ wordsRead: 1250, streak: 12 });
    const router = useRouter();

    useEffect(() => {
        fetchArticles();
    }, []);

    const fetchArticles = async () => {
        try {
            const res = await api.get('/api/articles');
            setArticles(res.data);
        } catch (e) {
            console.error("Failed to fetch articles");
        }
    };

    const handleIngest = async () => {
        const url = prompt("Enter URL to ingest:");
        if(url) {
            try {
                await api.post('/ingest/url', null, { params: { url } });
                fetchArticles();
            } catch(e) {
                alert("Ingestion failed");
            }
        }
    }

    return (
        <div className="font-lexend bg-[#f8f9fc] min-h-screen flex flex-col overflow-x-hidden">
            <header className="sticky top-0 z-50 flex items-center justify-between border-b border-slate-200 bg-[#f8f9fc]/80 backdrop-blur-md px-6 py-3 lg:px-10">
                <div className="flex items-center gap-4">
                    <div className="size-8 text-[#135bec]">
                        <span className="material-symbols-outlined text-3xl">auto_stories</span>
                    </div>
                    <h2 className="text-slate-900 text-xl font-bold leading-tight tracking-[-0.015em]">ReadAlly.AI</h2>
                </div>
                <div className="flex flex-1 justify-end gap-6 items-center">
                    <button onClick={handleIngest} className="text-sm font-bold text-[#135bec] hover:bg-blue-50 px-3 py-1 rounded">
                        + Add Content
                    </button>
                    <Link href="/profile" className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border-2 border-white shadow-sm" style={{backgroundImage: 'url("https://api.dicebear.com/9.x/adventurer/svg?seed=Cookie")'}}></Link>
                </div>
            </header>

            <main className="flex-1 flex justify-center py-8 px-4 md:px-8">
                <div className="flex flex-col max-w-[1200px] w-full gap-8">
                    <div className="flex flex-col lg:flex-row gap-6">
                        {/* Hero */}
                        <div className="flex-[2] rounded-2xl bg-white shadow-sm border border-slate-200 p-2 overflow-hidden">
                            <div className="flex flex-col items-stretch justify-start h-full md:flex-row md:items-center gap-4">
                                <div className="w-full md:w-1/2 h-48 md:h-full min-h-[240px] bg-center bg-no-repeat bg-cover rounded-xl" style={{backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuB1zvUKwe7MB09uWaZdCXRoaBTU1Q0Qo4ys3rsKReewuJP3-DwYtLbusz88GTLjn2aZ1xxffR5kRpLtFsU-g3hOKXWpxvGLkwidp8VVt_iMaFwguTNhEw5MjVKyjeQYhrL3wsf8BJOdBfD6EmbqjicnXGvfewi-jPgibWiTwqiPwehEdjXDwCHbhSFqGs782DQ0YQFEnQNWllR40fA61qQDoauz4n6hqi720T4OXh5oWjVyjKYmwK85elxtfKJeWT_xQ8bjiFU0M9l6")'}}></div>
                                <div className="flex flex-col justify-center gap-3 p-4">
                                    <div className="inline-flex items-center gap-2">
                                        <span className="bg-[#135bec]/10 text-[#135bec] text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">Daily Pick</span>
                                        <span className="text-slate-400 text-xs font-medium">8 min read</span>
                                    </div>
                                    <h1 className="text-slate-900 text-2xl font-bold leading-tight">The Future of Neural Networks</h1>
                                    <p className="text-slate-500 text-base font-normal leading-relaxed line-clamp-3">An immersive deep dive into AI cognition and how language models are reshaping our understanding of intelligence.</p>
                                    <div className="flex items-center justify-between pt-2 mt-auto">
                                        <span className="text-slate-500 text-sm font-medium">Difficulty: <span className="text-slate-900 font-semibold">IELTS</span></span>
                                        <button className="flex cursor-pointer items-center justify-center rounded-lg h-10 px-6 bg-[#135bec] hover:bg-blue-700 transition-colors text-white text-sm font-bold shadow-lg shadow-blue-500/20">Start Reading</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {/* Stats */}
                        <div className="flex-1 flex flex-col sm:flex-row lg:flex-col gap-4">
                            <div className="flex-1 flex flex-col justify-between gap-2 rounded-2xl p-6 bg-white border border-slate-200 shadow-sm">
                                <div className="flex justify-between items-start">
                                    <div className="p-2 bg-green-100 rounded-lg text-green-600"><span className="material-symbols-outlined">menu_book</span></div>
                                    <span className="text-xs font-bold text-green-600 flex items-center gap-1">+12% <span className="material-symbols-outlined text-[14px]">arrow_upward</span></span>
                                </div>
                                <div>
                                    <p className="text-slate-500 text-sm font-medium">Words Read Today</p>
                                    <p className="text-slate-900 text-3xl font-bold mt-1">{stats.wordsRead}</p>
                                </div>
                            </div>
                            <div className="flex-1 flex flex-col justify-between gap-2 rounded-2xl p-6 bg-white border border-slate-200 shadow-sm">
                                <div className="flex justify-between items-start">
                                    <div className="p-2 bg-orange-100 rounded-lg text-orange-600"><span className="material-symbols-outlined">local_fire_department</span></div>
                                </div>
                                <div>
                                    <p className="text-slate-500 text-sm font-medium">Current Streak</p>
                                    <p className="text-slate-900 text-3xl font-bold mt-1">{stats.streak} <span className="text-base font-normal text-slate-400">Days</span></p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Cards */}
                    <div className="flex flex-col gap-6">
                        <div className="border-b border-slate-200">
                            <nav className="flex gap-8 overflow-x-auto pb-px">
                                <button className="border-b-[3px] border-[#135bec] text-slate-900 pb-3 pt-2 px-1 text-sm font-bold whitespace-nowrap">All</button>
                                <button className="border-b-[3px] border-transparent text-slate-500 hover:text-slate-700 pb-3 pt-2 px-1 text-sm font-bold whitespace-nowrap">High School</button>
                                <button className="border-b-[3px] border-transparent text-slate-500 hover:text-slate-700 pb-3 pt-2 px-1 text-sm font-bold whitespace-nowrap">CET-4/6</button>
                            </nav>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {articles.map((article: any) => (
                                <Link key={article.id} href={`/read/${article.id}`} className="group flex flex-col gap-3 pb-3 cursor-pointer">
                                    <div className="overflow-hidden rounded-xl">
                                        <div className="w-full bg-center bg-no-repeat aspect-video bg-cover transform group-hover:scale-105 transition-transform duration-500"
                                             style={{backgroundImage: `url("${article.cover_image || 'https://lh3.googleusercontent.com/aida-public/AB6AXuC6mlqqbMrHd77Fs6j6htrKVncuuohfQ55o9uAsualwxBNs0A6LmTQ8ytSwCHZnKrcLmxhSNaieSgliAdYwtM-SN6gsYz4tAf8SQwVs774oX8jb5tkhrPJ_PToFR3DtvonmL7OP8AvGEyt9O9fz4N7nhgRjILeSyZP7U9OGs3cUEu7NEU9nbLNtwzwYP8vhteoM2hDH1SYcAWLXDERBK7OFdCymFFMftrM7zXMdElxPOpRFdwAFTVKPUDXowe8_aj-IRM-ZNxZwWyHk'}")`}}></div>
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center justify-between">
                                            <p className="text-xs font-bold text-[#135bec] uppercase tracking-wide">Article</p>
                                            <span className="text-[10px] font-semibold bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">{article.difficulty}</span>
                                        </div>
                                        <h3 className="text-slate-900 text-base font-bold leading-tight group-hover:text-[#135bec] transition-colors">{article.title}</h3>
                                        <p className="text-slate-500 text-sm font-normal">{article.word_count} words</p>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};
