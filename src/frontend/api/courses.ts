import request from './client'

export interface Course {
  course_id: string
  user_id: string
  topic: string
  outline: OutlineChapter[]
  created_at: string
}

export interface OutlineChapter {
  chapter: string
  lessons: OutlineLesson[]
}

export interface OutlineLesson {
  lesson_id: string
  title: string
}

export function listCourses(): Promise<Course[]> {
  return request<Course[]>('/courses')
}

export function getCourse(id: string): Promise<Course> {
  return request<Course>(`/courses/${id}`)
}

export function createCourse(topic: string): Promise<Course> {
  return request<Course>('/courses', {
    method: 'POST',
    body: JSON.stringify({ topic }),
  })
}

export function deleteCourse(id: string): Promise<void> {
  return request<void>(`/courses/${id}`, { method: 'DELETE' })
}

export function generateOutline(courseId: string): Promise<Course> {
  return request<Course>(`/courses/${courseId}/outline`, { method: 'POST' })
}
