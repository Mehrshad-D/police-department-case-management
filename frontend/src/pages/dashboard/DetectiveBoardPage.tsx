import { useState, useCallback, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
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

const CARD_WIDTH = 150
const CARD_HEIGHT = 90
const GRID_COLS = 4
const GRID_DX = 180
const GRID_DY = 120

export function DetectiveBoardPage() {
  const [searchParams] = useSearchParams()
  const caseIdParam = searchParams.get('caseId')
  const caseId = caseIdParam ? parseInt(caseIdParam, 10) : null
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(caseId)
  const [positions, setPositions] = useState<Record<number, { x: number; y: number }>>({})
  const [connectingFrom, setConnectingFrom] = useState<number | null>(null)
  const boardRef = useRef<HTMLDivElement>(null)
  const cardRefs = useRef<Record<number, HTMLDivElement | null>>({})
  /** During drag: { id, startPos, startClientX, startClientY } so we can compute position from pointer. */
  const dragRef = useRef<{ id: number; startPos: { x: number; y: number }; startClientX: number; startClientY: number } | null>(null)

  const { data: casesData } = useCasesList()
  const casesList = casesData ? ensureArray(casesData as { id: number; title: string }[] | { results: { id: number; title: string }[] }) : []

  const { data: evidenceData, isLoading: evidenceLoading } = useEvidenceList(selectedCaseId)
  const evidenceList = evidenceData ? ensureArray(evidenceData as Evidence[] | { results: Evidence[] }) : []

  const { data: linksData } = useEvidenceLinks(selectedCaseId)
  const links = linksData ? ensureArray(linksData as EvidenceLink[] | { results: EvidenceLink[] }) : []

  const createLink = useEvidenceLinkCreate(selectedCaseId ?? 0)

  // Initialize positions by list index when evidence loads; keep existing when list same
  useEffect(() => {
    if (!evidenceList.length) return
    setPositions((prev) => {
      const next: Record<number, { x: number; y: number }> = {}
      evidenceList.forEach((ev, i) => {
        if (prev[ev.id]) {
          next[ev.id] = prev[ev.id]
        } else {
          next[ev.id] = {
            x: 80 + (i % GRID_COLS) * GRID_DX,
            y: 80 + Math.floor(i / GRID_COLS) * GRID_DY,
          }
        }
      })
      return next
    })
  }, [selectedCaseId, evidenceList.length])

  useEffect(() => {
    if (selectedCaseId && !caseIdParam) setSelectedCaseId(selectedCaseId)
  }, [selectedCaseId, caseIdParam])

  const getPos = useCallback((id: number) => {
    return positions[id] ?? { x: 80, y: 80 }
  }, [positions])

  const setPos = useCallback((id: number, x: number, y: number) => {
    setPositions((p) => ({ ...p, [id]: { x, y } }))
  }, [])

  const handlePointerDown = useCallback(
    (evId: number, e: React.PointerEvent) => {
      e.preventDefault()
      if (e.button !== 0) return
      const pos = getPos(evId)
      dragRef.current = { id: evId, startPos: { x: pos.x, y: pos.y }, startClientX: e.clientX, startClientY: e.clientY }
      ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
    },
    [getPos]
  )
  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    const d = dragRef.current
    if (!d) return
    const newX = d.startPos.x + (e.clientX - d.startClientX)
    const newY = d.startPos.y + (e.clientY - d.startClientY)
    setPositions((p) => ({ ...p, [d.id]: { x: Math.max(0, newX), y: Math.max(0, newY) } }))
  }, [])
  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (dragRef.current) (e.target as HTMLElement).releasePointerCapture?.(e.pointerId)
    dragRef.current = null
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
    createLink.mutate({ evidence_from: fromId, evidence_to: toId, link_type: 'red' })
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
            <div
              ref={boardRef}
              className="relative bg-slate-900/50 rounded-b-xl overflow-visible"
              style={{ width: '100%', minWidth: 800, minHeight: 520 }}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerLeave={handlePointerUp}
            >
              {/* Red connection lines: same coordinate system as cards (absolute px). Lines update as cards move. */}
              <svg
                className="absolute top-0 left-0 pointer-events-none overflow-visible"
                style={{ zIndex: 0, width: '100%', height: '100%', minHeight: 520 }}
              >
                <defs>
                  <marker id="arrowhead-red" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#ef4444" />
                  </marker>
                </defs>
                {links.map((link) => {
                  const from = getPos(link.evidence_from)
                  const to = getPos(link.evidence_to)
                  const x1 = from.x + CARD_WIDTH / 2
                  const y1 = from.y + CARD_HEIGHT / 2
                  const x2 = to.x + CARD_WIDTH / 2
                  const y2 = to.y + CARD_HEIGHT / 2
                  return (
                    <line
                      key={link.id}
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="#ef4444"
                      strokeWidth={2}
                      markerEnd="url(#arrowhead-red)"
                    />
                  )
                })}
              </svg>

              {evidenceList.map((ev) => {
                const pos = getPos(ev.id)
                return (
                  <div
                    key={ev.id}
                    ref={(el) => { cardRefs.current[ev.id] = el }}
                    onPointerDown={(e) => handlePointerDown(ev.id, e)}
                    style={{
                      position: 'absolute',
                      left: pos.x,
                      top: pos.y,
                      width: CARD_WIDTH,
                      minHeight: CARD_HEIGHT,
                      zIndex: 10,
                    }}
                    className="cursor-grab active:cursor-grabbing"
                  >
                    <Card
                      className={`p-3 select-none h-full ${connectingFrom === ev.id ? 'ring-2 ring-red-500' : ''}`}
                      onDoubleClick={(e) => {
                        e.preventDefault()
                        if (connectingFrom) handleConnect(connectingFrom, ev.id)
                        else setConnectingFrom(ev.id)
                      }}
                    >
                      <p className="text-xs text-slate-500 truncate">{ev.evidence_type}</p>
                      <p className="text-sm font-medium text-slate-100 truncate">{ev.title}</p>
                      {connectingFrom === ev.id && (
                        <p className="text-xs text-red-400 mt-1">Double-click another card to connect (red line)</p>
                      )}
                    </Card>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
