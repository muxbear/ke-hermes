import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePasswordEncrypt } from './usePasswordEncrypt'

export function useAuth() {
  const authStore = useAuthStore()
  const router = useRouter()
  const route = useRoute()
  const { publicKey, fetchPublicKey, encrypt } = usePasswordEncrypt()

  const loading = computed(() => authStore.isLoginLoading)
  const error = computed(() => authStore.loginError)

  async function loginWithPassword(account: string, password: string, rememberMe: boolean) {
    try {
      // 尝试获取公钥用于加密，失败则降级为明文传输
      let finalPassword = password
      try {
        await fetchPublicKey()
        if (publicKey.value) {
          finalPassword = encrypt(password)
        }
      } catch {
        // 无法获取公钥，使用明文密码（开发阶段降级方案）
        console.warn('Failed to fetch public key, sending password in plaintext')
      }

      await authStore.loginWithPassword({
        account,
        password: finalPassword,
        rememberMe,
      })
      redirectAfterLogin()
    } catch (err) {
      console.error('Login failed:', err)
      throw err
    }
  }

  async function loginWithPhone(phone: string, smsCode: string) {
    try {
      await authStore.loginWithPhone({ phone, smsCode })
      redirectAfterLogin()
    } catch (err) {
      console.error('Phone login failed:', err)
      throw err
    }
  }

  function redirectAfterLogin() {
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  }

  async function logout() {
    await authStore.logout()
    router.push('/login')
  }

  return {
    isAuthenticated: authStore.isAuthenticated,
    user: authStore.user,
    loading,
    error,
    loginWithPassword,
    loginWithPhone,
    logout,
  }
}
