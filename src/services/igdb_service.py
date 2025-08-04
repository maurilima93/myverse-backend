import requests
import os
from typing import List, Dict, Optional

class IGDBService:
    def __init__(self):
        self.client_id = os.environ.get('IGDB_CLIENT_ID')
        self.access_token = os.environ.get('IGDB_ACCESS_TOKEN')
        self.base_url = 'https://api.igdb.com/v4'
        
    def _make_request(self, endpoint: str, query: str) -> Optional[List[Dict]]:
        """Fazer requisição para a API do IGDB"""
        if not self.client_id or not self.access_token:
            # Retornar dados mock se não houver credenciais
            return self._get_mock_data(endpoint, query)
        
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = {
                'Client-ID': self.client_id,
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=query, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Erro na requisição IGDB: {e}")
            return self._get_mock_data(endpoint, query)
    
    def _get_mock_data(self, endpoint: str, query: str) -> List[Dict]:
        """Retornar dados mock quando API não está disponível"""
        if 'search' in query.lower() or 'batman' in query.lower():
            return [
                {
                    'id': 1942,
                    'name': 'The Witcher 3: Wild Hunt',
                    'summary': 'Um RPG de mundo aberto ambientado em um universo de fantasia sombria.',
                    'first_release_date': 1431993600,  # 2015-05-19
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co1rfi.jpg'},
                    'rating': 94.5,
                    'genres': [{'name': 'Role-playing (RPG)'}, {'name': 'Adventure'}],
                    'platforms': [{'name': 'PC (Microsoft Windows)'}, {'name': 'PlayStation 4'}, {'name': 'Xbox One'}]
                },
                {
                    'id': 1020,
                    'name': 'Grand Theft Auto V',
                    'summary': 'Um jogo de ação-aventura em mundo aberto.',
                    'first_release_date': 1379376000,  # 2013-09-17
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co1tmu.jpg'},
                    'rating': 90.2,
                    'genres': [{'name': 'Shooter'}, {'name': 'Racing'}, {'name': 'Adventure'}],
                    'platforms': [{'name': 'PC (Microsoft Windows)'}, {'name': 'PlayStation 4'}, {'name': 'Xbox One'}]
                },
                {
                    'id': 121,
                    'name': 'Minecraft',
                    'summary': 'Um jogo sandbox que permite aos jogadores construir com uma variedade de blocos diferentes.',
                    'first_release_date': 1289779200,  # 2010-11-18
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co49x5.jpg'},
                    'rating': 83.0,
                    'genres': [{'name': 'Simulator'}, {'name': 'Adventure'}, {'name': 'Indie'}],
                    'platforms': [{'name': 'PC (Microsoft Windows)'}, {'name': 'Android'}, {'name': 'iOS'}]
                },
                {
                    'id': 1877,
                    'name': 'Cyberpunk 2077',
                    'summary': 'Um RPG de ação em mundo aberto ambientado na megalópole de Night City.',
                    'first_release_date': 1607558400,  # 2020-12-10
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co1wyy.jpg'},
                    'rating': 78.3,
                    'genres': [{'name': 'Role-playing (RPG)'}, {'name': 'Shooter'}],
                    'platforms': [{'name': 'PC (Microsoft Windows)'}, {'name': 'PlayStation 4'}, {'name': 'Xbox One'}]
                },
                {
                    'id': 1905,
                    'name': 'Red Dead Redemption 2',
                    'summary': 'Um jogo de ação-aventura ambientado no Velho Oeste americano.',
                    'first_release_date': 1540425600,  # 2018-10-26
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co1q1f.jpg'},
                    'rating': 93.0,
                    'genres': [{'name': 'Adventure'}, {'name': 'Shooter'}],
                    'platforms': [{'name': 'PC (Microsoft Windows)'}, {'name': 'PlayStation 4'}, {'name': 'Xbox One'}]
                }
            ]
        else:
            return []
    
    def search_games(self, query: str) -> List[Dict]:
        """Buscar jogos"""
        igdb_query = f'''
        search "{query}";
        fields name, summary, first_release_date, cover.url, rating, genres.name, platforms.name;
        limit 10;
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data:
            return []
        
        games = []
        for game in data:
            # Converter timestamp para data
            release_date = ''
            if game.get('first_release_date'):
                from datetime import datetime
                release_date = datetime.fromtimestamp(game['first_release_date']).strftime('%Y-%m-%d')
            
            # Processar URL da capa
            cover_url = None
            if game.get('cover') and game['cover'].get('url'):
                cover_url = f"https:{game['cover']['url'].replace('t_thumb', 't_cover_big')}"
            
            # Processar gêneros
            genres = []
            if game.get('genres'):
                genres = [genre['name'] for genre in game['genres']]
            
            # Processar plataformas
            platforms = []
            if game.get('platforms'):
                platforms = [platform['name'] for platform in game['platforms'][:5]]  # Limitar a 5 plataformas
            
            games.append({
                'id': game['id'],
                'type': 'game',
                'title': game['name'],
                'overview': game.get('summary', ''),
                'release_date': release_date,
                'poster_url': cover_url,
                'rating': round(game.get('rating', 0) / 10, 1) if game.get('rating') else 0,  # Converter de 0-100 para 0-10
                'genres': genres,
                'platforms': platforms
            })
        
        return games
    
    def get_popular_games(self) -> List[Dict]:
        """Buscar jogos populares"""
        igdb_query = '''
        fields name, summary, first_release_date, cover.url, rating, genres.name, platforms.name;
        sort rating desc;
        where rating > 80 & first_release_date > 1420070400;
        limit 20;
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data:
            return []
        
        games = []
        for game in data:
            # Converter timestamp para data
            release_date = ''
            if game.get('first_release_date'):
                from datetime import datetime
                release_date = datetime.fromtimestamp(game['first_release_date']).strftime('%Y-%m-%d')
            
            # Processar URL da capa
            cover_url = None
            if game.get('cover') and game['cover'].get('url'):
                cover_url = f"https:{game['cover']['url'].replace('t_thumb', 't_cover_big')}"
            
            # Processar gêneros
            genres = []
            if game.get('genres'):
                genres = [genre['name'] for genre in game['genres']]
            
            # Processar plataformas
            platforms = []
            if game.get('platforms'):
                platforms = [platform['name'] for platform in game['platforms'][:5]]
            
            games.append({
                'id': game['id'],
                'type': 'game',
                'title': game['name'],
                'overview': game.get('summary', ''),
                'release_date': release_date,
                'poster_url': cover_url,
                'rating': round(game.get('rating', 0) / 10, 1) if game.get('rating') else 0,
                'genres': genres,
                'platforms': platforms
            })
        
        return games
    
    def get_games_by_genre(self, genre_name: str) -> List[Dict]:
        """Buscar jogos por gênero"""
        # Mapear nomes de gêneros comuns
        genre_map = {
            'Action': 'Action',
            'Adventure': 'Adventure', 
            'RPG': 'Role-playing (RPG)',
            'Strategy': 'Strategy',
            'Shooter': 'Shooter',
            'Sports': 'Sport',
            'Racing': 'Racing',
            'Puzzle': 'Puzzle',
            'Platform': 'Platform',
            'Fighting': 'Fighting',
            'Simulation': 'Simulator'
        }
        
        mapped_genre = genre_map.get(genre_name, genre_name)
        
        igdb_query = f'''
        fields name, summary, first_release_date, cover.url, rating, genres.name, platforms.name;
        where genres.name = "{mapped_genre}" & rating > 70;
        sort rating desc;
        limit 10;
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data:
            return []
        
        games = []
        for game in data:
            # Converter timestamp para data
            release_date = ''
            if game.get('first_release_date'):
                from datetime import datetime
                release_date = datetime.fromtimestamp(game['first_release_date']).strftime('%Y-%m-%d')
            
            # Processar URL da capa
            cover_url = None
            if game.get('cover') and game['cover'].get('url'):
                cover_url = f"https:{game['cover']['url'].replace('t_thumb', 't_cover_big')}"
            
            # Processar gêneros
            genres = []
            if game.get('genres'):
                genres = [genre['name'] for genre in game['genres']]
            
            # Processar plataformas
            platforms = []
            if game.get('platforms'):
                platforms = [platform['name'] for platform in game['platforms'][:5]]
            
            games.append({
                'id': game['id'],
                'type': 'game',
                'title': game['name'],
                'overview': game.get('summary', ''),
                'release_date': release_date,
                'poster_url': cover_url,
                'rating': round(game.get('rating', 0) / 10, 1) if game.get('rating') else 0,
                'genres': genres,
                'platforms': platforms
            })
        
        return games

