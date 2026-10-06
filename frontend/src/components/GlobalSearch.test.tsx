import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { GlobalSearch } from './GlobalSearch';
import { searchApi } from '../lib/searchApi';
import { SearchResultItem } from '../types/search';

vi.mock('../lib/searchApi', () => ({
  searchApi: { globalSearch: vi.fn() }
}));

const item = (over: Partial<SearchResultItem>): SearchResultItem => ({
  entity_type: 'PROJECT',
  entity_id: 'e1',
  title: 'Apollo',
  snippet: 'The Apollo project',
  url: '/projects/e1',
  score: 3.0,
  matched_field: 'name',
  ...over
});

function renderSearch() {
  return render(
    <MemoryRouter>
      <GlobalSearch />
    </MemoryRouter>
  );
}

async function openAndType(query: string) {
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
  const input = await screen.findByPlaceholderText(/Search projects, tasks/i);
  fireEvent.change(input, { target: { value: query } });
  return input;
}

describe('GlobalSearch command center', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('opens with Ctrl+K and focuses the input', async () => {
    renderSearch();
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    const input = await screen.findByPlaceholderText(/Search projects, tasks/i);
    expect(input).toHaveFocus();
  });

  it('shows loading state then results', async () => {
    (searchApi.globalSearch as any).mockImplementation(
      () => new Promise(res => setTimeout(() => res([item({})]), 50))
    );
    renderSearch();
    const input = await openAndType('apollo');

    expect(await screen.findByRole('status')).toHaveTextContent('Searching…');
    expect(input).toBeInTheDocument();
    expect(await screen.findByText('Apollo')).toBeInTheDocument();
  });

  it('renders grouped results by entity type', async () => {
    (searchApi.globalSearch as any).mockResolvedValue([
      item({}),
      item({ entity_type: 'TASK', entity_id: 't1', title: 'Apollo task', url: '/projects/p/tasks/t1' })
    ]);
    renderSearch();
    await openAndType('apollo');
    expect(await screen.findByText('Apollo')).toBeInTheDocument();
    expect(screen.getByText('PROJECT')).toBeInTheDocument();
    expect(screen.getByText('TASK')).toBeInTheDocument();
  });

  it('shows the empty state for no results', async () => {
    (searchApi.globalSearch as any).mockResolvedValue([]);
    renderSearch();
    await openAndType('nothingmatches');
    expect(await screen.findByText(/No results found for/i)).toBeInTheDocument();
  });

  it('shows the error state on request failure', async () => {
    (searchApi.globalSearch as any).mockRejectedValue(new Error('boom'));
    renderSearch();
    await openAndType('errorcase');
    expect(await screen.findByText(/Search is temporarily unavailable/i)).toBeInTheDocument();
  });

  it('does not search for short queries', async () => {
    renderSearch();
    await openAndType('a');
    expect(screen.getByText('Commands')).toBeInTheDocument();
    expect(searchApi.globalSearch).not.toHaveBeenCalled();
  });

  it('navigates with keyboard and opens on Enter', async () => {
    (searchApi.globalSearch as any).mockResolvedValue([item({})]);
    renderSearch();
    const input = await openAndType('apollo');
    await screen.findByText('Apollo');

    // Arrow down moves the active row onto the result; Enter opens it.
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() =>
      expect(screen.queryByPlaceholderText(/Search projects, tasks/i)).not.toBeInTheDocument()
    );
  });

  it('closes on Escape', async () => {
    renderSearch();
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    expect(await screen.findByPlaceholderText(/Search projects, tasks/i)).toBeInTheDocument();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByPlaceholderText(/Search projects, tasks/i)).not.toBeInTheDocument();
  });

  it('opens a result with mouse click', async () => {
    (searchApi.globalSearch as any).mockResolvedValue([item({})]);
    renderSearch();
    await openAndType('apollo');
    fireEvent.click(await screen.findByText('Apollo'));
    await waitFor(() =>
      expect(screen.queryByPlaceholderText(/Search projects, tasks/i)).not.toBeInTheDocument()
    );
  });

  it('closes with the ESC button', async () => {
    renderSearch();
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    fireEvent.click(await screen.findByText('ESC'));
    expect(screen.queryByPlaceholderText(/Search projects, tasks/i)).not.toBeInTheDocument();
  });
});
