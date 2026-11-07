# coding: utf-8
import json
import os
import tempfile
import unittest
from collections import OrderedDict

_TEMP_DIR = tempfile.TemporaryDirectory()
os.environ['SEQUENCIAS_DB'] = os.path.join(_TEMP_DIR.name, 'sequencias.db')

import main  # noqa: E402
import sequencias_db  # noqa: E402
from musica import Musica  # noqa: E402


ORIGINAIS = [
    (0, 'Bm,G,D,A', 'bm;g;d;a', 199),
    (1, 'C,G,Am,F', 'c;g;am;f', 296),
    (2, 'Em,G', 'em;g', 4),
    (3, 'C,A7,Dm,G7', 'c;a7;dm;g7', 5),
    (4, 'Gm,F', 'gm;f', 7),
    (5, 'C,C7,F,Fm', 'c;c7;f;fm', 3),
]


class BaseTest(unittest.TestCase):

    def setUp(self):
        caminho = sequencias_db.caminho_db()
        if os.path.exists(caminho):
            os.remove(caminho)
        sequencias_db.init_db()
        self.client = main.app.test_client()


class TestCatalogo(BaseTest):

    def test_get_lista_as_seis_originais(self):
        resposta = self.client.get('/sequencias')
        self.assertEqual(200, resposta.status_code)
        self.assertTrue(resposta.content_type.startswith('text/html'))
        catalogo = json.loads(resposta.data)
        self.assertEqual(
            ['bmgda', 'cgamf', 'emg', 'ca7dmg7', 'gmf', 'cc7ffm'],
            [item['chave'] for item in catalogo],
        )

    def test_seed_nao_duplica(self):
        sequencias_db.init_db()
        self.assertEqual(6, len(sequencias_db.listar_sequencias()))

    def test_post_cria_sequencia_normalizada(self):
        resposta = self.client.post('/sequencias', json={
            'nome': 'Nova', 'acordes': 'D,A,Bm,G',
        })
        self.assertEqual(201, resposta.status_code)
        sequencia = json.loads(resposta.data)
        self.assertEqual('d;a;bm;g', sequencia['acordes'])
        self.assertEqual('dabmg', sequencia['chave'])
        self.assertEqual(7, len(sequencias_db.listar_sequencias()))

    def test_post_aceita_lista(self):
        resposta = self.client.post('/sequencias', json={
            'nome': 'Lista', 'acordes': ['D', 'A', 'Bm', 'G'],
        })
        self.assertEqual(201, resposta.status_code)
        self.assertEqual('d;a;bm;g', json.loads(resposta.data)['acordes'])

    def test_post_duplicata_devolve_existente(self):
        criada = json.loads(self.client.post('/sequencias', json={
            'nome': 'Nova', 'acordes': 'D,A,Bm,G',
        }).data)
        resposta = self.client.post('/sequencias', json={
            'nome': 'Outro nome', 'acordes': ['d', 'a', 'bm', 'g'],
        })
        self.assertEqual(200, resposta.status_code)
        self.assertEqual(criada['id'], json.loads(resposta.data)['id'])
        self.assertEqual(7, len(sequencias_db.listar_sequencias()))

    def test_post_acordes_vazios_retorna_400(self):
        for acordes in ('', [], None):
            with self.subTest(acordes=acordes):
                resposta = self.client.post('/sequencias', json={
                    'nome': 'Vazia', 'acordes': acordes,
                })
                self.assertEqual(400, resposta.status_code)

    def test_post_corpo_invalido_retorna_400(self):
        resposta = self.client.post(
            '/sequencias', data='nao e json', content_type='text/plain')
        self.assertEqual(400, resposta.status_code)


