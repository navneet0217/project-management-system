import { useSearchParams } from 'react-router-dom'
import { tasksApi } from '../api/tasks'
import { PageHeaderRow } from '../components/PageHeaderRow'
import TasksTable from '../components/TasksTable'
import { taskTableInitial } from '../lib/taskParams'

const fetcher = tasksApi.list

// All tasks the signed-in user can see (admin: everything, manager: own projects).
export default function Tasks() {
  const [params] = useSearchParams()
  return (
    <>
      <PageHeaderRow title="All tasks" />
      <TasksTable fetcher={fetcher} initial={taskTableInitial(params)} />
    </>
  )
}
