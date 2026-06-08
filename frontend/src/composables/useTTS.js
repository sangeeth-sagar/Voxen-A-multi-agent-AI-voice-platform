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

  speechSynthesis.cancel()

  const LOCALE_MAP = { en: 'en-GB', hi: 'hi-IN', mr: 'mr-IN', ml: 'ml-IN' }
  const locale = languageCode ? LOCALE_MAP[languageCode] : getTtsLocale()

  const MAX_CHARS = 200
  const chunks = text.length > MAX_CHARS ? splitTextIntoChunks(text, MAX_CHARS) : [text]

  const VOICE_FALLBACK_CHAIN = {
    'en-GB': ['en-GB', 'en-US', 'en-AU', 'en-IN', 'en'],
    'en-US': ['en-US', 'en-GB', 'en-AU', 'en'],
    'hi-IN': ['hi-IN', 'en-IN', 'en-US'],
    'mr-IN': ['mr-IN', 'hi-IN', 'en-IN', 'en-US'],
    'ml-IN': ['ml-IN', 'hi-IN', 'en-IN', 'en-US'],
  }

  const voices = await getVoices()
  const fallbackChain = VOICE_FALLBACK_CHAIN[locale] || [locale, 'en-US']
  let selectedVoice = null

  for (const fallbackLocale of fallbackChain) {
    selectedVoice =
      voices.find(v => v.lang === fallbackLocale) ||
      voices.find(v => v.lang.startsWith(fallbackLocale.split('-')[0]))
    if (selectedVoice) break
  }

  for (const chunk of chunks) {
    await new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(chunk)
      utterance.rate = 0.92
      utterance.pitch = 1.0
      utterance.volume = 1.0

      if (selectedVoice) {
        utterance.voice = selectedVoice
        utterance.lang = selectedVoice.lang
      } else {
        utterance.lang = locale
      }

      const resumeTimer = setInterval(() => {
        if (speechSynthesis.paused) speechSynthesis.resume()
      }, 500)

      utterance.onend = () => { clearInterval(resumeTimer); resolve() }
      utterance.onerror = (e) => {
        clearInterval(resumeTimer)
        console.warn('[useTTS] error:', e.error)
        resolve()
      }

      currentUtterance = utterance
      speechSynthesis.speak(utterance)
    })
  }
}

function splitTextIntoChunks(text, maxChars) {
  if (text.length <= maxChars) return [text]
  const chunks = []
  let remaining = text
  while (remaining.length > 0) {
    if (remaining.length <= maxChars) { chunks.push(remaining); break }
    const slice = remaining.slice(0, maxChars)
    const lastBreak = Math.max(
      slice.lastIndexOf('. '), slice.lastIndexOf('? '),
      slice.lastIndexOf('! '), slice.lastIndexOf('। '), slice.lastIndexOf('\n')
    )
    const cutAt = lastBreak > 30 ? lastBreak + 1 : maxChars
    chunks.push(remaining.slice(0, cutAt).trim())
    remaining = remaining.slice(cutAt).trim()
  }
  return chunks.filter(c => c.length > 0)
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
