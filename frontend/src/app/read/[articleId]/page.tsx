"use client";
import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import ReadingLayout from '@/components/reading/ReadingLayout';
import ParagraphBlock from '@/components/reading/ParagraphBlock';
import api from '@/lib/api';
import useTheme from '@/lib/useTheme';

export default function ReadingView() {
    useTheme('dark');
    const params = useParams();
    const articleId = params.articleId;

    const [article, setArticle] = useState<any>(null);
    const [paragraphs, setParagraphs] = useState<any[]>([]);
    const [page, setPage] = useState(1);
    const [hasNext, setHasNext] = useState(false);
    const [loading, setLoading] = useState(true);

    // Full Text TTS State
    const [isGlobalPlaying, setIsGlobalPlaying] = useState(false);
    const [currentTTSParaIndex, setCurrentTTSParaIndex] = useState<number | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    useEffect(() => {
        if(articleId) fetchPage(1);
    }, [articleId]);

    const fetchPage = async (pageNum: number) => {
        setLoading(true);
        try {
            const res = await api.get(`/api/articles/${articleId}/page/${pageNum}`);
            setArticle(res.data.article);

            // If page 1, replace. If next page, append?
            // The requirement says "Pagination". Usually replace.
            // But for continuous reading (TTS), appending might be better or handling page transitions.
            // Let's implement traditional pagination (replace) for visual simplicity,
            // but the TTS logic will need to handle fetching next page.

            setParagraphs(res.data.paragraphs);
            setHasNext(res.data.has_next);
            setPage(pageNum);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const playParagraphAudio = async (text: string) => {
        // Stop global if playing
        if (isGlobalPlaying) {
             stopGlobalTTS();
        }

        try {
            const res = await api.get('/api/tts/paragraph', {
                params: { text },
                responseType: 'blob'
            });
            const url = URL.createObjectURL(res.data);
            const audio = new Audio(url);
            audio.play();
        } catch (e) {
            console.error("TTS failed", e);
        }
    };

    // Global TTS Logic
    const startGlobalTTS = () => {
        if (paragraphs.length === 0) return;
        setIsGlobalPlaying(true);
        playSequence(0);
    };

    const stopGlobalTTS = () => {
        setIsGlobalPlaying(false);
        setCurrentTTSParaIndex(null);
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
        }
    };

    const playSequence = async (index: number) => {
        if (index >= paragraphs.length) {
            if (hasNext) {
                // Auto load next page
                // This is complex because we need to wait for state update.
                // Simplified: Stop at end of page.
                stopGlobalTTS();
                alert("End of page. Please click next page to continue.");
            } else {
                stopGlobalTTS();
            }
            return;
        }

        setCurrentTTSParaIndex(index);

        // Auto Scroll
        const element = document.getElementById(`para-${paragraphs[index].id}`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        try {
            const text = paragraphs[index].content;
            const res = await api.get('/api/tts/paragraph', {
                params: { text },
                responseType: 'blob'
            });
            const url = URL.createObjectURL(res.data);
            const audio = new Audio(url);
            audioRef.current = audio;

            audio.onended = () => {
                playSequence(index + 1);
            };

            audio.play();
        } catch (e) {
            console.error("TTS Sequence failed", e);
            stopGlobalTTS();
        }
    };

    return (
        <ReadingLayout>
            {!loading && article ? (
                <>
                    <div className="mb-12 border-b border-slate-200 dark:border-slate-800 pb-8">
                        <div className="flex justify-between items-start">
                             <h1 className="text-3xl md:text-4xl lg:text-[40px] font-bold text-slate-900 dark:text-white leading-tight mb-4 tracking-tight">{article.title}</h1>
                             <button
                                onClick={isGlobalPlaying ? stopGlobalTTS : startGlobalTTS}
                                className={isGlobalPlaying ? "bg-red-500 text-white p-3 rounded-full shadow-lg hover:bg-red-600 transition-colors" : "bg-[#137fec] text-white p-3 rounded-full shadow-lg hover:bg-blue-600 transition-colors"}
                             >
                                <span className="material-symbols-outlined text-[24px]">{isGlobalPlaying ? "stop" : "play_arrow"}</span>
                             </button>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-[#94a3b8]">
                            <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-xs font-medium text-slate-600 dark:text-slate-300">{article.difficulty}</span>
                            <span>•</span>
                            <span>{article.word_count} words</span>
                        </div>
                    </div>

                    <div className="space-y-8">
                        {paragraphs.map((para, index) => (
                            <div key={para.id} id={`para-${para.id}`}>
                                <ParagraphBlock
                                    id={para.id}
                                    content={para.content}
                                    annotations={para.annotations}
                                    isActiveForTTS={index === currentTTSParaIndex}
                                    onPlayTTS={playParagraphAudio}
                                />
                            </div>
                        ))}
                    </div>

                    <div className="mt-12 flex justify-between">
                         <button
                            disabled={page === 1}
                            onClick={() => fetchPage(page - 1)}
                            className="px-6 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <button
                            disabled={!hasNext}
                            onClick={() => fetchPage(page + 1)}
                            className="px-6 py-2 rounded-lg bg-[#137fec] text-white disabled:opacity-50 hover:bg-blue-600"
                        >
                            Next Page
                        </button>
                    </div>
                </>
            ) : (
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-500 dark:text-slate-400">Loading Article...</div>
                </div>
            )}
        </ReadingLayout>
    );
}
