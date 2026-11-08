import { Empty, Timeline, Typography } from 'antd'
import { ArrowRightOutlined } from '@ant-design/icons'
import { ACTION_COLORS, describeActivity } from '../../../lib/activity'
import { formatDateTime } from '../../../lib/dates'
import type { ProjectActivity } from '../../../types'

// Timeline of audit entries, newest first (the API already returns them in that order).
export default function ActivityTimeline({
  items,
  showProject = false,
}: {
  items: ProjectActivity[]
  showProject?: boolean
}) {
  if (items.length === 0) return <Empty description="No activity yet" />

  return (
    <Timeline
      className="activity-timeline"
      items={items.map((a) => {
        const view = describeActivity(a)
        return {
          color: ACTION_COLORS[a.action],
          content: (
            <div className="activity-entry">
              <div>
                <strong>{a.actor?.full_name ?? 'Someone'}</strong> {view.summary}
                {showProject && a.project_name && (
                  <Typography.Text type="secondary"> · {a.project_name}</Typography.Text>
                )}
              </div>
              {view.hasChange && (
                <div className="activity-change">
                  <span>{view.from ?? '—'}</span>
                  <ArrowRightOutlined />
                  <span>{view.to ?? '—'}</span>
                </div>
              )}
              {view.quote && <div className="activity-quote">{view.quote}</div>}
              <Typography.Text type="secondary" className="activity-time">
                {formatDateTime(a.created_at)}
              </Typography.Text>
            </div>
          ),
        }
      })}
    />
  )
}
