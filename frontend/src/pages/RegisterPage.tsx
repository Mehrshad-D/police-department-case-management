import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { authApi } from '@/api/endpoints'
import { getApiErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function RegisterPage() {
  const [form, setForm] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    full_name: '',
    national_id: '',
  })
  const navigate = useNavigate()

  const register = useMutation({
    mutationFn: () => authApi.register(form),
    onSuccess: () => {
      navigate('/login')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.username || !form.password || !form.email || !form.phone || !form.full_name || !form.national_id)
      return
    register.mutate()
  }

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [key]: e.target.value }))

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-xl"
      >
        <h1 className="text-xl font-semibold text-slate-100 mb-6">Create account</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Username</label>
            <Input value={form.username} onChange={update('username')} placeholder="Username" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Password</label>
            <Input type="password" value={form.password} onChange={update('password')} placeholder="••••••••" minLength={8} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Email</label>
            <Input type="email" value={form.email} onChange={update('email')} placeholder="Email" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Phone</label>
            <Input value={form.phone} onChange={update('phone')} placeholder="Phone" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Full name</label>
            <Input value={form.full_name} onChange={update('full_name')} placeholder="Full name" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">National ID</label>
            <Input value={form.national_id} onChange={update('national_id')} placeholder="National ID" required />
          </div>
          {register.isError && (
            <p className="text-sm text-red-400">{getApiErrorMessage(register.error)}</p>
          )}
          <Button type="submit" className="w-full" loading={register.isPending}>
            Register
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-400 hover:underline">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
