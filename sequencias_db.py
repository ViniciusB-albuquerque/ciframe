# coding: utf-8
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

DB_PADRAO = os.path.join('data', 'sequencias.db')

SEQUENCIAS_ORIGINAIS = [
    ('Bm G D A', 'bm;g;d;a'),
    ('C G Am F', 'c;g;am;f'),
    ('Em G', 'em;g'),
    ('C A7 Dm G7', 'c;a7;dm;g7'),
    ('Gm F', 'gm;f'),
    ('C C7 F Fm', 'c;c7;f;fm'),
]


def caminho_db(caminho=None):
    return caminho or os.environ.get('SEQUENCIAS_DB', DB_PADRAO)


def normalizar_acordes(acordes):
    if isinstance(acordes, str):
        partes = acordes.replace(';', ',').split(',')
    elif isinstance(acordes, (list, tuple)):
        partes = []
        for item in acordes:
            if isinstance(item, str):
                partes.extend(item.replace(';', ',').split(','))
    else:
        return []
    return [parte.strip().lower() for parte in partes if parte.strip()]


def normalizar_chave(chave):
    if not isinstance(chave, str):
        return ''
    return ''.join(normalizar_acordes(chave))


def _conectar(caminho=None):
    caminho = caminho_db(caminho)
    diretorio = os.path.dirname(os.path.abspath(caminho))
    os.makedirs(diretorio, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def _para_dict(linha):
    return {
        'id': linha['id'],
        'nome': linha['nome'],
        'acordes': linha['acordes'],
        'chave': linha['chave'],
        'criado_em': linha['criado_em'],
    }


def _buscar_por_chave(conexao, chave):
    linha = conexao.execute(
        'SELECT id, nome, acordes, chave, criado_em FROM sequencias WHERE chave = ?',
        (chave,),
    ).fetchone()
    return _para_dict(linha) if linha else None


def init_db(caminho=None):
    agora = datetime.now(timezone.utc).isoformat()
    with closing(_conectar(caminho)) as conexao:
        conexao.execute(
            '''
            CREATE TABLE IF NOT EXISTS sequencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                acordes TEXT NOT NULL,
                chave TEXT NOT NULL UNIQUE,
                criado_em TEXT NOT NULL
            )
            '''
        )
        for nome, acordes in SEQUENCIAS_ORIGINAIS:
            conexao.execute(
                '''
                INSERT OR IGNORE INTO sequencias (nome, acordes, chave, criado_em)
                VALUES (?, ?, ?, ?)
                ''',
                (nome, acordes, acordes.replace(';', ''), agora),
            )
        conexao.commit()


def listar_sequencias(caminho=None):
    with closing(_conectar(caminho)) as conexao:
        linhas = conexao.execute(
            'SELECT id, nome, acordes, chave, criado_em FROM sequencias ORDER BY id'
        ).fetchall()
    return [_para_dict(linha) for linha in linhas]


def buscar_por_chave(chave, caminho=None):
    chave = normalizar_chave(chave)
    if not chave:
        return None
    with closing(_conectar(caminho)) as conexao:
        return _buscar_por_chave(conexao, chave)


def criar_sequencia(nome, acordes, caminho=None):
    tokens = normalizar_acordes(acordes)
    if not tokens:
        raise ValueError('informe ao menos um acorde')

    nome = nome.strip() if isinstance(nome, str) else ''
    if not nome:
        nome = ', '.join(tokens)
    chave = ''.join(tokens)
    acordes = ';'.join(tokens)
    agora = datetime.now(timezone.utc).isoformat()

    with closing(_conectar(caminho)) as conexao:
        existente = _buscar_por_chave(conexao, chave)
        if existente:
            return existente, False
        try:
            cursor = conexao.execute(
                '''
                INSERT INTO sequencias (nome, acordes, chave, criado_em)
                VALUES (?, ?, ?, ?)
                ''',
                (nome, acordes, chave, agora),
            )
            conexao.commit()
        except sqlite3.IntegrityError:
            conexao.rollback()
            return _buscar_por_chave(conexao, chave), False
        return {
            'id': cursor.lastrowid,
            'nome': nome,
            'acordes': acordes,
            'chave': chave,
            'criado_em': agora,
        }, True