class TestBusca(BaseTest):

    def setUp(self):
        super().setUp()
        self._globais = (main.musicas, main.generos, main.genero_musicas)
        musicas = [
            self._musica('m1', 'Rock', ['C', 'G', 'Am', 'F'], 10),
            self._musica('m2', 'Rock', ['C', 'G', 'Am', 'F', 'Dm'], 9),
            self._musica('m3', 'Samba', ['C', 'G', 'Em', 'F'], 8),
            self._musica('m4', 'Samba', ['c', 'g', 'am', 'f'], 7),
            self._musica('m5', 'Rock', ['G', 'Am', 'F'], 6),
            self._musica('m6', 'Samba', ['G', 'Am', 'F'], 5),
        ]
        main.musicas = OrderedDict(
            (musica.id_unico_musica, musica)
            for musica in sorted(musicas, key=lambda m: m.popularidade, reverse=True)
        )
        main.generos = ['Rock', 'Samba']
        main.genero_musicas = {'Rock': [], 'Samba': []}
        for musica in main.musicas.values():
            main.genero_musicas[musica.genero].append(musica)

    def tearDown(self):
        main.musicas, main.generos, main.genero_musicas = self._globais

    def _musica(self, id_musica, genero, cifra, popularidade):
        return Musica(
            'art', 'Artista ' + id_musica, id_musica, 'Musica ' + id_musica,
            genero, popularidade, [], 'C', cifra,
        )

    def _buscar(self, sequencia, generos=None):
        query = {'sequencia': sequencia}
        if generos:
            query['generos'] = generos
        resposta = self.client.get('/similares', query_string=query)
        self.assertEqual(200, resposta.status_code)
        return json.loads(resposta.data)

    def test_busca_sequencia_nova(self):
        self.client.post('/sequencias', json={
            'nome': 'Nova', 'acordes': 'G,Am,F',
        })
        encontrados = self._buscar('G,Am,F')
        self.assertEqual(
            {'art_m5', 'art_m6'},
            {item['id_unico_musica'] for item in encontrados},
        )

    def test_busca_ignora_maiusculas(self):
        self.client.post('/sequencias', json={
            'nome': 'Nova', 'acordes': 'g,am,f',
        })
        encontrados = self._buscar('G,AM,F')
        self.assertEqual(
            {'art_m5', 'art_m6'},
            {item['id_unico_musica'] for item in encontrados},
        )

    def test_busca_filtra_genero(self):
        self.client.post('/sequencias', json={
            'nome': 'Nova', 'acordes': 'G,Am,F',
        })
        encontrados = self._buscar('G,Am,F', generos='Samba')
        self.assertEqual(
            {'art_m6'},
            {item['id_unico_musica'] for item in encontrados},
        )

    def test_busca_sequencia_desconhecida_retorna_vazio(self):
        self.assertEqual([], self._buscar('X,Y,Z'))


class TestRegressao(BaseTest):

    def _todas_as_paginas(self, sequencia):
        encontrados = []
        pagina = 1
        while pagina <= 10:
            resposta = self.client.get('/similares', query_string={
                'sequencia': sequencia, 'pagina': pagina,
            })
            self.assertEqual(200, resposta.status_code)
            lote = json.loads(resposta.data)
            if not lote:
                break
            encontrados.extend(lote)
            pagina += 1
        return encontrados

    def test_conjunto_igual_ao_da_tag_nas_seis(self):
        for id_legado, sequencia, acordes, total in ORIGINAIS:
            with self.subTest(sequencia=sequencia):
                esperado = {
                    musica.id_unico_musica
                    for musica in main.musicas.values()
                    if str(id_legado) in musica.seqs_famosas
                }
                obtido = {
                    item['id_unico_musica']
                    for item in self._todas_as_paginas(sequencia)
                }
                self.assertEqual(total, len(esperado))
                self.assertEqual(esperado, obtido)

    def test_paginacao_da_sequencia_maior(self):
        primeira = json.loads(self.client.get(
            '/similares', query_string={'sequencia': 'Bm,G,D,A', 'pagina': 1}
        ).data)
        segunda = json.loads(self.client.get(
            '/similares', query_string={'sequencia': 'Bm,G,D,A', 'pagina': 2}
        ).data)
        self.assertEqual(100, len(primeira))
        self.assertEqual(99, len(segunda))


if __name__ == '__main__':
    unittest.main()
