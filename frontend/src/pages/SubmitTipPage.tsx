import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { tipsApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/authStore'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { getApiErrorMessage } from '@/api/client'

export function SubmitTipPage() {
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const [caseId, setCaseId] = useState<string>('')
  const [suspectId, setSuspectId] = useState<string>('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [success, setSuccess] = useState(false)

  const submit = useMutation({
    mutationFn: () =>
      tipsApi.create({
        case: caseId ? parseInt(caseId, 10) : undefined,
        suspect: suspectId ? parseInt(suspectId, 10) : undefined,
        title: title || 'Tip submission',
        description,
      }),
    onSuccess: () => {
      setSuccess(true)
      setTitle('')
      setDescription('')
      setCaseId('')
      setSuspectId('')
    },
  })

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <p className="text-slate-400 mb-4">You must be logged in to submit a tip.</p>
            <Link to="/login">
              <Button>Sign in</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/50">
        <div className="mx-auto max-w-2xl px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Submit a tip</h1>
          <Link to="/">
            <Button variant="ghost" size="sm">Home</Button>
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-2xl px-4 py-8">
        {success ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-green-400 font-medium mb-2">Tip submitted successfully.</p>
              <p className="text-slate-400 text-sm mb-4">An officer will review it. You will be notified of the outcome.</p>
              <Button onClick={() => setSuccess(false)} variant="secondary">Submit another tip</Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Tip form</CardTitle>
              <p className="text-slate-500 text-sm">Provide a case ID and/or suspect ID (optional), and describe your tip.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Case ID (optional)</label>
                <Input
                  type="number"
                  placeholder="e.g. 1"
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Suspect ID (optional)</label>
                <Input
                  type="number"
                  placeholder="e.g. 1"
                  value={suspectId}
                  onChange={(e) => setSuspectId(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Title</label>
                <Input
                  placeholder="Brief title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Description *</label>
                <textarea
                  placeholder="Describe your tip..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-slate-200 min-h-[120px]"
                  required
                />
              </div>
              <Button
                onClick={() => submit.mutate()}
                loading={submit.isPending}
                disabled={!description.trim()}
              >
                Submit tip
              </Button>
              {submit.isError && (
                <p className="text-sm text-red-400">{getApiErrorMessage(submit.error)}</p>
              )}
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
