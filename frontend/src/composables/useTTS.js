import { useLanguage } from './useLanguage'

const { getTtsLocale } = useLanguage()

let currentUtterance = null

function getVoices() {
  return new Promise(resolve => {
    const voices = speechSynthesis.getVoices()
    if (voices.length) return resolve(voices)
    speechSynthesis.onvoiceschanged = () => resolve(speechSynthesis.getVoices())
    setTimeout(() => resolve(speechSynthesis.getVoices()), 1000)
  })
}

const VOICE_FALLBACK_CHAIN = {
  'en-GB': ['en-GB', 'en-US', 'en-AU', 'en'],
  'en-US': ['en-US', 'en-GB', 'en'],
  'hi-IN': ['hi-IN', 'en-IN', 'en-US'],
  'mr-IN': ['hi-IN', 'en-IN', 'en-US'],
  'ml-IN': ['hi-IN', 'en-IN', 'en-US'],
}

function chunkText(text, maxLen = 180) {
  if (text.length <= maxLen) return [text]
  const chunks = []
  const sentences = text.match(/[^.!?।\n]+[.!?।\n]*/g) || [text]
  let current = ''
  for (const s of sentences) {
    if ((current + s).length > maxLen && current.length > 0) {
      chunks.push(current.trim())
      current = s
    } else {
      current += s
    }
  }
  if (current.trim()) chunks.push(current.trim())
  return chunks.filter(c => c.length > 0)
}

async function speak(text, languageCode = null) {
  if (!text) return
  speechSynthesis.cancel()

  const LOCALE_MAP = {
    en: 'en-US',
    hi: 'hi-IN',
    mr: 'hi-IN',
    ml: 'hi-IN',
  }
  const locale = languageCode ? (LOCALE_MAP[languageCode] || 'en-US') : getTtsLocale()

  const voices = await getVoices()
  const chain = VOICE_FALLBACK_CHAIN[locale] || [locale, 'en-US']
  let selectedVoice = null
  for (const l of chain) {
    selectedVoice =
      voices.find(v => v.lang === l) ||
      voices.find(v => v.lang.startsWith(l.split('-')[0]))
    if (selectedVoice) break
  }

  const chunks = chunkText(text, 180)

  for (const chunk of chunks) {
    await new Promise((resolve) => {
      const u = new SpeechSynthesisUtterance(chunk)
      if (selectedVoice) { u.voice = selectedVoice; u.lang = selectedVoice.lang }
      else u.lang = locale
      u.rate = 0.9
      u.pitch = 1.0
      u.volume = 1.0

      const timer = setInterval(() => {
        if (speechSynthesis.paused) speechSynthesis.resume()
      }, 250)

      u.onend = () => { clearInterval(timer); resolve() }
      u.onerror = (e) => { clearInterval(timer); console.warn('[TTS]', e.error); resolve() }

      currentUtterance = u
      try { speechSynthesis.speak(u) } catch (e) { clearInterval(timer); resolve() }
    })
  }
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
