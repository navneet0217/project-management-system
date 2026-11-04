// The API sends UTC timestamps without a timezone suffix, which browsers would read as local time.
export function parseUtc(value: string): Date {
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`)
}

export const formatDateTime = (value: string) =>
  parseUtc(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export const formatDate = (value: string) => parseUtc(value).toLocaleDateString()
