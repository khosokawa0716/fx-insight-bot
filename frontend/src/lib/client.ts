const API_BASE_URL = ''

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async fetch<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body } = options

    const config: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    }

    if (body) {
      config.body = JSON.stringify(body)
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config)

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }
}

export const apiClient = new ApiClient()
