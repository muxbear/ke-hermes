import { ref } from 'vue'
import JSEncrypt from 'jsencrypt'
import { authApi } from '@/services/authApi'

export function usePasswordEncrypt() {
  const publicKey = ref('')

  async function fetchPublicKey(): Promise<void> {
    if (publicKey.value) return
    const res = await authApi.getPublicKey()
    publicKey.value = res.data.data.publicKey
  }

  function encrypt(password: string): string {
    const jsEncrypt = new JSEncrypt()
    jsEncrypt.setPublicKey(publicKey.value)
    const encrypted = jsEncrypt.encrypt(password)
    if (!encrypted) {
      throw new Error('RSA encryption failed')
    }
    return encrypted
  }

  return { publicKey, fetchPublicKey, encrypt }
}
