export async function api<T>(path:string, options?:RequestInit):Promise<T> {
  const response = await fetch('/api/v1'+path, { ...options, headers: {'Content-Type':'application/json',...options?.headers} })
  const body = await response.json()
  if (!response.ok) throw new Error(body.error?.code || 'REQUEST_FAILED')
  return body as T
}
