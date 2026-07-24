import { useEffect, useState } from 'react';

import { loadDataset } from '../lib/data';
import type { Dataset } from '../types';

type State =
  { status: 'loading' } | { status: 'error'; error: string } | { status: 'ready'; data: Dataset };

export function useDataset(): State {
  const [state, setState] = useState<State>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    loadDataset()
      .then((data) => {
        if (!cancelled) setState({ status: 'ready', data });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: 'error',
            error: error instanceof Error ? error.message : 'Unknown error loading data.',
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
