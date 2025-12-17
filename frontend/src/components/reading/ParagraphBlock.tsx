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
    annotations: Annotation[];
    isActiveForTTS: boolean;
    onPlayTTS: (text: string) => void; // Paragraph-level TTS
}

export default function ParagraphBlock({ id, content, annotations, isActiveForTTS, onPlayTTS }: ParagraphProps) {
    const [translation, setTranslation] = useState<string | null>(null);
    const [syntax, setSyntax] = useState<string | null>(null);
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
        if (!annotations || annotations.length === 0) return <p className="text-lg md:text-xl text-slate-800 dark:text-slate-200 leading-[1.8] font-normal tracking-wide">{content}</p>;

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

        return <p className="text-lg md:text-xl text-slate-800 dark:text-slate-200 leading-[1.8] font-normal tracking-wide">{parts}</p>;
    };

    return (
        <div className={clsx("paragraph-container relative group transition-all duration-300 p-2 rounded-xl", isActiveForTTS ? "bg-blue-50/10 ring-2 ring-[#137fec]" : "")}>

            {/* Right Side Buttons (Popover) */}
            <div className="absolute -right-12 top-1 z-20 opacity-100">
                <Popover className="relative">
                    <Popover.Button className="p-1.5 rounded-full text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 shadow-sm ring-2 ring-[#137fec]/20 outline-none hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                        <span className="material-symbols-outlined text-[20px]">more_vert</span>
                    </Popover.Button>
                    <Transition
                        as={Fragment}
                        enter="transition ease-out duration-200"
                        enterFrom="opacity-0 translate-y-1"
                        enterTo="opacity-100 translate-y-0"
                        leave="transition ease-in duration-150"
                        leaveFrom="opacity-100 translate-y-0"
                        leaveTo="opacity-0 translate-y-1"
                    >
                        <Popover.Panel className="absolute right-0 mt-2 w-56 origin-top-right rounded-xl bg-white dark:bg-[#1e293b] shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden z-30">
                            <div className="p-1 flex flex-col gap-1">
                                <button onClick={handleTranslate} className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg transition-colors text-left">
                                    <span className="material-symbols-outlined text-[20px] text-blue-500">translate</span>
                                    <span>Translate Paragraph</span>
                                </button>
                                <button onClick={handleSyntax} className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg transition-colors text-left">
                                    <span className="material-symbols-outlined text-[20px] text-emerald-500">school</span>
                                    <span>Syntax Analysis</span>
                                </button>
                                <button onClick={() => onPlayTTS(content)} className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50 rounded-lg transition-colors text-left">
                                    <span className="material-symbols-outlined text-[20px] text-purple-500">volume_up</span>
                                    <span>Read Paragraph</span>
                                </button>
                            </div>
                        </Popover.Panel>
                    </Transition>
                </Popover>
            </div>

            {/* Paragraph Text */}
            {renderContent()}

            {/* Inline Action Panels */}
            {activePanel === 'translation' && (
                <div className="mt-4 bg-slate-50 dark:bg-[#18232e] rounded-xl border border-slate-200 dark:border-slate-700/60 overflow-hidden shadow-inner animate-fade-in">
                    <div className="flex items-center gap-2 px-4 py-2 bg-blue-50/50 dark:bg-blue-900/10 border-b border-blue-100 dark:border-blue-900/20">
                        <span className="material-symbols-outlined text-[16px] text-[#137fec]">auto_awesome</span>
                        <span className="text-xs font-bold text-[#137fec] uppercase tracking-wider">AI Translation</span>
                    </div>
                    <div className="p-4">
                        <p className="text-slate-600 dark:text-slate-300 text-base leading-relaxed italic">{translation || "Loading translation..."}</p>
                    </div>
                </div>
            )}

            {activePanel === 'syntax' && (
                <div className="mt-4 bg-slate-50 dark:bg-[#18232e] rounded-xl border border-slate-200 dark:border-slate-700/60 overflow-hidden shadow-inner animate-fade-in">
                    <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50/50 dark:bg-emerald-900/10 border-b border-emerald-100 dark:border-emerald-900/20">
                        <span className="material-symbols-outlined text-[16px] text-emerald-600 dark:text-emerald-400">psychology</span>
                        <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">Grammar Insight</span>
                    </div>
                    <div className="p-4">
                        <p className="text-slate-600 dark:text-slate-300 text-base leading-relaxed whitespace-pre-wrap">{syntax || "Loading analysis..."}</p>
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
