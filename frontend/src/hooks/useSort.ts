import { useCallback, useState } from 'react'
import type { SorterResult } from 'antd/es/table/interface'

export interface Sort<F extends string> {
  field: F
  order: 'asc' | 'desc'
}

// Reusable server-side table sorting. Spread `sortProps('title')` into a column to make it sortable.
export function useSort<F extends string>(fields: readonly F[], initial: Sort<F>) {
  const [sort, setSort] = useState<Sort<F>>(initial)

  const sortProps = useCallback(
    (field: F) => ({
      sorter: true as const,
      sortOrder: sort.field === field ? (sort.order === 'asc' ? ('ascend' as const) : ('descend' as const)) : null,
    }),
    [sort],
  )

  // Call from the table's onChange. Clearing the sort falls back to the initial one.
  const onTableChange = useCallback(
    (sorter: SorterResult<never> | SorterResult<never>[]) => {
      const s = Array.isArray(sorter) ? sorter[0] : sorter
      const field = s?.field as F | undefined
      if (s?.order && field && fields.includes(field)) {
        setSort({ field, order: s.order === 'ascend' ? 'asc' : 'desc' })
      } else {
        setSort(initial)
      }
    },
    // `initial` and `fields` are stable constants at the call sites
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )

  return { sort, sortProps, onTableChange }
}
