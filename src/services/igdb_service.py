import os
import requests
from typing import List, Dict

class IGDBService:
    def __init__(self):
        self.client_id = os.environ.get('IGDB_CLIENT_ID')
        self.access_token = os.environ.get('IGDB_ACCESS_TOKEN')
        self.base_url = 'https://api.igdb.com/v4'
    
    def search_games(self, query: str) -> List[Dict]:
        if not self.client_id or not self.access_token:
            return self._get_mock_games(query)
        
        try:
            url = f"{self.base_url}/games"
            headers = {
                'Client-ID': self.client_id,
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            # Query IGDB usando Apicalypse
            data = f'''
            search "{query}";
            fields name, cover.url, rating, first_release_date, genres.name, summary, platforms.name;
            limit 10;
            '''
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            games_data = response.json()
            games = []
            
            for game in games_data:
                # Processar URL da capa
                cover_url = None
                if game.get('cover') and game['cover'].get('url'):
                    cover_url = f"https:{game['cover']['url'].replace('t_thumb', 't_cover_big')}"
                
                # Processar data de lançamento
                release_date = ''
                if game.get('first_release_date'):
                    import datetime
                    release_date = datetime.datetime.fromtimestamp(game['first_release_date']).strftime('%Y')
                
                # Processar gêneros
                genres = []
                if game.get('genres'):
                    genres = [genre.get('name', '') for genre in game['genres']]
                
                # Processar plataformas
                platforms = []
                if game.get('platforms'):
                    platforms = [platform.get('name', '') for platform in game['platforms']]
                
                games.append({
                    'id': str(game['id']),
                    'title': game.get('name', ''),
                    'type': 'game',
                    'poster_url': cover_url,
                    'rating': game.get('rating', 0) / 10 if game.get('rating') else 0,  # Converter para escala 0-10
                    'release_date': release_date,
                    'genres': genres,
                    'platforms': platforms,
                    'description': game.get('summary', '')
                })
            
            return games
            
        except Exception as e:
            print(f"Erro ao buscar jogos no IGDB: {e}")
            return self._get_mock_games(query)
    
    def _get_mock_games(self, query: str) -> List[Dict]:
        return [
            {
                'id': 'mock_game_1',
                'title': f'Jogo Mock: {query}',
                'type': 'game',
                'poster_url': 'https://via.placeholder.com/300x450/10B981/FFFFFF?text=Mock+Game',
                'rating': 8.8,
                'release_date': '2023',
                'genres': ['Ação', 'RPG'],
                'platforms': ['PC', 'PlayStation', 'Xbox'],
                'description': f'Este é um jogo mock para a busca "{query}". Dados reais virão da API IGDB.'
            }
        ]

