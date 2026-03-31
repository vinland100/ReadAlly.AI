/**
 * Pure frontend word pronunciation hook.
 *
 * Strategy:
 *   1. Try Free Dictionary API (dictionaryapi.dev) for real American English audio.
 *   2. Fallback to browser Web Speech API (SpeechSynthesis) with en-US voice.
 *
 * Includes a simple in-memory cache so repeated clicks don't re-fetch.
 */

interface WordPronunciation {
  audioUrl: string | null;
  phonetic: string | null;
}

const pronunciationCache = new Map<string, WordPronunciation>(); // word -> { audioUrl, phonetic }
let currentAudio: HTMLAudioElement | null = null;
// Cancellation token: increment to cancel any running sequence
let cancelToken = 0;

/**
 * Fetch the US pronunciation audio URL and phonetic from Free Dictionary API.
 * Returns the data object or null if unavailable.
 */
export async function getWordPronunciation(word: string): Promise<WordPronunciation | null> {
  const lower = word.toLowerCase().trim();
  if (!lower) return null;

  // Check cache first
  if (pronunciationCache.has(lower)) {
    return pronunciationCache.get(lower)!;
  }

  try {
    const res = await fetch(
      `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(lower)}`
    );
    if (!res.ok) return null;

    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) return null;

    let bestAudio: string | null = null;
    let bestPhonetic: string | null = null;

    // Priority Pass 1: Look for US-specific audio and its associated text
    // This solves words like "glass" which have both US and UK entries.
    for (const entry of data) {
      if (entry.phonetics && Array.isArray(entry.phonetics)) {
        for (const ph of entry.phonetics) {
          const isUS = ph.audio && (ph.audio.includes('-us') || ph.audio.includes('_us'));
          if (isUS && ph.text) {
            const result = { audioUrl: ph.audio, phonetic: ph.text };
            pronunciationCache.set(lower, result);
            return result;
          }
        }
      }
    }

    // Priority Pass 2: Fallback to any available audio and any available phonetic
    // If we find US audio here, we'll keep it but continue to look for phonetic text.
    for (const entry of data) {
      if (entry.phonetic && !bestPhonetic) bestPhonetic = entry.phonetic;
      
      if (entry.phonetics && Array.isArray(entry.phonetics)) {
        for (const ph of entry.phonetics) {
          // Prefer US audio URL if found
          if (ph.audio && (ph.audio.includes('-us') || ph.audio.includes('_us'))) {
            bestAudio = ph.audio;
          } else if (!bestAudio && ph.audio) {
            bestAudio = ph.audio;
          }

          if (ph.text && !bestPhonetic) {
            bestPhonetic = ph.text;
          }
        }
      }
    }

    const result = { audioUrl: bestAudio, phonetic: bestPhonetic };
    pronunciationCache.set(lower, result);
    return result;
  } catch {
    return null;
  }
}

/**
 * Legacy support/Internal helper for audio URL only
 */
async function fetchAudioUrl(word: string): Promise<string | null> {
  const data = await getWordPronunciation(word);
  return data?.audioUrl || null;
}

/**
 * Play pronunciation of a single word using Audio API.
 * Falls back to Web Speech API if no audio URL is available.
 */
async function playWordAudio(audioUrl: string): Promise<void> {
  // Stop any currently playing audio
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }

  return new Promise<void>((resolve, reject) => {
    const audio = new Audio(audioUrl);
    currentAudio = audio;
    audio.onended = () => {
      currentAudio = null;
      resolve();
    };
    audio.onerror = () => {
      currentAudio = null;
      reject(new Error('Audio playback failed'));
    };
    audio.play().catch((err) => {
      currentAudio = null;
      reject(err);
    });
  });
}

/** Simple promise-based delay */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Fallback: use the browser's SpeechSynthesis API to pronounce a word.
 */
function speakWithSpeechSynthesis(word: string): void {
  if (!('speechSynthesis' in window)) return;

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(word);
  utterance.lang = 'en-US';
  utterance.rate = 0.9;
  utterance.pitch = 1;

  // Try to find a US English voice
  const voices = window.speechSynthesis.getVoices();
  const usVoice = voices.find(
    (v) => v.lang === 'en-US' || v.lang.startsWith('en-US')
  );
  if (usVoice) {
    utterance.voice = usVoice;
  }

  window.speechSynthesis.speak(utterance);
}

/**
 * Main function: pronounce a single English word.
 * Fetches audio on-demand, caches it, and plays it.
 */
export async function pronounceWord(word: string): Promise<void> {
  const clean = word.replace(/[^a-zA-Z'-]/g, '').trim();
  if (!clean) return;

  try {
    const audioUrl = await fetchAudioUrl(clean);
    if (audioUrl) {
      await playWordAudio(audioUrl);
    } else {
      // Fallback to speech synthesis
      speakWithSpeechSynthesis(clean);
    }
  } catch {
    // If Audio API fails, fallback to speech synthesis
    speakWithSpeechSynthesis(clean);
  }
}

/**
 * Pronounce a list of words sequentially, with a short pause between each.
 * Any previously running sequence is automatically cancelled first.
 */
export async function pronouncePhrase(words: string[]): Promise<void> {
  // Cancel any in-progress sequence
  cancelToken++;
  const myToken = cancelToken;

  // Also stop whatever is currently playing
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }

  for (const word of words) {
    // Check if we've been superseded
    if (cancelToken !== myToken) return;

    const clean = word.replace(/[^a-zA-Z'-]/g, '').trim();
    if (!clean) continue;

    try {
      const audioUrl = await fetchAudioUrl(clean);
      if (cancelToken !== myToken) return;

      if (audioUrl) {
        await playWordAudio(audioUrl);
      } else {
        // Fallback: wrap SpeechSynthesis in a promise so we await it
        await new Promise<void>((resolve) => {
          if (!('speechSynthesis' in window)) { resolve(); return; }
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(clean);
          utterance.lang = 'en-US';
          utterance.rate = 0.9;
          const voices = window.speechSynthesis.getVoices();
          const usVoice = voices.find((v) => v.lang === 'en-US' || v.lang.startsWith('en-US'));
          if (usVoice) utterance.voice = usVoice;
          utterance.onend = () => resolve();
          utterance.onerror = () => resolve();
          window.speechSynthesis.speak(utterance);
        });
      }
    } catch {
      speakWithSpeechSynthesis(clean);
    }

    // Short pause between words (300ms), but bail if cancelled
    if (cancelToken !== myToken) return;
    await delay(300);
  }
}

/**
 * Stop any currently playing pronunciation.
 */
export function stopPronunciation(): void {
  // Increment token to cancel any running sequence
  cancelToken++;

  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}
