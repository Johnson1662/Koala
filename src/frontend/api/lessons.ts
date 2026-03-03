import request from './client'

export interface LessonStep {
  step_id: number
  type: 'text' | 'image' | 'svg' | 'question-choice' | 'question-fill' | 'question-open'
  content: string
  options?: string[]
  answer?: string
  explanation?: string
  source?: string
}

export interface Lesson {
  lesson_id: string
  course_id: string
  title: string
  steps: LessonStep[]
}

export interface AnswerResult {
  correct: boolean
  xp_delta: number
  explanation: string
}

export function generateLesson(courseId: string, title: string): Promise<Lesson> {
  return request<Lesson>('/lessons/generate', {
    method: 'POST',
    body: JSON.stringify({ course_id: courseId, title }),
  })
}

export function submitAnswer(lessonId: string, stepId: number, answer: string): Promise<AnswerResult> {
  return request<AnswerResult>(`/lessons/${lessonId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ step_id: stepId, answer }),
  })
}

export function submitFeedback(lessonId: string, feedback: string): Promise<void> {
  return request<void>(`/lessons/${lessonId}/feedback`, {
    method: 'POST',
    body: JSON.stringify({ feedback }),
  })
}
