import os
import requests
from typing import List, Dict, Optional

class IGDBService:
    def __init__(self):
        self.client_id = os.environ.get('IGDB_CLIENT_ID')
        self.access_token = os.environ.get('IGDB_ACCESS_TOKEN')
        self.base_url = 'https://api.igdb.com/v4'
        
    def _make_request(self, endpoint: str, query: str) -> Optional[list]:
        """Fazer requisição para a API do IGDB"""
        if not self.client_id or not self.access_token:
            # Retornar dados mock se não tiver credenciais
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
            
        except requests.RequestException as e:
            print(f"Erro na requisição IGDB: {e}")
            return self._get_mock_data(endpoint, query)
    
    def _get_mock_data(self, endpoint: str, query: str) -> list:
        """Retornar dados mock para desenvolvimento"""
        if 'search' in query.lower() or 'games' in endpoint:
            return [
                {
                    'id': 1942,
                    'name': 'The Witcher 3: Wild Hunt',
                    'summary': 'Um RPG de mundo aberto ambientado em um universo de fantasia sombria.',
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co1rfi.jpg'},
                    'first_release_date': 1431993600,
                    'rating': 94.5,
                    'genres': [{'name': 'RPG'}, {'name': 'Aventura'}],
                    'platforms': [{'name': 'PC'}, {'name': 'PlayStation 4'}, {'name': 'Xbox One'}]
                },
                {
                    'id': 1074,
                    'name': 'Grand Theft Auto V',
                    'summary': 'Um jogo de ação-aventura em mundo aberto.',
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co2lbd.jpg'},
                    'first_release_date': 1379376000,
                    'rating': 92.3,
                    'genres': [{'name': 'Ação'}, {'name': 'Aventura'}],
                    'platforms': [{'name': 'PC'}, {'name': 'PlayStation 5'}, {'name': 'Xbox Series X/S'}]
                },
                {
                    'id': 119388,
                    'name': 'Cyberpunk 2077',
                    'summary': 'Um RPG de ação em primeira pessoa ambientado em Night City.',
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co2dpv.jpg'},
                    'first_release_date': 1607558400,
                    'rating': 78.9,
                    'genres': [{'name': 'RPG'}, {'name': 'Ação'}],
                    'platforms': [{'name': 'PC'}, {'name': 'PlayStation 5'}, {'name': 'Xbox Series X/S'}]
                },
                {
                    'id': 1877,
                    'name': 'Red Dead Redemption 2',
                    'summary': 'Um jogo de ação-aventura ambientado no Velho Oeste.',
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co1q1f.jpg'},
                    'first_release_date': 1540425600,
                    'rating': 96.4,
                    'genres': [{'name': 'Ação'}, {'name': 'Aventura'}],
                    'platforms': [{'name': 'PC'}, {'name': 'PlayStation 4'}, {'name': 'Xbox One'}]
                },
                {
                    'id': 1905,
                    'name': 'God of War',
                    'summary': 'Kratos e seu filho Atreus embarcam em uma jornada épica.',
                    'cover': {'url': '//images.igdb.com/igdb/image/upload/t_cover_big/co1tmu.jpg'},
                    'first_release_date': 1524182400,
                    'rating': 94.2,
                    'genres': [{'name': 'Ação'}, {'name': 'Aventura'}],
                    'platforms': [{'name': 'PlayStation 4'}, {'name': 'PC'}]
                }
            ]
        
        return []
    
    def _format_game(self, game_data: dict) -> dict:
        """Formatar dados do jogo"""
        # Converter timestamp para data
        release_date = None
        if game_data.get('first_release_date'):
            from datetime import datetime
            release_date = datetime.fromtimestamp(game_data['first_release_date']).strftime('%Y-%m-%d')
        
        # Formatar URL da capa
        cover_url = None
        if game_data.get('cover') and game_data['cover'].get('url'):
            cover_url = f"https:{game_data['cover']['url']}"
        
        return {
            'id': str(game_data.get('id')),
            'title': game_data.get('name'),
            'type': 'game',
            'overview': game_data.get('summary'),
            'poster_url': cover_url,
            'release_date': release_date,
            'rating': game_data.get('rating'),
            'genres': [genre['name'] for genre in game_data.get('genres', [])],
            'platforms': [platform['name'] for platform in game_data.get('platforms', [])]
        }
    
    def search_games(self, query: str) -> List[dict]:
        """Buscar jogos"""
        igdb_query = f'''
        search "{query}";
        fields name, summary, cover.url, first_release_date, rating, genres.name, platforms.name;
        limit 10;
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data:
            return []
        
        return [self._format_game(game) for game in data]
    
    def get_popular_games(self) -> List[dict]:
        """Buscar jogos populares"""
        igdb_query = '''
        fields name, summary, cover.url, first_release_date, rating, genres.name, platforms.name;
        sort rating desc;
        where rating > 80 & rating_count > 100;
        limit 10;
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data:
            return []
        
        return [self._format_game(game) for game in data]
    
    def get_game_details(self, game_id: str) -> Optional[dict]:
        """Buscar detalhes de um jogo"""
        igdb_query = f'''
        fields name, summary, storyline, cover.url, screenshots.url, first_release_date, 
               rating, rating_count, genres.name, platforms.name, involved_companies.company.name,
               game_modes.name, themes.name, websites.url;
        where id = {game_id};
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data or len(data) == 0:
            return None
        
        game = data[0]
        
        # Formatar screenshots
        screenshots = []
        if game.get('screenshots'):
            screenshots = [f"https:{screenshot['url']}" for screenshot in game['screenshots']]
        
        # Formatar empresas
        companies = []
        if game.get('involved_companies'):
            companies = [company['company']['name'] for company in game['involved_companies']]
        
        return {
            'id': str(game.get('id')),
            'title': game.get('name'),
            'type': 'game',
            'overview': game.get('summary'),
            'storyline': game.get('storyline'),
            'poster_url': f"https:{game['cover']['url']}" if game.get('cover') else None,
            'screenshots': screenshots,
            'release_date': game.get('first_release_date'),
            'rating': game.get('rating'),
            'rating_count': game.get('rating_count'),
            'genres': [genre['name'] for genre in game.get('genres', [])],
            'platforms': [platform['name'] for platform in game.get('platforms', [])],
            'companies': companies,
            'game_modes': [mode['name'] for mode in game.get('game_modes', [])],
            'themes': [theme['name'] for theme in game.get('themes', [])],
            'websites': [website['url'] for website in game.get('websites', [])]
        }
    
    def get_games_by_genres(self, genre_names: List[str]) -> List[dict]:
        """Buscar jogos por gêneros"""
        # Mapeamento básico de gêneros para IGDB
        genre_map = {
            'ação': 'Action',
            'aventura': 'Adventure', 
            'rpg': 'Role-playing (RPG)',
            'estratégia': 'Strategy',
            'simulação': 'Simulator',
            'esportes': 'Sport',
            'corrida': 'Racing',
            'luta': 'Fighting',
            'plataforma': 'Platform',
            'puzzle': 'Puzzle',
            'tiro': 'Shooter',
            'terror': 'Horror'
        }
        
        # Converter nomes de gêneros
        igdb_genres = []
        for genre_name in genre_names:
            if genre_name.lower() in genre_map:
                igdb_genres.append(genre_map[genre_name.lower()])
        
        if not igdb_genres:
            return self.get_popular_games()
        
        # Criar query para buscar por gêneros
        genre_filter = ' | '.join([f'genres.name = "{genre}"' for genre in igdb_genres])
        
        igdb_query = f'''
        fields name, summary, cover.url, first_release_date, rating, genres.name, platforms.name;
        where ({genre_filter}) & rating > 70;
        sort rating desc;
        limit 10;
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data:
            return []
        
        return [self._format_game(game) for game in data]
    
    def get_trending_games(self) -> List[dict]:
        """Buscar jogos em alta (baseado em data de lançamento recente e rating)"""
        from datetime import datetime, timedelta
        
        # Data de 2 anos atrás em timestamp
        two_years_ago = int((datetime.now() - timedelta(days=730)).timestamp())
        
        igdb_query = f'''
        fields name, summary, cover.url, first_release_date, rating, genres.name, platforms.name;
        where first_release_date > {two_years_ago} & rating > 75;
        sort rating desc;
        limit 10;
        '''
        
        data = self._make_request('games', igdb_query)
        
        if not data:
            return self.get_popular_games()
        
        return [self._format_game(game) for game in data]

