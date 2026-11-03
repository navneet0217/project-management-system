import { Tag } from 'antd'
import { TAG_COLORS, label } from '../lib/options'

export function StatusTag({ value }: { value: string }) {
  return <Tag color={TAG_COLORS[value]}>{label(value)}</Tag>
}
