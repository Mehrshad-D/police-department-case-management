import { useState, useCallback, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import html2canvas from 'html2canvas'
import { useCasesList } from '@/hooks/useCases'
import { useEvidenceList, useEvidenceLinks, useEvidenceLinkCreate } from '@/hooks/useEvidence'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import type { Evidence } from '@/types'
import type { EvidenceLink } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

interface CardPosition {
  id: number
  x: number
  y: number
}

export function DetectiveBoardPage() {
  const [searchParams] = useSearchParams()
  const caseIdParam = searchParams.get('caseId')
  const caseId = caseIdParam ? parseInt(caseIdParam, 10) : null
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(caseId)
  const [positions, setPositions] = useState<Record<number, CardPosition>>({})
  const [connectingFrom, setConnectingFrom] = useState<number | null>(null)
  const boardRef = useRef<HTMLDivElement>(null)

  const { data: casesData } = useCasesList()
  const casesList = casesData ? ensureArray(casesData as { id: number; title: string }[] | { results: { id: number; title: string }[] }) : []

  const { data: evidenceData, isLoading: evidenceLoading } = useEvidenceList(selectedCaseId)
  const evidenceList = evidenceData ? ensureArray(evidenceData as Evidence[] | { results: Evidence[] }) : []

  const { data: linksData } = useEvidenceLinks(selectedCaseId)
  const links = linksData ? ensureArray(linksData as EvidenceLink[] | { results: EvidenceLink[] }) : []

  const createLink = useEvidenceLinkCreate(selectedCaseId ?? 0)

  useEffect(() => {
    if (selectedCaseId && !caseIdParam) setSelectedCaseId(selectedCaseId)
  }, [selectedCaseId, caseIdParam])

  const getPos = (id: number) => positions[id] ?? { x: 100 + (id % 5) * 180, y: 100 + Math.floor(id / 5) * 120 }
  const setPos = useCallback((id: number, x: number, y: number) => {
    setPositions((p) => ({ ...p, [id]: { id, x, y } }))
  }, [])

  const handleExportImage = async () => {
    if (!boardRef.current) return
    const canvas = await html2canvas(boardRef.current, { backgroundColor: '#0f172a', scale: 2 })
    const link = document.createElement('a')
    link.download = `board-case-${selectedCaseId ?? 'all'}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  }

  const handleConnect = (fromId: number, toId: number) => {
    if (fromId === toId || !selectedCaseId) return
    const exists = links.some((l) => (l.evidence_from === fromId && l.evidence_to === toId) || (l.evidence_from === toId && l.evidence_to === fromId))
    if (exists) return
    createLink.mutate({ evidence_from: fromId, evidence_to: toId, link_type: 'related' })
    setConnectingFrom(null)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-100">Detective Board</h1>
        <div className="flex items-center gap-2">
          <select
            className="rounded-lg bg-slate-800 border border-slate-600 text-slate-100 px-3 py-2 text-sm"
            value={selectedCaseId ?? ''}
            onChange={(e) => setSelectedCaseId(e.target.value ? parseInt(e.target.value, 10) : null)}
          >
            <option value="">Select case</option>
            {casesList.map((c) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
          <Button variant="secondary" size="sm" onClick={handleExportImage}>
            Export as image
          </Button>
        </div>
      </div>

      {!selectedCaseId && (
        <Card><CardContent className="py-12 text-center text-slate-500">Select a case to view the evidence board.</CardContent></Card>
      )}

      {selectedCaseId && evidenceLoading && (
        <Card><CardContent className="py-12 text-center text-slate-500">Loading evidence...</CardContent></Card>
      )}

      {selectedCaseId && !evidenceLoading && (
        <Card>
          <CardContent className="p-0 overflow-hidden">
            <div ref={boardRef} className="relative min-h-[500px] bg-slate-900/50 rounded-b-xl">
              {/* SVG lines */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ overflow: 'visible' }}>
                {links.map((link) => {
                  const from = getPos(link.evidence_from)
                  const to = getPos(link.evidence_to)
                  return (
                    <line
                      key={link.id}
                      x1={from.x + 75}
                      y1={from.y + 40}
                      x2={to.x + 75}
                      y2={to.y + 40}
                      stroke="rgba(59, 130, 246, 0.6)"
                      strokeWidth={2}
                      markerEnd="url(#arrowhead)"
                    />
                  )
                })}
                <defs>
                  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="rgba(59, 130, 246, 0.8)" />
                  </marker>
                </defs>
              </svg>

              {evidenceList.map((ev) => {
                const pos = getPos(ev.id)
                return (
                  <motion.div
                    key={ev.id}
                    drag
                    dragMomentum={false}
                    onDragEnd={(_, info) => setPos(ev.id, pos.x + info.delta.x, pos.y + info.delta.y)}
                    style={{ left: pos.x, top: pos.y }}
                    className="absolute w-[150px] cursor-grab active:cursor-grabbing z-10"
                  >
                    <Card
                      className={`p-3 select-none ${connectingFrom === ev.id ? 'ring-2 ring-primary-500' : ''}`}
                      onDoubleClick={() => {
                        if (connectingFrom) handleConnect(connectingFrom, ev.id)
                        else setConnectingFrom(ev.id)
                      }}
                    >
                      <p className="text-xs text-slate-500 truncate">{ev.evidence_type}</p>
                      <p className="text-sm font-medium text-slate-100 truncate">{ev.title}</p>
                      {connectingFrom === ev.id && (
                        <p className="text-xs text-primary-400 mt-1">Double-click another card to connect</p>
                      )}
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
