import { useState, useRef } from 'react'
import { useEvidenceList } from '@/hooks/useEvidence'
import { useEvidenceCreate } from '@/hooks/useEvidence'
import { useCasesList } from '@/hooks/useCases'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { CardSkeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import { getApiErrorMessage } from '@/api/client'
import type { Evidence } from '@/types'
import type { Case } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

const EVIDENCE_TYPES = [
  { value: 'witness', label: 'Witness' },
  { value: 'biological', label: 'Biological' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'id_document', label: 'Identification Document' },
  { value: 'other', label: 'Other' },
] as const

export function DocumentsPage() {
  const [caseId, setCaseId] = useState<string>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [type, setType] = useState<string>('other')
  // Witness
  const [transcript, setTranscript] = useState('')
  const [witnessFiles, setWitnessFiles] = useState<{ file: File; mediaType: string }[]>([])
  const witnessFileRef = useRef<HTMLInputElement>(null)
  // Biological
  const [biologicalImages, setBiologicalImages] = useState<File[]>([])
  const biologicalImagesRef = useRef<HTMLInputElement>(null)
  // Vehicle
  const [vehicleModel, setVehicleModel] = useState('')
  const [vehicleColor, setVehicleColor] = useState('')
  const [licensePlate, setLicensePlate] = useState('')
  const [serialNumber, setSerialNumber] = useState('')
  // ID Document
  const [ownerFullName, setOwnerFullName] = useState('')
  const [attributesJson, setAttributesJson] = useState('{}')

  const { data: casesData } = useCasesList()
  const casesList = casesData ? ensureArray(casesData as Case[] | { results: Case[] }) : []
  const { data, isLoading, error } = useEvidenceList(caseId ? parseInt(caseId, 10) : null)
  const createEvidence = useEvidenceCreate()
  const list = data ? ensureArray(data as Evidence[] | { results: Evidence[] }) : []

  const resetForm = () => {
    setTitle('')
    setDescription('')
    setTranscript('')
    setWitnessFiles([])
    setBiologicalImages([])
    setVehicleModel('')
    setVehicleColor('')
    setLicensePlate('')
    setSerialNumber('')
    setOwnerFullName('')
    setAttributesJson('{}')
    setModalOpen(false)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!caseId || !title.trim()) return
    if (type === 'biological' && biologicalImages.length === 0) {
      return
    }
    if (type === 'vehicle') {
      const hasPlate = licensePlate.trim().length > 0
      const hasSerial = serialNumber.trim().length > 0
      if (hasPlate && hasSerial) return
      if (!hasPlate && !hasSerial) return
    }

    const payload = new FormData()
    payload.append('case', caseId)
    payload.append('evidence_type', type)
    payload.append('title', title.trim())
    payload.append('description', description)

    if (type === 'witness') {
      payload.append('transcript', transcript)
      witnessFiles.forEach(({ file, mediaType }, i) => {
        payload.append(`media_files_${i}`, file)
        payload.append(`media_files_${i}_type`, mediaType)
      })
    }
    if (type === 'biological') {
      biologicalImages.forEach((file) => payload.append('images', file))
    }
    if (type === 'vehicle') {
      payload.append('model', vehicleModel)
      payload.append('color', vehicleColor)
      payload.append('license_plate', licensePlate)
      payload.append('serial_number', serialNumber)
    }
    if (type === 'id_document') {
      payload.append('owner_full_name', ownerFullName)
      try {
        const attrs = attributesJson.trim() ? JSON.parse(attributesJson) : {}
        payload.append('attributes', JSON.stringify(attrs))
      } catch {
        payload.append('attributes', '{}')
      }
    }

    createEvidence.mutate(payload, { onSuccess: resetForm })
  }

  const addWitnessFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    const next: { file: File; mediaType: string }[] = [...witnessFiles]
    for (let i = 0; i < files.length; i++) {
      const f = files[i]
      const t = f.type
      const mediaType = t.startsWith('image/') ? 'image' : t.startsWith('video/') ? 'video' : 'audio'
      next.push({ file: f, mediaType })
    }
    setWitnessFiles(next)
    if (witnessFileRef.current) witnessFileRef.current.value = ''
  }

  const addBiologicalImages = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    setBiologicalImages((prev) => [...prev, ...Array.from(files)])
    if (biologicalImagesRef.current) biologicalImagesRef.current.value = ''
  }

  const vehicleValid = () => {
    const hasPlate = licensePlate.trim().length > 0
    const hasSerial = serialNumber.trim().length > 0
    return (hasPlate && !hasSerial) || (!hasPlate && hasSerial)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-100">Documents & Evidence</h1>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-400 whitespace-nowrap">Case</label>
            <select
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              className="rounded-lg bg-slate-800 border border-slate-600 text-slate-200 px-3 py-2 text-sm min-w-[200px]"
            >
              <option value="">— Select case —</option>
              {casesList.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  #{c.id} — {c.title}
                </option>
              ))}
            </select>
          </div>
          <Button onClick={() => setModalOpen(true)} disabled={!caseId}>Add evidence</Button>
        </div>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add evidence">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Case</label>
            <select
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              required
              className="w-full rounded-lg bg-slate-800 border border-slate-600 text-slate-200 px-4 py-2.5"
            >
              <option value="">— Select case —</option>
              {casesList.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  #{c.id} — {c.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Type</label>
            <select
              className="w-full rounded-lg bg-slate-800 border border-slate-600 text-slate-100 px-4 py-2.5"
              value={type}
              onChange={(e) => setType(e.target.value)}
            >
              {EVIDENCE_TYPES.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Title</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Description</label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>

          {type === 'witness' && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Transcript (optional)</label>
                <textarea
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  className="w-full rounded-lg bg-slate-800 border border-slate-600 text-slate-200 px-4 py-2.5 min-h-[80px]"
                  placeholder="Witness statement or transcript"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Media files (image / video / audio)</label>
                <input
                  ref={witnessFileRef}
                  type="file"
                  accept="image/*,video/*,audio/*"
                  multiple
                  onChange={addWitnessFiles}
                  className="block w-full text-sm text-slate-400 file:mr-4 file:rounded file:border-0 file:bg-primary-600 file:px-4 file:py-2 file:text-slate-100"
                />
                {witnessFiles.length > 0 && (
                  <ul className="mt-2 text-xs text-slate-500">
                    {witnessFiles.map((f, i) => (
                      <li key={i} className="flex items-center justify-between">
                        {f.file.name} ({f.mediaType})
                        <button
                          type="button"
                          onClick={() => setWitnessFiles((p) => p.filter((_, j) => j !== i))}
                          className="text-red-400 hover:underline"
                        >
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}

          {type === 'biological' && (
            <div>
              <label className="block text-sm text-slate-400 mb-1">Images (at least 1 required)</label>
              <input
                ref={biologicalImagesRef}
                type="file"
                accept="image/*"
                multiple
                onChange={addBiologicalImages}
                className="block w-full text-sm text-slate-400 file:mr-4 file:rounded file:border-0 file:bg-primary-600 file:px-4 file:py-2 file:text-slate-100"
              />
              {biologicalImages.length > 0 && (
                <ul className="mt-2 text-xs text-slate-500">
                  {biologicalImages.map((f, i) => (
                    <li key={i} className="flex items-center justify-between">
                      {f.name}
                      <button
                        type="button"
                        onClick={() => setBiologicalImages((p) => p.filter((_, j) => j !== i))}
                        className="text-red-400 hover:underline"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {biologicalImages.length === 0 && (
                <p className="text-amber-500 text-xs mt-1">Add at least one image.</p>
              )}
            </div>
          )}

          {type === 'vehicle' && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Model</label>
                <Input value={vehicleModel} onChange={(e) => setVehicleModel(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Color</label>
                <Input value={vehicleColor} onChange={(e) => setVehicleColor(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">License plate (optional if serial number set)</label>
                <Input value={licensePlate} onChange={(e) => setLicensePlate(e.target.value)} placeholder="e.g. ABC-123" />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Serial number (optional if license plate set)</label>
                <Input value={serialNumber} onChange={(e) => setSerialNumber(e.target.value)} />
              </div>
              {!vehicleValid() && (licensePlate.trim() || serialNumber.trim()) && (
                <p className="text-amber-500 text-xs">Provide exactly one of license plate or serial number.</p>
              )}
            </>
          )}

          {type === 'id_document' && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Owner full name</label>
                <Input value={ownerFullName} onChange={(e) => setOwnerFullName(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Attributes (JSON, optional)</label>
                <textarea
                  value={attributesJson}
                  onChange={(e) => setAttributesJson(e.target.value)}
                  className="w-full rounded-lg bg-slate-800 border border-slate-600 text-slate-200 px-4 py-2.5 font-mono text-sm min-h-[60px]"
                  placeholder='{"document_type": "national_id", "number": "..."}'
                />
              </div>
            </>
          )}

          {createEvidence.isError && (
            <p className="text-sm text-red-400">{getApiErrorMessage(createEvidence.error)}</p>
          )}
          <Button
            type="submit"
            loading={createEvidence.isPending}
            disabled={
              type === 'biological' && biologicalImages.length === 0
                ? true
                : type === 'vehicle' ? !vehicleValid() : false
            }
          >
            Save
          </Button>
        </form>
      </Modal>

      {error && <p className="text-red-400">Failed to load evidence.</p>}
      {!caseId && <Card><CardContent className="py-12 text-center text-slate-500">Select a case above to list evidence or add new evidence.</CardContent></Card>}
      {caseId && isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (<CardSkeleton key={i} />))}
        </div>
      )}
      {caseId && !isLoading && list.length === 0 && (
        <Card><CardContent className="py-12 text-center text-slate-500">No evidence for this case.</CardContent></Card>
      )}
      {caseId && !isLoading && list.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {list.map((e) => (
            <Card key={e.id}>
              <CardHeader>
                <CardTitle className="text-base truncate">{e.title}</CardTitle>
                <span className="text-xs text-slate-500">{e.evidence_type}</span>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-500 line-clamp-2">{e.description || '—'}</p>
                <p className="text-xs text-slate-600 mt-2">{formatDate(e.date_recorded ?? e.created_at)} · {e.recorder_username ?? '—'}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
