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

  async function encryptPassword(password: string): Promise<string> {
    try {
      await fetchPublicKey()
      if (publicKey.value) {
        return encrypt(password)
      }
    } catch {
      console.warn('Failed to fetch public key, sending password in plaintext')
    }
    return password
  }

  async function loginWithPassword(account: string, password: string, rememberMe: boolean) {
    try {
      const finalPassword = await encryptPassword(password)
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

  async function register(payload: {
    phone: string
    smsCode: string
    nickname: string
    password: string
    agreedProtocolVersion: string
  }) {
    try {
      const finalPassword = await encryptPassword(payload.password)
      await authStore.register({
        ...payload,
        password: finalPassword,
      })
      redirectAfterLogin()
    } catch (err) {
      console.error('Register failed:', err)
      throw err
    }
  }

  async function emailRegister(payload: {
    email: string
    emailCode: string
    nickname: string
    password: string
    agreedProtocolVersion: string
  }) {
    try {
      const finalPassword = await encryptPassword(payload.password)
      await authStore.emailRegister({
        ...payload,
        password: finalPassword,
      })
      redirectAfterLogin()
    } catch (err) {
      console.error('Email register failed:', err)
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
    register,
    emailRegister,
    logout,
  }
}
