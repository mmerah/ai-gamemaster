import { apiClient } from './apiClient'

// Response types
interface Voice {
  id: string
  name: string
  language?: string
  gender?: string
  preview_url?: string
}

interface VoicesResponse {
  voices: Voice[]
}

interface SynthesizeResponse {
  audio_path: string
  audio_url?: string
  duration?: number
}

interface NarrationToggleResponse {
  enabled: boolean
  message?: string
}

interface NarrationStatusResponse {
  enabled: boolean
  voice_id?: string
}

/**
 * TTS API service for handling text-to-speech functionality
 */
export const ttsApi = {
  /**
   * Get available TTS voices
   */
  async getVoices(): Promise<VoicesResponse> {
    const response = await apiClient.get<VoicesResponse>('/api/tts/voices')
    return response.data
  },

  /**
   * Synthesize speech from text
   */
  async synthesize(text: string, voiceId: string): Promise<SynthesizeResponse> {
    const response = await apiClient.post<SynthesizeResponse>('/api/tts/synthesize', {
      text,
      voice_id: voiceId
    })
    return response.data
  },

  /**
   * Generate a voice preview with sample text
   */
  async previewVoice(voiceId: string, sampleText?: string | null): Promise<SynthesizeResponse> {
    const text = sampleText || "Welcome to your adventure! The path ahead is filled with mystery and excitement."
    return this.synthesize(text, voiceId)
  },

  /**
   * Toggle narration on/off for the current session
   */
  async toggleNarration(enabled: boolean): Promise<NarrationToggleResponse> {
    const response = await apiClient.post<NarrationToggleResponse>('/api/tts/narration/toggle', {
      enabled
    })
    return response.data
  },

  /**
   * Get current narration status
   */
  async getNarrationStatus(): Promise<NarrationStatusResponse> {
    const response = await apiClient.get<NarrationStatusResponse>('/api/tts/narration/status')
    return response.data
  }
}

// Export types for use in other modules
export type { Voice, VoicesResponse, SynthesizeResponse, NarrationToggleResponse, NarrationStatusResponse }
