import os
import requests
from typing import List, Dict

class TMDbService:
    def __init__(self):
        self.api_key = os.environ.get('TMDB_API_KEY')
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = 'https://image.tmdb.org/t/p/w500'
    
    def search_movies(self, query: str) -> List[Dict]:
        if not self.api_key:
            return self._get_mock_movies(query)
        
        try:
            url = f"{self.base_url}/search/movie"
            params = {
                'api_key': self.api_key,
                'query': query,
                'language': 'pt-BR'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            movies = []
            
            for movie in data.get('results', [])[:10]:  # Limitar a 10 resultados
                movies.append({
                    'id': str(movie['id']),
                    'title': movie.get('title', ''),
                    'type': 'movie',
                    'poster_url': f"{self.image_base_url}{movie['poster_path']}" if movie.get('poster_path') else None,
                    'rating': movie.get('vote_average', 0),
                    'release_date': movie.get('release_date', ''),
                    'genres': self._get_genre_names(movie.get('genre_ids', [])),
                    'description': movie.get('overview', '')
                })
            
            return movies
            
        except Exception as e:
            print(f"Erro ao buscar filmes no TMDb: {e}")
            return self._get_mock_movies(query)
    
    def search_tv_shows(self, query: str) -> List[Dict]:
        if not self.api_key:
            return self._get_mock_tv_shows(query)
        
        try:
            url = f"{self.base_url}/search/tv"
            params = {
                'api_key': self.api_key,
                'query': query,
                'language': 'pt-BR'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            tv_shows = []
            
            for show in data.get('results', [])[:10]:  # Limitar a 10 resultados
                tv_shows.append({
                    'id': str(show['id']),
                    'title': show.get('name', ''),
                    'type': 'tv',
                    'poster_url': f"{self.image_base_url}{show['poster_path']}" if show.get('poster_path') else None,
                    'rating': show.get('vote_average', 0),
                    'release_date': show.get('first_air_date', ''),
                    'genres': self._get_genre_names(show.get('genre_ids', [])),
                    'description': show.get('overview', '')
                })
            
            return tv_shows
            
        except Exception as e:
            print(f"Erro ao buscar séries no TMDb: {e}")
            return self._get_mock_tv_shows(query)
    
    def _get_genre_names(self, genre_ids: List[int]) -> List[str]:
        # Mapeamento básico de gêneros do TMDb
        genre_map = {
            28: 'Ação', 12: 'Aventura', 16: 'Animação', 35: 'Comédia',
            80: 'Crime', 99: 'Documentário', 18: 'Drama', 10751: 'Família',
            14: 'Fantasia', 36: 'História', 27: 'Terror', 10402: 'Música',
            9648: 'Mistério', 10749: 'Romance', 878: 'Ficção Científica',
            10770: 'Filme para TV', 53: 'Thriller', 10752: 'Guerra', 37: 'Faroeste'
        }
        
        return [genre_map.get(genre_id, 'Desconhecido') for genre_id in genre_ids]
    
    def _get_mock_movies(self, query: str) -> List[Dict]:
        return [
            {
                'id': 'mock_movie_1',
                'title': f'Filme Mock: {query}',
                'type': 'movie',
                'poster_url': 'https://via.placeholder.com/300x450/8B5CF6/FFFFFF?text=Mock+Movie',
                'rating': 8.5,
                'release_date': '2023',
                'genres': ['Ação', 'Aventura'],
                'description': f'Este é um filme mock para a busca "{query}". Dados reais virão da API TMDb.'
            }
        ]
    
    def _get_mock_tv_shows(self, query: str) -> List[Dict]:
        return [
            {
                'id': 'mock_tv_1',
                'title': f'Série Mock: {query}',
                'type': 'tv',
                'poster_url': 'https://via.placeholder.com/300x450/F59E0B/FFFFFF?text=Mock+TV',
                'rating': 9.0,
                'release_date': '2023',
                'genres': ['Drama', 'Thriller'],
                'description': f'Esta é uma série mock para a busca "{query}". Dados reais virão da API TMDb.'
            }
        ]

