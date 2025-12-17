"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { useEffect } from 'react';

export default function ProfileScreen() {
    const router = useRouter();
    const [user, setUser] = useState<any>(null);
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/users/me')
            .then(res => {
                setUser(res.data);
                setLoading(false);
            })
            .catch((e) => {
                console.error(e);
                router.push('/');
            });
    }, [router]);

    const handleSave = async () => {
        try {
            if (oldPassword && newPassword) {
                await api.post('/users/me/password', {
                    old_password: oldPassword,
                    new_password: newPassword
                });
                alert('Password updated successfully');
                setOldPassword('');
                setNewPassword('');
            }
            // Here you could also update nickname if needed
            alert('Changes saved!');
        } catch (e: any) {
            alert(e.response?.data?.detail || 'Failed to save changes');
        }
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#f8f8f5] dark:bg-[#23220f]">Loading...</div>;

    return (
        <div className="profile-page bg-[#f8f8f5] dark:bg-[#23220f] font-spline antialiased min-h-screen flex flex-col transition-colors duration-300">
            <header className="w-full px-6 py-4 flex items-center justify-center items-center justify-between border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-[#2c2b15]/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="flex items-center gap-3 text-gray-900 dark:text-white">
                    <div className="size-8 text-[#f9f506]">
                        <svg className="w-full h-full" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg"><path d="M24 4L44 24L24 44L4 24L24 4Z" fill="currentColor" stroke="currentColor" strokeLinejoin="round" strokeWidth="4"></path><path d="M24 14V34" stroke="black" strokeLinecap="round" strokeWidth="4"></path><path d="M14 24H34" stroke="black" strokeLinecap="round" strokeWidth="4"></path></svg>
                    </div>
                    <h1 className="text-xl font-bold tracking-tight">ReadAlly.AI</h1>
                </div>
                <div className="flex items-center gap-4">
                    <button onClick={() => router.push('/dashboard')} className="flex items-center justify-center gap-2 rounded-full px-3 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 text-xs font-bold">Back</button>
                    <div className="size-10 rounded-full bg-cover bg-center border-2 border-[#f9f506] cursor-pointer" style={{ backgroundImage: 'url("https://api.dicebear.com/9.x/adventurer/svg?seed=Cookie")' }}></div>
                </div>
            </header>
            <main className="flex-grow flex items-center justify-center p-4 sm:p-6 lg:p-10 relative overflow-hidden">
                <div className="absolute top-20 left-10 size-64 bg-[#f9f506]/5 rounded-full blur-3xl -z-10"></div>
                <div className="absolute bottom-10 right-10 size-96 bg-[#f9f506]/10 rounded-full blur-3xl -z-10"></div>

                <div className="w-full max-w-[540px] bg-white dark:bg-[#2c2b15] rounded-lg shadow-xl border border-gray-100 dark:border-gray-800 flex flex-col overflow-hidden animate-fade-in-up">
                    <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">Profile Settings</h2>
                        <button onClick={() => router.push('/dashboard')} className="flex items-center justify-center size-10 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"><span className="material-symbols-outlined">close</span></button>
                    </div>
                    <div className="p-6 sm:p-8 flex flex-col gap-8 overflow-y-auto max-h-[80vh]">
                        <div className="flex flex-col items-center gap-4">
                            <div className="relative group">
                                <div className="size-32 rounded-full bg-cover bg-center border-4 border-white dark:border-gray-700 shadow-sm" style={{ backgroundImage: 'url("https://api.dicebear.com/9.x/adventurer/svg?seed=Cookie")' }}></div>
                                <button className="absolute bottom-1 right-1 bg-[#f9f506] text-black size-9 rounded-full flex items-center justify-center shadow-md hover:scale-105 transition-transform cursor-pointer border-2 border-white dark:border-[#2c2b15]"><span className="material-symbols-outlined text-[18px]">edit</span></button>
                            </div>
                            <div className="text-center"><p className="text-gray-900 dark:text-white text-lg font-bold">{user?.nickname || 'Reader'}</p><p className="text-gray-500 dark:text-gray-400 text-sm">Member since 2023</p></div>
                        </div>
                        <form className="flex flex-col gap-6" onSubmit={(e) => e.preventDefault()}>
                            <div className="flex flex-col gap-2">
                                <label className="text-gray-700 dark:text-gray-200 text-sm font-semibold ml-1">Nickname</label>
                                <div className="relative">
                                    <input className="w-full bg-[#f8f8f5] dark:bg-[#23220f] border-transparent focus:border-[#f9f506] focus:ring-0 rounded-xl px-5 py-3.5 text-gray-900 dark:text-white placeholder-gray-400 transition-all outline-none font-medium" type="text" defaultValue={user?.nickname || ''} />
                                    <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none text-xl">person</span>
                                </div>
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-gray-700 dark:text-gray-200 text-sm font-semibold ml-1">Email Address</label>
                                <div className="relative opacity-70">
                                    <input className="w-full bg-gray-100 dark:bg-gray-800/50 border-transparent rounded-xl px-5 py-3.5 text-gray-500 dark:text-gray-400 cursor-not-allowed font-medium" disabled readOnly type="email" value={user?.email || ''} />
                                    <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none text-xl">lock</span>
                                </div>
                            </div>
                            <div className="flex flex-col gap-4">
                                <h3 className="text-gray-900 dark:text-white font-bold text-lg">Password</h3>
                                <details className="group bg-[#f8f8f5] dark:bg-[#23220f] rounded-xl overflow-hidden transition-all duration-300" open>
                                    <summary className="flex items-center justify-between p-4 cursor-pointer list-none text-gray-700 dark:text-gray-200 font-medium hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"><span>Change Password</span><span className="material-symbols-outlined transition-transform group-open:rotate-180">expand_more</span></summary>
                                    <div className="p-4 pt-0 flex flex-col gap-4 animate-fade-in">
                                        <div className="mt-2">
                                            <input
                                                value={oldPassword}
                                                onChange={(e) => setOldPassword(e.target.value)}
                                                className="w-full bg-white dark:bg-[#2c2b15] border border-gray-200 dark:border-gray-700 focus:border-[#f9f506] focus:ring-1 focus:ring-[#f9f506] rounded-xl px-4 py-3 text-gray-900 dark:text-white mb-3"
                                                placeholder="Current Password"
                                                type="password"
                                            />
                                            <input
                                                value={newPassword}
                                                onChange={(e) => setNewPassword(e.target.value)}
                                                className="w-full bg-white dark:bg-[#2c2b15] border border-gray-200 dark:border-gray-700 focus:border-[#f9f506] focus:ring-1 focus:ring-[#f9f506] rounded-xl px-4 py-3 text-gray-900 dark:text-white"
                                                placeholder="New Password"
                                                type="password"
                                            />
                                        </div>
                                    </div>
                                </details>
                            </div>
                        </form>
                    </div>
                    <div className="p-6 border-t border-gray-100 dark:border-gray-800 flex flex-col sm:flex-row gap-4 items-center justify-between bg-gray-50/50 dark:bg-gray-900/20">
                        <button onClick={() => {
                            localStorage.removeItem('token');
                            router.push('/');
                        }} className="text-sm font-semibold text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400 transition-colors" type="button">Sign Out</button>
                        <div className="flex gap-3 w-full sm:w-auto">
                            <button onClick={() => router.push('/dashboard')} className="flex-1 sm:flex-none px-6 py-3 rounded-full border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 font-bold text-sm hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors" type="button">Cancel</button>
                            <button onClick={handleSave} className="flex-1 sm:flex-none px-8 py-3 rounded-full bg-[#f9f506] text-black font-bold text-sm shadow-lg shadow-[#f9f506]/20 hover:shadow-[#f9f506]/40 hover:scale-[1.02] active:scale-[0.98] transition-all" type="button">Save Changes</button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
