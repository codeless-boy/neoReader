import api from './index'

export interface Book {
  id: number
  title: string
  author?: string
  path: string
  file_size: number
  encoding?: string
  added_at: string
  cover_path?: string
  description?: string
}

export interface Chapter {
  id: number
  book_id: number
  title: string
  start_offset: number
  end_offset?: number
  ordering: number
}

export const getBooks = (skip = 0, limit = 100) => {
  return api.get<Book[]>('/books/', { params: { skip, limit } })
}

export const getBook = (id: number) => {
  return api.get<Book>(`/books/${id}`)
}

export const uploadBook = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post<Book>('/books/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const deleteBook = (id: number) => {
  return api.delete(`/books/${id}`)
}

export const getBookContent = (id: number, start = 0, limit = 10000) => {
  return api.get<{ content: string; has_more: boolean; total_size: number; encoding: string }>(
    `/reader/${id}/content`,
    { params: { start, limit } }
  )
}

export const getChapters = (id: number) => {
  return api.get<Chapter[]>(`/books/${id}/chapters`)
}
