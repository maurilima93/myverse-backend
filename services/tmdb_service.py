import requests
import os
from typing import List, Dict, Optional

class TMDbService:
    def __init__(self):
        self.api_key = os.environ.get('TMDB_API_KEY')
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = 'https://image.tmdb.org/t/p/w500'
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Fazer requisição para a API do TMDb"""
        if not self.api_key:
            # Retornar dados mock se não houver API key
            return self._get_mock_data(endpoint)
        
        try:
            url = f"{self.base_url}/{endpoint}"
            default_params = {'api_key': self.api_key, 'language': 'pt-BR'}
            
            if params:
                default_params.update(params)
            
            response = requests.get(url, params=default_params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Erro na requisição TMDb: {e}")
            return self._get_mock_data(endpoint)
    
    def _get_mock_data(self, endpoint: str) -> Dict:
        """Retornar dados mock quando API não está disponível"""
        if 'search/movie' in endpoint:
            return {
                'results': [
                    {
                        'id': 155,
                        'title': 'The Dark Knight',
                        'overview': 'Batman enfrenta o Joker em Gotham City.',
                        'release_date': '2008-07-18',
                        'poster_path': '/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
                        'vote_average': 9.0,
                        'genre_ids': [28, 80, 18]
                    },
                    {
                        'id': 272,
                        'title': 'Batman Begins',
                        'overview': 'A origem do Batman.',
                        'release_date': '2005-06-10',
                        'poster_path': '/dr6x4GyyegBWtinPBzipY02J2lV.jpg',
                        'vote_average': 8.2,
                        'genre_ids': [28, 80]
                    }
                ]
            }
        elif 'search/tv' in endpoint:
            return {
                'results': [
                    {
                        'id': 1399,
                        'name': 'Game of Thrones',
                        'overview': 'Nove famílias nobres lutam pelo controle de Westeros.',
                        'first_air_date': '2011-04-17',
                        'poster_path': '/u3bZgnGQ9T01sWNhyveQz0wH0Hl.jpg',
                        'vote_average': 9.3,
                        'genre_ids': [18, 10759, 10765]
                    }
                ]
            }
        else:
            return {'results': []}
    
    def search_movies(self, query: str) -> List[Dict]:
        """Buscar filmes"""
        data = self._make_request('search/movie', {'query': query})
        
        if not data or 'results' not in data:
            return []
        
        movies = []
        for movie in data['results'][:10]:  # Limitar a 10 resultados
            movies.append({
                'id': movie['id'],
                'type': 'movie',
                'title': movie['title'],
                'overview': movie.get('overview', ''),
                'release_date': movie.get('release_date', ''),
                'poster_url': f"{self.image_base_url}{movie['poster_path']}" if movie.get('poster_path') else None,
                'rating': round(movie.get('vote_average', 0), 1),
                'genres': self._get_genre_names(movie.get('genre_ids', []), 'movie')
            })
        
        return movies
    
    def search_tv_shows(self, query: str) -> List[Dict]:
        """Buscar séries de TV"""
        data = self._make_request('search/tv', {'query': query})
        
        if not data or 'results' not in data:
            return []
        
        tv_shows = []
        for show in data['results'][:10]:  # Limitar a 10 resultados
            tv_shows.append({
                'id': show['id'],
                'type': 'tv',
                'title': show['name'],
                'overview': show.get('overview', ''),
                'release_date': show.get('first_air_date', ''),
                'poster_url': f"{self.image_base_url}{show['poster_path']}" if show.get('poster_path') else None,
                'rating': round(show.get('vote_average', 0), 1),
                'genres': self._get_genre_names(show.get('genre_ids', []), 'tv')
            })
        
        return tv_shows
    
    def get_popular_movies(self) -> List[Dict]:
        """Buscar filmes populares"""
        data = self._make_request('movie/popular')
        
        if not data or 'results' not in data:
            return []
        
        movies = []
        for movie in data['results'][:20]:
            movies.append({
                'id': movie['id'],
                'type': 'movie',
                'title': movie['title'],
                'overview': movie.get('overview', ''),
                'release_date': movie.get('release_date', ''),
                'poster_url': f"{self.image_base_url}{movie['poster_path']}" if movie.get('poster_path') else None,
                'rating': round(movie.get('vote_average', 0), 1),
                'genres': self._get_genre_names(movie.get('genre_ids', []), 'movie')
            })
        
        return movies
    
    def get_popular_tv_shows(self) -> List[Dict]:
        """Buscar séries populares"""
        data = self._make_request('tv/popular')
        
        if not data or 'results' not in data:
            return []
        
        tv_shows = []
        for show in data['results'][:20]:
            tv_shows.append({
                'id': show['id'],
                'type': 'tv',
                'title': show['name'],
                'overview': show.get('overview', ''),
                'release_date': show.get('first_air_date', ''),
                'poster_url': f"{self.image_base_url}{show['poster_path']}" if show.get('poster_path') else None,
                'rating': round(show.get('vote_average', 0), 1),
                'genres': self._get_genre_names(show.get('genre_ids', []), 'tv')
            })
        
        return tv_shows
    
    def get_movies_by_genre(self, genre_name: str) -> List[Dict]:
        """Buscar filmes por gênero"""
        # Mapear nome do gênero para ID
        genre_map = {
            'Action': 28, 'Adventure': 12, 'Animation': 16, 'Comedy': 35,
            'Crime': 80, 'Documentary': 99, 'Drama': 18, 'Family': 10751,
            'Fantasy': 14, 'History': 36, 'Horror': 27, 'Music': 10402,
            'Mystery': 9648, 'Romance': 10749, 'Science Fiction': 878,
            'TV Movie': 10770, 'Thriller': 53, 'War': 10752, 'Western': 37
        }
        
        genre_id = genre_map.get(genre_name)
        if not genre_id:
            return []
        
        data = self._make_request('discover/movie', {'with_genres': genre_id})
        
        if not data or 'results' not in data:
            return []
        
        movies = []
        for movie in data['results'][:10]:
            movies.append({
                'id': movie['id'],
                'type': 'movie',
                'title': movie['title'],
                'overview': movie.get('overview', ''),
                'release_date': movie.get('release_date', ''),
                'poster_url': f"{self.image_base_url}{movie['poster_path']}" if movie.get('poster_path') else None,
                'rating': round(movie.get('vote_average', 0), 1),
                'genres': self._get_genre_names(movie.get('genre_ids', []), 'movie')
            })
        
        return movies
    
    def get_tv_shows_by_genre(self, genre_name: str) -> List[Dict]:
        """Buscar séries por gênero"""
        # Mapear nome do gênero para ID
        genre_map = {
            'Action & Adventure': 10759, 'Animation': 16, 'Comedy': 35,
            'Crime': 80, 'Documentary': 99, 'Drama': 18, 'Family': 10751,
            'Kids': 10762, 'Mystery': 9648, 'News': 10763, 'Reality': 10764,
            'Sci-Fi & Fantasy': 10765, 'Soap': 10766, 'Talk': 10767,
            'War & Politics': 10768, 'Western': 37
        }
        
        genre_id = genre_map.get(genre_name)
        if not genre_id:
            return []
        
        data = self._make_request('discover/tv', {'with_genres': genre_id})
        
        if not data or 'results' not in data:
            return []
        
        tv_shows = []
        for show in data['results'][:10]:
            tv_shows.append({
                'id': show['id'],
                'type': 'tv',
                'title': show['name'],
                'overview': show.get('overview', ''),
                'release_date': show.get('first_air_date', ''),
                'poster_url': f"{self.image_base_url}{show['poster_path']}" if show.get('poster_path') else None,
                'rating': round(show.get('vote_average', 0), 1),
                'genres': self._get_genre_names(show.get('genre_ids', []), 'tv')
            })
        
        return tv_shows
    
    def _get_genre_names(self, genre_ids: List[int], media_type: str) -> List[str]:
        """Converter IDs de gênero para nomes"""
        movie_genres = {
            28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy',
            80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
            14: 'Fantasy', 36: 'History', 27: 'Horror', 10402: 'Music',
            9648: 'Mystery', 10749: 'Romance', 878: 'Science Fiction',
            10770: 'TV Movie', 53: 'Thriller', 10752: 'War', 37: 'Western'
        }
        
        tv_genres = {
            10759: 'Action & Adventure', 16: 'Animation', 35: 'Comedy',
            80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
            10762: 'Kids', 9648: 'Mystery', 10763: 'News', 10764: 'Reality',
            10765: 'Sci-Fi & Fantasy', 10766: 'Soap', 10767: 'Talk',
            10768: 'War & Politics', 37: 'Western'
        }
        
        genre_map = movie_genres if media_type == 'movie' else tv_genres
        
        return [genre_map.get(genre_id, 'Unknown') for genre_id in genre_ids if genre_id in genre_map]

