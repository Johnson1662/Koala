import request from './client'

export interface UploadResult {
  course_id: string
  status: 'processing' | 'ready'
}

export function uploadPdf(courseId: string, file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('course_id', courseId)
  return request<UploadResult>('/rag/upload', { method: 'POST', body: form, headers: {} })
}

export function uploadUrl(courseId: string, url: string): Promise<UploadResult> {
  return request<UploadResult>('/rag/upload', {
    method: 'POST',
    body: JSON.stringify({ course_id: courseId, url }),
  })
}

export function getRagStatus(courseId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/rag/status/${courseId}`)
}
