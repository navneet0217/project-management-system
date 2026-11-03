import { useEffect, useRef, useState } from 'react'
import { Input } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useDebouncedValue } from '../hooks/useDebouncedValue'

// Search box that filters while you type (debounced); no need to press Enter.
export default function SearchInput({
  placeholder,
  onSearch,
  width = 260,
}: {
  placeholder: string
  onSearch: (value: string) => void
  width?: number
}) {
  const [text, setText] = useState('')
  const debounced = useDebouncedValue(text.trim())
  const last = useRef('')

  useEffect(() => {
    // only report real changes, so the first render does not trigger a reload
    if (debounced !== last.current) {
      last.current = debounced
      onSearch(debounced)
    }
  }, [debounced, onSearch])

  return (
    <Input
      allowClear
      value={text}
      onChange={(e) => setText(e.target.value)}
      onPressEnter={() => onSearch(text.trim())}
      prefix={<SearchOutlined />}
      placeholder={placeholder}
      style={{ width }}
    />
  )
}
