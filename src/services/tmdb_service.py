import os
import requests
from typing import List, Dict, Optional

class TMDbService:
    def __init__(self):
        self.api_key = os.environ.get('TMDB_API_KEY')
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = 'https://image.tmdb.org/t/p/w500'
        
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Fazer requisição para a API do TMDb"""
        if not self.api_key:
            # Retornar dados mock se não tiver API key
            return self._get_mock_data(endpoint)
        
        try:
            url = f"{self.base_url}/{endpoint}"
            
            default_params = {'api_key': self.api_key, 'language': 'pt-BR'}
            if params:
                default_params.update(params)
            
            response = requests.get(url, params=default_params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            print(f"Erro na requisição TMDb: {e}")
            return self._get_mock_data(endpoint)
    
    def _get_mock_data(self, endpoint: str) -> dict:
        """Retornar dados mock para desenvolvimento"""
        if 'search/movie' in endpoint:
            return {
                'results': [
                    {
                        'id': 550,
                        'title': 'Clube da Luta',
                        'overview': 'Um funcionário de escritório insone e um fabricante de sabão formam um clube de luta subterrâneo.',
                        'poster_path': '/bptfVGEQuv6vDTIMVCHjJ9Dz8PX.jpg',
                        'release_date': '1999-10-15',
                        'vote_average': 8.4,
                        'genre_ids': [18, 53]
                    },
                    {
                        'id': 13,
                        'title': 'Forrest Gump',
                        'overview': 'A história de um homem simples com um coração grande.',
                        'poster_path': '/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg',
                        'release_date': '1994-07-06',
                        'vote_average': 8.5,
                        'genre_ids': [18, 35]
                    }
                ]
            }
        elif 'search/tv' in endpoint:
            return {
                'results': [
                    {
                        'id': 1399,
                        'name': 'Game of Thrones',
                        'overview': 'Nove famílias nobres lutam pelo controle das terras míticas de Westeros.',
                        'poster_path': '/u3bZgnGQ9T01sWNhyveQz0wH0Hl.jpg',
                        'first_air_date': '2011-04-17',
                        'vote_average': 8.3,
                        'genre_ids': [18, 10765]
                    }
                ]
            }
        elif 'trending' in endpoint:
            return {
                'results': [
                    {
                        'id': 872585,
                        'title': 'Oppenheimer',
                        'overview': 'A história de J. Robert Oppenheimer e seu papel no desenvolvimento da bomba atômica.',
                        'poster_path': '/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg',
                        'release_date': '2023-07-21',
                        'vote_average': 8.2,
                        'media_type': 'movie'
                    }
                ]
            }
        
        return {'results': []}
    
    def _format_movie(self, movie_data: dict) -> dict:
        """Formatar dados do filme"""
        return {
            'id': str(movie_data.get('id')),
            'title': movie_data.get('title'),
            'type': 'movie',
            'overview': movie_data.get('overview'),
            'poster_url': f"{self.image_base_url}{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None,
            'release_date': movie_data.get('release_date'),
            'rating': movie_data.get('vote_average'),
            'genre_ids': movie_data.get('genre_ids', [])
        }
    
    def _format_tv_show(self, tv_data: dict) -> dict:
        """Formatar dados da série"""
        return {
            'id': str(tv_data.get('id')),
            'title': tv_data.get('name'),
            'type': 'tv',
            'overview': tv_data.get('overview'),
            'poster_url': f"{self.image_base_url}{tv_data.get('poster_path')}" if tv_data.get('poster_path') else None,
            'release_date': tv_data.get('first_air_date'),
            'rating': tv_data.get('vote_average'),
            'genre_ids': tv_data.get('genre_ids', [])
        }
    
    def search_movies(self, query: str) -> List[dict]:
        """Buscar filmes"""
        data = self._make_request('search/movie', {'query': query})
        
        if not data or 'results' not in data:
            return []
        
        return [self._format_movie(movie) for movie in data['results'][:10]]
    
    def search_tv_shows(self, query: str) -> List[dict]:
        """Buscar séries"""
        data = self._make_request('search/tv', {'query': query})
        
        if not data or 'results' not in data:
            return []
        
        return [self._format_tv_show(tv) for tv in data['results'][:10]]
    
    def get_trending_movies(self) -> List[dict]:
        """Buscar filmes em alta"""
        data = self._make_request('trending/movie/week')
        
        if not data or 'results' not in data:
            return []
        
        return [self._format_movie(movie) for movie in data['results'][:10]]
    
    def get_trending_tv_shows(self) -> List[dict]:
        """Buscar séries em alta"""
        data = self._make_request('trending/tv/week')
        
        if not data or 'results' not in data:
            return []
        
        return [self._format_tv_show(tv) for tv in data['results'][:10]]
    
    def get_movie_details(self, movie_id: str) -> Optional[dict]:
        """Buscar detalhes de um filme"""
        data = self._make_request(f'movie/{movie_id}')
        
        if not data:
            return None
        
        return {
            'id': str(data.get('id')),
            'title': data.get('title'),
            'type': 'movie',
            'overview': data.get('overview'),
            'poster_url': f"{self.image_base_url}{data.get('poster_path')}" if data.get('poster_path') else None,
            'backdrop_url': f"https://image.tmdb.org/t/p/w1280{data.get('backdrop_path')}" if data.get('backdrop_path') else None,
            'release_date': data.get('release_date'),
            'rating': data.get('vote_average'),
            'runtime': data.get('runtime'),
            'genres': [genre['name'] for genre in data.get('genres', [])],
            'production_companies': [company['name'] for company in data.get('production_companies', [])],
            'budget': data.get('budget'),
            'revenue': data.get('revenue')
        }
    
    def get_tv_show_details(self, tv_id: str) -> Optional[dict]:
        """Buscar detalhes de uma série"""
        data = self._make_request(f'tv/{tv_id}')
        
        if not data:
            return None
        
        return {
            'id': str(data.get('id')),
            'title': data.get('name'),
            'type': 'tv',
            'overview': data.get('overview'),
            'poster_url': f"{self.image_base_url}{data.get('poster_path')}" if data.get('poster_path') else None,
            'backdrop_url': f"https://image.tmdb.org/t/p/w1280{data.get('backdrop_path')}" if data.get('backdrop_path') else None,
            'first_air_date': data.get('first_air_date'),
            'last_air_date': data.get('last_air_date'),
            'rating': data.get('vote_average'),
            'number_of_seasons': data.get('number_of_seasons'),
            'number_of_episodes': data.get('number_of_episodes'),
            'genres': [genre['name'] for genre in data.get('genres', [])],
            'networks': [network['name'] for network in data.get('networks', [])],
            'status': data.get('status')
        }
    
    def get_movies_by_genres(self, genre_names: List[str]) -> List[dict]:
        """Buscar filmes por gêneros"""
        # Mapeamento básico de gêneros (seria melhor buscar da API)
        genre_map = {
            'ação': 28, 'aventura': 12, 'animação': 16, 'comédia': 35,
            'crime': 80, 'documentário': 99, 'drama': 18, 'família': 10751,
            'fantasia': 14, 'história': 36, 'terror': 27, 'música': 10402,
            'mistério': 9648, 'romance': 10749, 'ficção científica': 878,
            'thriller': 53, 'guerra': 10752, 'western': 37
        }
        
        genre_ids = []
        for genre_name in genre_names:
            if genre_name.lower() in genre_map:
                genre_ids.append(genre_map[genre_name.lower()])
        
        if not genre_ids:
            return self.get_trending_movies()
        
        params = {
            'with_genres': ','.join(map(str, genre_ids)),
            'sort_by': 'popularity.desc'
        }
        
        data = self._make_request('discover/movie', params)
        
        if not data or 'results' not in data:
            return []
        
        return [self._format_movie(movie) for movie in data['results'][:10]]
    
    def get_tv_shows_by_genres(self, genre_names: List[str]) -> List[dict]:
        """Buscar séries por gêneros"""
        # Usar o mesmo mapeamento de gêneros
        genre_map = {
            'ação': 10759, 'aventura': 10759, 'animação': 16, 'comédia': 35,
            'crime': 80, 'documentário': 99, 'drama': 18, 'família': 10751,
            'fantasia': 10765, 'história': 36, 'terror': 27, 'música': 10402,
            'mistério': 9648, 'romance': 10749, 'ficção científica': 10765,
            'thriller': 53, 'guerra': 10768, 'western': 37
        }
        
        genre_ids = []
        for genre_name in genre_names:
            if genre_name.lower() in genre_map:
                genre_ids.append(genre_map[genre_name.lower()])
        
        if not genre_ids:
            return self.get_trending_tv_shows()
        
        params = {
            'with_genres': ','.join(map(str, genre_ids)),
            'sort_by': 'popularity.desc'
        }
        
        data = self._make_request('discover/tv', params)
        
        if not data or 'results' not in data:
            return []
        
        return [self._format_tv_show(tv) for tv in data['results'][:10]]

