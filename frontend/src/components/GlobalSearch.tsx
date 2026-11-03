import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AutoComplete, Input, Spin, Tag, type InputRef } from 'antd'
import { SearchOutlined, UserOutlined } from '@ant-design/icons'
import { projectsApi } from '../api/projects'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { label } from '../lib/options'
import type { Project } from '../types'

const MIN_CHARS = 2

function ResultRow({ project }: { project: Project }) {
  return (
    <div className="gs-row">
      <div className="gs-row-main">
        <span className="gs-name">{project.name}</span>
        <Tag style={{ marginInlineEnd: 0 }}>{label(project.status)}</Tag>
      </div>
      <div className="gs-row-sub">
        {project.manager && (
          <span>
            <UserOutlined /> {project.manager.full_name}
          </span>
        )}
        {project.description && <span className="gs-desc">{project.description}</span>}
      </div>
    </div>
  )
}

// Header search: finds projects by name, manager or description as you type, and opens the one you pick.
export default function GlobalSearch() {
  const navigate = useNavigate()
  const inputRef = useRef<InputRef>(null)
  const [text, setText] = useState('')
  const [results, setResults] = useState<Project[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const query = useDebouncedValue(text.trim(), 300)

  useEffect(() => {
    if (query.length < MIN_CHARS) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setResults([])
      setSearched(false)
      return
    }
    let stale = false // ignore a slow response if the user has already typed something else
    setLoading(true)
    projectsApi
      .list({ search: query, size: 8 })
      .then((page) => {
        if (!stale) {
          setResults(page.items)
          setSearched(true)
        }
      })
      .catch(() => {
        if (!stale) setResults([])
      })
      .finally(() => {
        if (!stale) setLoading(false)
      })
    return () => {
      stale = true
    }
  }, [query])

  // Ctrl+K (or Cmd+K) focuses the search from anywhere
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const options = results.map((p) => ({ value: String(p.id), label: <ResultRow project={p} /> }))

  const onSelect = (id: string) => {
    setText('')
    setResults([])
    setSearched(false)
    inputRef.current?.blur()
    navigate(`/projects/${id}`)
  }

  const typedEnough = text.trim().length >= MIN_CHARS
  // below the minimum length there is nothing to show, so the dropdown stays closed
  const empty = !typedEnough ? null : loading ? (
    <Spin size="small" />
  ) : searched ? (
    'No matching projects'
  ) : null

  return (
    <AutoComplete
      className="global-search"
      value={text}
      options={options}
      onChange={setText}
      onSelect={onSelect}
      filterOption={false}
      popupMatchSelectWidth={440}
      notFoundContent={empty ? <div style={{ padding: 8, textAlign: 'center' }}>{empty}</div> : null}
    >
      <Input
        ref={inputRef}
        allowClear
        prefix={<SearchOutlined />}
        placeholder="Search projects, managers, descriptions…"
      />
    </AutoComplete>
  )
}
