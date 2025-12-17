"use client";
import React, { useEffect } from 'react';

export default function useTheme(theme: 'light' | 'dark') {
    useEffect(() => {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.classList.add('dark');
        } else {
            root.classList.remove('dark');
        }
    }, [theme]);
}
