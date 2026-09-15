import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./api', () => ({
  api: {
    personas: vi.fn().mockResolvedValue([
      {
        email: 'patient@demo.matchcare.local',
        password: 'demo1234',
        role: 'patient',
        display_name: 'Ava Chen',
        org_slug: 'bayview',
        org_name: 'Bayview Health Network',
      },
    ]),
  },
  ApiError: class extends Error {
    status: number
    constructor(status: number, message: string) {
      super(message)
      this.status = status
    }
  },
}))

describe('App login shell', () => {
  it('renders the demo login shell', async () => {
    render(<App />)
    expect(await screen.findByText(/Demo login/i)).toBeInTheDocument()
    expect(screen.getByText(/generated seed data/i)).toBeInTheDocument()
    expect(await screen.findByText(/Continue as Ava Chen/i)).toBeInTheDocument()
  })
})
