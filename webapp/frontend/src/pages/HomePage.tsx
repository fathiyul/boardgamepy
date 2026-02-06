import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { GameMeta } from '../types';

const fetchGames = async (): Promise<GameMeta[]> => {
  const res = await api.get('/games');
  return res.data;
};

export default function HomePage() {
  const { data, isLoading, error } = useQuery({ queryKey: ['games'], queryFn: fetchGames });

  return (
      <div className="container">
      <h1>BoardGamePy Web</h1>
      {isLoading && <p>Loading games…</p>}
      {error && <p>Failed to load games.</p>}
      <div className="card-grid">
        {data?.map((game) => (
          <Link to={`/${game.slug}`} key={game.slug} className="card">
            <div className="flex" style={{ justifyContent: 'space-between' }}>
              <h3>{game.title}</h3>
              {!game.playable && <span className="badge">Soon</span>}
            </div>
            <p>{game.description}</p>
            <p style={{ fontSize: 12, color: '#475569' }}>
              {game.min_players === game.max_players
                ? `${game.min_players} players`
                : `${game.min_players}-${game.max_players} players`}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
