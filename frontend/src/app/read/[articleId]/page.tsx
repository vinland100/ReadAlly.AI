"use client";
import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import ReadingLayout from '@/components/reading/ReadingLayout';
import ParagraphBlock from '@/components/reading/ParagraphBlock';
import clsx from 'clsx';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import useTheme from '@/lib/useTheme';

export default function ReadingView() {
    useTheme('light');
    const params = useParams();
    const articleId = params.articleId;
    const router = useRouter();

    const [article, setArticle] = useState<any>(null);
    const [paragraphs, setParagraphs] = useState<any[]>([]);
    const [page, setPage] = useState(1);
    const [hasNext, setHasNext] = useState(false);
    const [loading, setLoading] = useState(true);
    const [isRecording, setIsRecording] = useState(false);

    // Full Text TTS State
    const [isGlobalPlaying, setIsGlobalPlaying] = useState(false);
    const [currentTTSParaIndex, setCurrentTTSParaIndex] = useState<number | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    useEffect(() => {
        if (articleId) fetchPage(1);
    }, [articleId]);

    const fetchPage = async (pageNum: number) => {
        setLoading(true);
        try {
            const res = await api.get(`/api/articles/${articleId}/page/${pageNum}`);
            setArticle(res.data.article);

            let paras = res.data.paragraphs;
            // If the first paragraph is an image that matches the cover image, remove it to avoid duplicates
            if (pageNum === 1 && res.data.article.cover_image) {
                if (paras.length > 0 && paras[0].image_url === res.data.article.cover_image) {
                    paras = paras.slice(1);
                }
            }

            setParagraphs(paras);
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
                    <div className="mb-12 border-b border-slate-200 pb-8">
                        <div className="flex justify-between items-start">
                            <h1 className="text-3xl md:text-4xl lg:text-[40px] font-bold text-slate-900 leading-tight mb-4 tracking-tight">{article.title}</h1>
                        </div>

                        {article.cover_image && (
                            <div className="my-8 rounded-2xl overflow-hidden shadow-xl shadow-slate-200/50">
                                <img
                                    src={article.cover_image}
                                    alt={article.title}
                                    className="w-full aspect-[16/9] object-cover"
                                />
                            </div>
                        )}

                        <div className="flex items-center gap-4 text-sm text-slate-500">
                            <span className="bg-slate-100 px-2 py-0.5 rounded text-xs font-medium text-slate-600">{article.difficulty}</span>
                            <span>•</span>
                            <span>{article.word_count !== undefined ? article.word_count : 0} words</span>
                            <button
                                onClick={isGlobalPlaying ? stopGlobalTTS : startGlobalTTS}
                                className={clsx(
                                    "ml-auto p-2 rounded-full transition-all flex items-center justify-center shadow-sm hover:shadow-md",
                                    isGlobalPlaying
                                        ? "bg-black text-white hover:bg-black/80 ring-2 ring-black/20"
                                        : "bg-black text-white hover:bg-black/80 hover:scale-105 active:scale-95"
                                )}
                            >
                                <span className="material-symbols-outlined text-[20px]">{isGlobalPlaying ? "stop" : "headphones"}</span>
                            </button>
                        </div>
                    </div>

                    <div className="space-y-8">
                        {paragraphs.map((para, index) => (
                            <div key={para.id} id={`para-${para.id}`}>
                                <ParagraphBlock
                                    id={para.id}
                                    content={para.content}
                                    image_url={para.image_url}
                                    annotations={para.annotations}
                                    isActiveForTTS={index === currentTTSParaIndex}
                                    onPlayTTS={playParagraphAudio}
                                />
                            </div>
                        ))}
                    </div>

                    <div className="mt-12 flex justify-center border-t border-slate-200 dark:border-slate-800 pt-8">
                        <button
                            disabled={isRecording}
                            onClick={async () => {
                                if (isRecording) return;
                                setIsRecording(true);
                                try {
                                    await api.post('/users/me/record-reading', null, {
                                        params: {
                                            article_id: articleId,
                                            word_count: article.word_count
                                        }
                                    });
                                    router.push('/dashboard');
                                } catch (e: any) {
                                    console.error("Failed to record reading", e);
                                    if (e.response?.status === 401) {
                                        alert("Session expired. Please sign in again.");
                                        router.push('/');
                                    } else {
                                        router.push('/dashboard'); // Still redirect for other errors
                                    }
                                } finally {
                                    setIsRecording(false);
                                }
                            }}
                            className="w-full max-w-md flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-[#135bec] hover:bg-blue-700 text-white font-bold text-lg shadow-lg shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
                        >
                            <span className="material-symbols-outlined">{isRecording ? "sync" : "check_circle"}</span>
                            <span>{isRecording ? "Saving Progress..." : "Finish Reading"}</span>
                        </button>
                    </div>
                </>
            ) : (
                <div className="flex items-center justify-center h-64">
                    <div className="text-slate-500">Loading Article...</div>
                </div>
            )}
        </ReadingLayout>
    );
}
