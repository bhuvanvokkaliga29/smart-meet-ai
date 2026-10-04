import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App Component', () => {
  it('renders the application correctly', () => {
    render(<App />);
    const dashboardElements = screen.getAllByText(/SmartMeet AI/i);
    expect(dashboardElements.length).toBeGreaterThan(0);
  });
});
