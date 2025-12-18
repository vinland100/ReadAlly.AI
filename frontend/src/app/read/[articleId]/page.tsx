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
    const [isGlobalPlaying, setIsGlobalPlaying] = useState(false);
    const [currentTTSParaIndex, setCurrentTTSParaIndex] = useState<number | null>(null);
    const [isTTSLoading, setIsTTSLoading] = useState(false);
    const [activeParaId, setActiveParaId] = useState<number | null>(null);
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

    const playParagraphAudio = async (text: string, paraId: number, index: number, audioPath?: string | null) => {
        if (isTTSLoading) return;

        // Robust backend root calculation
        let baseUrl = api.defaults.baseURL || "";
        if (!baseUrl.startsWith('http') && typeof window !== 'undefined') {
            baseUrl = window.location.origin + baseUrl;
        }
        // Remove trailing slash and /api
        const backendUrl = baseUrl.replace(/\/api\/?$/, '').replace(/\/+$/, '');

        // Ensure audioPath doesn't result in double slashes if it has leading slash
        // Use the new ID-based endpoint
        const staticUrl = `${backendUrl}/api/tts/${paraId}`;

        // If clicking the same paragraph that is already playing, stop it.
        if (activeParaId === paraId && audioRef.current && !audioRef.current.paused) {
            stopGlobalTTS();
            return;
        }

        // Stop global if playing
        if (isGlobalPlaying) {
            stopGlobalTTS();
        }

        setIsTTSLoading(true);
        setActiveParaId(paraId);
        setCurrentTTSParaIndex(index);

        try {
            if (!paraId) {
                console.warn(`No paraId provided`);
                setIsTTSLoading(false);
                setActiveParaId(null);
                setCurrentTTSParaIndex(null);
                return;
            }

            const audio = new Audio(staticUrl);
            audioRef.current = audio;

            const onAudioReady = () => {
                setIsTTSLoading(false);
                audio.play().catch(e => {
                    console.error("Playback failed", e);
                    setIsTTSLoading(false);
                    setActiveParaId(null);
                    setCurrentTTSParaIndex(null);
                });
            };

            audio.oncanplaythrough = onAudioReady;
            // Fallback for cached audio
            if (audio.readyState >= 4) {
                onAudioReady();
            }

            audio.onended = () => {
                setIsTTSLoading(false);
                if (!isGlobalPlaying) {
                    setActiveParaId(null);
                    setCurrentTTSParaIndex(null);
                }
            };

            audio.onerror = () => {
                console.error("Audio playback error:", staticUrl);
                setIsTTSLoading(false);
                setActiveParaId(null);
                setCurrentTTSParaIndex(null);
            };

            // Safeguard: Reset loading state after 10s if nothing happens
            setTimeout(() => {
                if (isTTSLoading && audioRef.current === audio) {
                    setIsTTSLoading(false);
                }
            }, 10000);

        } catch (e) {
            console.error("TTS failed", e);
            setIsTTSLoading(false);
            setActiveParaId(null);
            setCurrentTTSParaIndex(null);
        }
    };

    // Global TTS Logic
    const startGlobalTTS = () => {
        if (paragraphs.length === 0 || isTTSLoading) return;
        setIsGlobalPlaying(true);
        playSequence(0);
    };

    const stopGlobalTTS = () => {
        setIsGlobalPlaying(false);
        setCurrentTTSParaIndex(null);
        setActiveParaId(null);
        setIsTTSLoading(false);
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.onended = null;
            audioRef.current.oncanplay = null;
            audioRef.current.onerror = null;
            audioRef.current = null;
        }
    };

    const playSequence = async (index: number) => {
        if (index >= paragraphs.length) {
            if (hasNext) {
                stopGlobalTTS();
                alert("End of page. Please click next page to continue.");
            } else {
                stopGlobalTTS();
            }
            return;
        }

        // We don't check !isGlobalPlaying here yet because we need to set state first
        setCurrentTTSParaIndex(index);
        setActiveParaId(paragraphs[index].id);

        // Auto Scroll to center
        const element = document.getElementById(`para-${paragraphs[index].id}`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        setIsTTSLoading(true);
        // Robust backend root calculation
        let baseUrl = api.defaults.baseURL || "";
        if (!baseUrl.startsWith('http') && typeof window !== 'undefined') {
            baseUrl = window.location.origin + baseUrl;
        }
        const backendUrl = baseUrl.replace(/\/api\/?$/, '').replace(/\/+$/, '');

        const para = paragraphs[index];
        const staticUrl = `${backendUrl}/api/tts/${para.id}`;

        try {
            if (!para.id) {
                console.warn(`No paragraph ID at index ${index}, skipping...`);
                // Skip to next instead of stopping
                playSequence(index + 1);
                return;
            }

            const audio = new Audio(staticUrl);
            audioRef.current = audio;

            const onAudioReady = () => {
                setIsTTSLoading(false);
                audio.play().catch(e => {
                    console.error("Sequence Playback failed", e);
                    // Skip if playback fails
                    playSequence(index + 1);
                });
            };

            audio.oncanplaythrough = onAudioReady;
            if (audio.readyState >= 4) {
                onAudioReady();
            }

            audio.onended = () => {
                playSequence(index + 1);
            };

            audio.onerror = () => {
                console.error("Sequence playback error at index", index, staticUrl);
                // Skip on error too
                playSequence(index + 1);
            };

        } catch (e) {
            console.error("TTS Sequence failed", e);
            setIsTTSLoading(false);
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
                                    audio_path={para.audio_path}
                                    annotations={para.annotations}
                                    isActiveForTTS={index === currentTTSParaIndex}
                                    onPlayTTS={(text, audioPath) => playParagraphAudio(text, para.id, index, audioPath)}
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
