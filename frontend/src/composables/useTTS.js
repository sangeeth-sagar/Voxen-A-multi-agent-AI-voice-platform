import { useLanguage } from './useLanguage'

const { getTtsLocale } = useLanguage()

let currentUtterance = null

// Wait for voices to load (required on Chrome)
function getVoices() {
  return new Promise(resolve => {
    const voices = speechSynthesis.getVoices()
    if (voices.length) return resolve(voices)
    speechSynthesis.onvoiceschanged = () => resolve(speechSynthesis.getVoices())
  })
}

async function speak(text, languageCode = null) {
  if (!text) return

  // Stop anything currently playing
  speechSynthesis.cancel()

  const LOCALE_MAP = { en: 'en-GB', hi: 'hi-IN', mr: 'mr-IN', ml: 'ml-IN' }
  const locale = languageCode ? LOCALE_MAP[languageCode] : getTtsLocale()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = 0.92
  utterance.pitch = 1.0
  utterance.volume = 1.0

  // Fallback voice chain — if exact locale missing, try these in order
  const VOICE_FALLBACK_CHAIN = {
    'mr-IN': ['mr-IN', 'hi-IN', 'en-IN', 'en-US'],  // Marathi → Hindi → Indian English → English
    'ml-IN': ['ml-IN', 'hi-IN', 'en-IN', 'en-US'],  // Malayalam → Hindi → Indian English → English
    'hi-IN': ['hi-IN', 'en-IN', 'en-US'],
    'en-US': ['en-US', 'en-GB', 'en'],
  }

  const voices = await getVoices()

  // Try each fallback locale in order until a voice is found
  const fallbackChain = VOICE_FALLBACK_CHAIN[locale] || [locale, 'en-US']
  let selectedVoice = null

  for (const fallbackLocale of fallbackChain) {
    selectedVoice =
      voices.find(v => v.lang === fallbackLocale) ||
      voices.find(v => v.lang.startsWith(fallbackLocale.split('-')[0]))
    if (selectedVoice) break
  }

  if (selectedVoice) {
    utterance.voice = selectedVoice
    utterance.lang = selectedVoice.lang
  } else {
    // Last resort — just set lang and let browser decide
    utterance.lang = locale
  }

  currentUtterance = utterance
  speechSynthesis.speak(utterance)

  return new Promise((resolve) => {
    utterance.onend = resolve
    utterance.onerror = resolve  // resolve even on error so app doesn't hang
  })
}

function stop() {
  speechSynthesis.cancel()
  currentUtterance = null
}

function isSpeaking() {
  return speechSynthesis.speaking
}

export function useTTS() {
  return { speak, stop, isSpeaking }
}
