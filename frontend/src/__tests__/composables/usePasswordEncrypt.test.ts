import { describe, it, expect, vi } from 'vitest'
import { usePasswordEncrypt } from '@/composables/usePasswordEncrypt'
import { authApi } from '@/services/authApi'

vi.mock('@/services/authApi', () => ({
  authApi: {
    getPublicKey: vi.fn(),
  },
}))

describe('usePasswordEncrypt', () => {
  it('fetchPublicKey retrieves and caches the key', async () => {
    vi.mocked(authApi.getPublicKey).mockResolvedValue({
      data: { data: { publicKey: 'mock-public-key' } },
    } as any)

    const { publicKey, fetchPublicKey } = usePasswordEncrypt()
    await fetchPublicKey()

    expect(publicKey.value).toBe('mock-public-key')
    expect(authApi.getPublicKey).toHaveBeenCalledTimes(1)

    // 再次调用不触发 API
    await fetchPublicKey()
    expect(authApi.getPublicKey).toHaveBeenCalledTimes(1)
  })

  it('encrypt returns a non-empty encrypted string', () => {
    const { encrypt } = usePasswordEncrypt()
    const result = encrypt('password123')
    // JSEncrypt may still produce output without a valid key set
    expect(typeof result).toBe('string')
    expect(result.length).toBeGreaterThan(0)
  })
})
