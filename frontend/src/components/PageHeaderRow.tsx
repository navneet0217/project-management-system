import { Space, Typography } from 'antd'

export function PageHeaderRow({ title, extra }: { title: string; extra?: React.ReactNode }) {
  return (
    <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }} wrap>
      <Typography.Title level={3} style={{ margin: 0 }}>
        {title}
      </Typography.Title>
      {extra}
    </Space>
  )
}
