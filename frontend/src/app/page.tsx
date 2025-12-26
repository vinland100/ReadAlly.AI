"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import useTheme from '@/lib/useTheme';
import api from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import Logo from '@/components/common/Logo';

export default function LoginScreen() {
    useTheme('light');
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const setToken = useAuthStore(state => state.setToken);

    const handleLogin = async () => {
        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const res = await api.post('/token', formData);
            setToken(res.data.access_token);
            router.push('/dashboard');
        } catch (e) {
            alert("Login failed");
        }
    };

    const handleRegister = async () => {
        try {
            await api.post('/register', { email, password, nickname: 'New User' });
            await handleLogin();
        } catch (e) {
            alert("Register failed");
        }
    }

    const handleSubmit = () => {
        if (isLogin) {
            handleLogin();
        } else {
            handleRegister();
        }
    }

    return (
        <div className="relative min-h-screen flex flex-col items-center justify-center p-4 font-display">
            {/* Header */}
            <header className="absolute top-0 left-0 w-full px-6 py-6 flex justify-between items-center z-10">
                <div className="flex items-center gap-3">
                    <Logo size={28} />
                    <h1 className="text-xl font-bold tracking-tight text-[#0d121b]">ReadAlly.AI</h1>
                </div>
            </header>

            {/* Main Auth Container */}
            <main className="w-full max-w-[480px] bg-white rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#e7ebf3] overflow-hidden mt-16 sm:mt-0">
                <div className="pt-8 pb-2 px-8 text-center">
                    <h2 className="text-[#0d121b] text-[26px] font-bold leading-tight mb-2">Welcome Back</h2>
                    <p className="text-[#4c669a] text-sm">Continue your immersive reading journey</p>
                </div>

                <div className="px-8 mt-6">
                    <div className="flex border-b border-[#cfd7e7]">
                        <button
                            onClick={() => setIsLogin(true)}
                            className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-all ${isLogin ? 'text-[#135bec] border-[#135bec]' : 'text-[#4c669a] border-transparent hover:text-[#0d121b]'}`}
                        >
                            Sign In
                        </button>
                        <button
                            onClick={() => setIsLogin(false)}
                            className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-all ${!isLogin ? 'text-[#135bec] border-[#135bec]' : 'text-[#4c669a] border-transparent hover:text-[#0d121b]'}`}
                        >
                            Sign Up
                        </button>
                    </div>
                </div>

                <div className="p-8 pt-6 flex flex-col gap-5">
                    <div className="flex flex-col gap-2">
                        <label className="text-[#0d121b] text-sm font-medium">Email Address</label>
                        <input
                            value={email} onChange={(e) => setEmail(e.target.value)}
                            className="w-full rounded-lg border border-[#cfd7e7] bg-[#f8f9fc] text-[#0d121b] h-12 px-4 focus:ring-2 focus:ring-[#135bec]/50 focus:border-[#135bec] transition-all outline-none placeholder:text-[#9ca3af]"
                            placeholder="name@example.com" type="email" />
                    </div>
                    <div className="flex flex-col gap-2">
                        <div className="flex justify-between items-center">
                            <label className="text-[#0d121b] text-sm font-medium">Password</label>
                            {isLogin && <a href="#" className="text-[#135bec] text-xs font-semibold hover:underline">Forgot Password?</a>}
                        </div>
                        <div className="relative w-full">
                            <input
                                value={password} onChange={(e) => setPassword(e.target.value)}
                                className="w-full rounded-lg border border-[#cfd7e7] bg-[#f8f9fc] text-[#0d121b] h-12 px-4 pr-12 focus:ring-2 focus:ring-[#135bec]/50 focus:border-[#135bec] transition-all outline-none placeholder:text-[#9ca3af]"
                                placeholder="Enter your password" type={showPassword ? 'text' : 'password'} />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-0 top-0 h-full w-12 flex items-center justify-center text-[#4c669a] hover:text-[#135bec] transition-colors"
                            >
                                <span className="material-symbols-outlined text-[20px]">{showPassword ? 'visibility_off' : 'visibility'}</span>
                            </button>
                        </div>
                    </div>
                    <button onClick={handleSubmit} className="w-full h-12 bg-[#135bec] hover:bg-blue-700 text-white font-bold rounded-lg shadow-md hover:shadow-lg transition-all transform active:scale-[0.99] flex items-center justify-center gap-2 mt-2">
                        <span>{isLogin ? 'Sign In' : 'Sign Up'}</span>
                        <span className="material-symbols-outlined text-[18px]">{isLogin ? 'login' : 'person_add'}</span>
                    </button>

                    <div className="relative flex py-2 items-center">
                        <div className="flex-grow border-t border-[#e7ebf3]"></div>
                        <span className="flex-shrink mx-4 text-xs text-[#4c669a] font-medium uppercase tracking-wider">Or continue with</span>
                        <div className="flex-grow border-t border-[#e7ebf3]"></div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <button className="flex items-center justify-center gap-2 h-10 rounded-lg border border-[#cfd7e7] hover:bg-gray-50 transition-colors bg-white text-[#0d121b] text-sm font-medium">
                            <span className="font-bold text-blue-500">G</span> Google
                        </button>
                        <button className="flex items-center justify-center gap-2 h-10 rounded-lg border border-[#cfd7e7] hover:bg-gray-50 transition-colors bg-white text-[#0d121b] text-sm font-medium">
                            <span className="material-symbols-outlined text-[18px]">laptop_mac</span> Apple
                        </button>
                    </div>
                </div>
                <div className="bg-[#f8f9fc] px-8 py-4 border-t border-[#e7ebf3] text-center">
                    <p className="text-xs text-[#4c669a]">
                        By signing in, you agree to our <a href="#" className="underline hover:text-[#135bec]">Terms</a> and <a href="#" className="underline hover:text-[#135bec]">Privacy Policy</a>.
                    </p>
                </div>
            </main>

            {/* Background Blobs */}
            <div aria-hidden="true" className="fixed top-0 left-0 w-full h-full pointer-events-none -z-10 overflow-hidden">
                <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-[#135bec]/5 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] bg-blue-300/10 rounded-full blur-[120px]"></div>
            </div>
        </div>
    );
};
