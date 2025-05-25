import { apiClient } from './apiClient'

/**
 * TTS API service for handling text-to-speech functionality
 */
export const ttsApi = {
  /**
   * Get available TTS voices
   */
  async getVoices() {
    const response = await apiClient.get('/api/tts/voices')
    return response.data
  },

  /**
   * Synthesize speech from text
   * @param {string} text - Text to synthesize
   * @param {string} voiceId - Voice ID to use
   */
  async synthesize(text, voiceId) {
    const response = await apiClient.post('/api/tts/synthesize', {
      text,
      voice_id: voiceId
    })
    return response.data
  },

  /**
   * Generate a voice preview with sample text
   * @param {string} voiceId - Voice ID to preview
   * @param {string} sampleText - Optional sample text (uses default if not provided)
   */
  async previewVoice(voiceId, sampleText = null) {
    const text = sampleText || "Welcome to your adventure! The path ahead is filled with mystery and excitement."
    return this.synthesize(text, voiceId)
  }
}
