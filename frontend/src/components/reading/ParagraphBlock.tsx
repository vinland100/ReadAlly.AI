import React, { Fragment, useRef, useState, useEffect } from 'react';
import { Popover, Transition, Dialog } from '@headlessui/react';
import api from '@/lib/api';
import clsx from 'clsx';
import { useAuthStore } from '@/lib/store';

interface Annotation {
    word: string;
    type: string;
    definition: string;
    context_example: string;
}

interface ParagraphProps {
    id: number;
    content: string;
    image_url?: string | null;
    audio_path?: string | null;
    annotations: Annotation[];
    isActiveForTTS: boolean;
    onPlayTTS: (text: string, audioPath?: string | null) => void;
}

interface TranslationResult {
    translation: string;
    style: string;
    key_phrases: { en: string; cn: string; }[];
}

interface SyntaxResult {
    structures: { pattern: string; content: string; explanation: string; }[];
    clauses: { type: string; content: string; explanation: string; }[];
    grammar_points: { point: string; point_cn?: string; explanation: string; }[];
}

export default function ParagraphBlock({ id, content, image_url, audio_path, annotations, isActiveForTTS, onPlayTTS }: ParagraphProps) {
    const [translation, setTranslation] = useState<TranslationResult | null>(null);
    const [syntax, setSyntax] = useState<SyntaxResult | null>(null);
    const [loadingAction, setLoadingAction] = useState<string | null>(null);
    const [activePanel, setActivePanel] = useState<'translation' | 'syntax' | null>(null);
    const [selectedWord, setSelectedWord] = useState<Annotation | null>(null);

    const handleTranslate = async () => {
        if (activePanel === 'translation') {
            setActivePanel(null);
            return;
        }
        if (translation) {
            setActivePanel('translation');
            return;
        }
        setLoadingAction('translation');
        try {
            const res = await api.post('/api/analyze/translation', null, { params: { paragraph_text: content } });
            setTranslation(res.data.translation);
            setActivePanel('translation');
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingAction(null);
        }
    };

    const handleSyntax = async () => {
        if (activePanel === 'syntax') {
            setActivePanel(null);
            return;
        }
        if (syntax) {
            setActivePanel('syntax');
            return;
        }
        setLoadingAction('syntax');
        try {
            const res = await api.post('/api/analyze/syntax', null, { params: { paragraph_text: content } });
            setSyntax(res.data.syntax);
            setActivePanel('syntax');
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingAction(null);
        }
    };

    // Render Text with Highlights
    const renderContent = () => {
        if (!annotations || annotations.length === 0) return <p className="text-lg md:text-xl text-slate-800 dark:text-slate-200 leading-[1.8] font-normal tracking-wide pr-10 xl:pr-0">{content}</p>;

        // Split content by words and reconstruct (simplified approach)
        // Better approach: Find indices of words and splice.
        // For simplicity: We will use a regex replace approach with React render.
        // Warning: This is tricky with overlapping phrases.
        // Given the constraint, let's try to match phrases.

        let parts: (string | React.ReactNode)[] = [content];

        annotations.forEach((anno) => {
            const newParts: (string | React.ReactNode)[] = [];
            parts.forEach((part) => {
                if (typeof part === 'string') {
                    const regex = new RegExp(`\\b(${anno.word})\\b`, 'gi');
                    const split = part.split(regex);
                    // split results in ["prefix", "match", "suffix", ...]
                    for (let i = 0; i < split.length; i++) {
                        if (split[i].toLowerCase() === anno.word.toLowerCase()) {
                            newParts.push(
                                <span key={`${anno.word}-${i}`} onClick={() => setSelectedWord(anno)} className="highlight-word relative group">
                                    {split[i]}
                                </span>
                            );
                        } else {
                            newParts.push(split[i]);
                        }
                    }
                } else {
                    newParts.push(part);
                }
            });
            parts = newParts;
        });

        return <p className="text-lg md:text-xl text-slate-800 dark:text-slate-200 leading-[1.8] font-normal tracking-wide pr-10 xl:pr-0">{parts}</p>;
    };

    return (
        <div className={clsx(
            "paragraph-container relative group/para transition-all duration-500 p-3 rounded-2xl border border-transparent",
            isActiveForTTS ? "bg-blue-50/50 dark:bg-blue-900/10 border-blue-200/50 dark:border-blue-800/50 ring-1 ring-blue-400/20 shadow-lg shadow-blue-500/5" : "hover:bg-slate-50/50 dark:hover:bg-slate-800/20"
        )}>

            {/* Right Side Buttons (Popover) - Redesigned to be subtle */}
            <div className="absolute right-2 top-2 xl:-right-12 xl:top-0 xl:bottom-0 xl:pt-1 z-20 flex items-start opacity-100 xl:opacity-0 xl:group-hover/para:opacity-100 transition-all duration-300">
                <Popover className="relative">
                    <Popover.Button className="p-2 rounded-lg text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all outline-none focus:ring-2 focus:ring-slate-200 dark:focus:ring-slate-700 active:scale-95">
                        <span className="material-symbols-outlined text-[20px]">more_horiz</span>
                    </Popover.Button>
                    <Transition
                        as={Fragment}
                        enter="transition ease-out duration-200"
                        enterFrom="opacity-0 translate-y-1 scale-95"
                        enterTo="opacity-100 translate-y-0 scale-100"
                        leave="transition ease-in duration-150"
                        leaveFrom="opacity-100 translate-y-0 scale-100"
                        leaveTo="opacity-0 translate-y-1 scale-95"
                    >
                        <Popover.Panel className="absolute right-0 mt-2 w-48 origin-top-right rounded-xl bg-white dark:bg-[#1e293b] shadow-2xl border border-slate-100 dark:border-slate-700/50 overflow-hidden z-30 ring-1 ring-black/5">
                            <div className="p-1.5 flex flex-col gap-1">
                                <button
                                    onClick={handleTranslate}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg transition-all active:scale-[0.97] group/btn"
                                >
                                    <span className="material-symbols-outlined text-[20px] text-slate-400 group-hover/btn:text-blue-500 transition-colors">translate</span>
                                    <span>Translate</span>
                                </button>
                                <button
                                    onClick={handleSyntax}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 hover:text-emerald-600 dark:hover:text-emerald-400 rounded-lg transition-all active:scale-[0.97] group/btn"
                                >
                                    <span className="material-symbols-outlined text-[20px] text-slate-400 group-hover/btn:text-emerald-500 transition-colors">school</span>
                                    <span>Syntax</span>
                                </button>
                                <button
                                    onClick={() => onPlayTTS(content, audio_path)}
                                    className={clsx(
                                        "w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-lg transition-all active:scale-[0.97] group/btn",
                                        isActiveForTTS
                                            ? "bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400"
                                            : "text-slate-600 dark:text-slate-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 hover:text-purple-600 dark:hover:text-purple-400"
                                    )}
                                >
                                    <span className={clsx(
                                        "material-symbols-outlined text-[20px] transition-colors",
                                        isActiveForTTS ? "text-purple-500 animate-pulse" : "text-slate-400 group-hover/btn:text-purple-500"
                                    )}>
                                        {isActiveForTTS ? "pause_circle" : "volume_up"}
                                    </span>
                                    <span>{isActiveForTTS ? "Reading..." : "Read"}</span>
                                </button>
                            </div>
                        </Popover.Panel>
                    </Transition>
                </Popover>
            </div>

            {/* Paragraph Content OR Image */}
            {image_url ? (
                <div className="my-6 rounded-lg overflow-hidden shadow-sm border border-slate-100 dark:border-slate-700/50">
                    <img
                        src={image_url}
                        alt="Article Image"
                        className="w-full h-auto object-cover max-h-[500px]"
                        loading="lazy"
                    />
                </div>
            ) : (
                renderContent()
            )}

            {/* Inline Action Panels */}
            {activePanel === 'translation' && (
                <div className="mt-4 bg-slate-50 rounded-xl border border-slate-200 overflow-hidden shadow-sm animate-fade-in font-lexend">
                    <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-100">
                        <div className="flex items-center gap-2">
                            <div className="size-6 rounded bg-blue-50 flex items-center justify-center">
                                <span className="material-symbols-outlined text-[16px] text-[#137fec]">translate</span>
                            </div>
                            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Smart Translation</span>
                        </div>
                        {translation?.style && (
                            <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full font-medium">{translation.style}</span>
                        )}
                    </div>
                    <div className="p-5 space-y-6">
                        <p className="text-slate-900 text-lg leading-relaxed font-medium">
                            {translation?.translation || "Loading..."}
                        </p>

                        {translation?.key_phrases && translation.key_phrases.length > 0 && (
                            <div className="pt-4 border-t border-slate-100">
                                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">Key Phrases</h4>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {translation.key_phrases.map((phrase, i) => (
                                        <div key={i} className="flex flex-col p-2.5 rounded-lg bg-white border border-slate-100 shadow-sm">
                                            <span className="text-sm font-bold text-slate-900">{phrase.en}</span>
                                            <span className="text-xs text-slate-500 mt-0.5">{phrase.cn}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {activePanel === 'syntax' && (
                <div className="mt-4 bg-[#fcfcfd] rounded-xl border border-slate-200 shadow-sm animate-fade-in font-lexend">
                    <div className="flex items-center gap-2 px-4 py-3 bg-white border-b border-slate-100 rounded-t-xl">
                        <div className="size-6 rounded bg-emerald-50 flex items-center justify-center">
                            <span className="material-symbols-outlined text-[16px] text-emerald-600">psychology</span>
                        </div>
                        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Grammar Insight (句法语法分析)</span>
                    </div>
                    <div className="p-5 space-y-8">
                        {syntax?.structures && syntax.structures.length > 0 && (
                            <div>
                                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">Sentence Patterns (句型结构)</h4>
                                <div className="space-y-4">
                                    {syntax.structures.map((s, i) => (
                                        <div key={i} className="relative pl-4 border-l-2 border-emerald-500/30">
                                            <div className="flex flex-col mb-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded uppercase">{s.pattern}</span>
                                                    <span className="text-sm text-slate-900 font-bold">{s.content}</span>
                                                </div>
                                            </div>
                                            <p className="text-xs text-slate-500 leading-relaxed font-medium">{s.explanation}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {syntax?.clauses && syntax.clauses.length > 0 && (
                            <div>
                                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">Clause Analysis (从句分析)</h4>
                                <div className="grid grid-cols-1 gap-3">
                                    {syntax.clauses.map((c, i) => (
                                        <div key={i} className="p-3 rounded-xl bg-white border border-slate-100 shadow-sm transition-all hover:shadow-md">
                                            <div className="flex items-center gap-2 mb-1.5">
                                                <span className="size-1.5 rounded-full bg-blue-500"></span>
                                                <span className="text-xs font-bold text-slate-700">{c.type}</span>
                                            </div>
                                            <p className="text-sm text-slate-900 mb-1 font-bold">{c.content}</p>
                                            <p className="text-xs text-slate-500 font-medium">{c.explanation}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {syntax?.grammar_points && syntax.grammar_points.length > 0 && (
                            <div>
                                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">Grammar Points (语法要点)</h4>
                                <div className="flex flex-wrap gap-3">
                                    {syntax.grammar_points.map((g, i) => (
                                        <div key={i} className="group/grammar relative hover:z-50">
                                            <div className="px-3 py-2 rounded-lg bg-orange-50 border border-orange-100 text-orange-700 text-xs font-bold hover:bg-orange-100 transition-all cursor-default flex flex-col items-center min-w-[100px] text-center">
                                                <span>{g.point}</span>
                                                {g.point_cn && <span className="text-[10px] opacity-80 mt-0.5 font-medium">{g.point_cn}</span>}
                                            </div>
                                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-56 p-3 bg-slate-900/95 backdrop-blur-md text-white text-[11px] rounded-xl shadow-2xl opacity-0 group-hover/grammar:opacity-100 transition-all duration-200 pointer-events-none z-[100] border border-white/10 ring-1 ring-black/20 translate-y-2 group-hover/grammar:translate-y-0 text-left">
                                                <p className="leading-relaxed font-medium">{g.explanation}</p>
                                                <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-slate-900/95"></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {!syntax && <div className="text-slate-500 text-sm">Loading grammar analysis...</div>}
                    </div>
                </div>
            )}

            {/* Centered Modal for Vocabulary */}
            <Transition appear show={!!selectedWord} as={Fragment}>
                <Dialog as="div" className="relative z-50" onClose={() => setSelectedWord(null)}>
                    <Transition.Child
                        as={Fragment}
                        enter="ease-out duration-300"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="ease-in duration-200"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-black/25 backdrop-blur-sm" />
                    </Transition.Child>

                    <div className="fixed inset-0 overflow-y-auto">
                        <div className="flex min-h-full items-center justify-center p-4 text-center">
                            <Transition.Child
                                as={Fragment}
                                enter="ease-out duration-300"
                                enterFrom="opacity-0 scale-95"
                                enterTo="opacity-100 scale-100"
                                leave="ease-in duration-200"
                                leaveFrom="opacity-100 scale-100"
                                leaveTo="opacity-0 scale-95"
                            >
                                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-[#1e293b] p-6 text-left align-middle shadow-xl transition-all border border-slate-200 dark:border-slate-700">
                                    <Dialog.Title as="div" className="flex justify-between items-start">
                                        <div className="flex flex-col">
                                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">{selectedWord?.word}</h3>
                                            <span className="text-sm font-mono text-[#137fec] mt-1">{selectedWord?.type}</span>
                                        </div>
                                        <button onClick={() => setSelectedWord(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                                            <span className="material-symbols-outlined">close</span>
                                        </button>
                                    </Dialog.Title>
                                    <div className="mt-4 space-y-4">
                                        <div className="flex gap-3 text-left">
                                            <div className="shrink-0 mt-0.5">
                                                <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold uppercase tracking-wider">Def</span>
                                            </div>
                                            <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">{selectedWord?.definition}</p>
                                        </div>
                                        {selectedWord?.context_example && (
                                            <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border-l-2 border-[#137fec]">
                                                <p className="text-slate-600 dark:text-slate-400 text-sm italic">"{selectedWord.context_example}"</p>
                                            </div>
                                        )}
                                    </div>
                                    <div className="mt-6 flex justify-end gap-3">
                                        <button onClick={() => setSelectedWord(null)} className="px-4 py-2 text-sm font-medium text-slate-500 hover:bg-slate-100 rounded-lg transition-colors">Close</button>
                                    </div>
                                </Dialog.Panel>
                            </Transition.Child>
                        </div>
                    </div>
                </Dialog>
            </Transition>
        </div>
    );
}
