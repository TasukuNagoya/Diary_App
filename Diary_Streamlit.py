import sqlite3
from datetime import date, datetime
from pathlib import Path
import tempfile

import pandas as pd
import streamlit as st

DB_FILE = Path(__file__).with_name('diary.db')

st.set_page_config(page_title='日記帳', page_icon='📔', layout='wide')


def connect():
    return sqlite3.connect(DB_FILE, timeout=15)


def init_db():
    with connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            diary_date TEXT NOT NULL,
            breakfast TEXT,
            lunch TEXT,
            dinner TEXT,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')


def list_entries(day=None):
    sql = 'SELECT id, diary_date, breakfast, lunch, dinner, content FROM diary_entries'
    args = ()
    if day is not None:
        sql += ' WHERE diary_date = ?'
        args = (day.isoformat(),)
    sql += ' ORDER BY diary_date DESC, id DESC'
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=args)


def get_entry(entry_id):
    with connect() as conn:
        return conn.execute('SELECT diary_date, breakfast, lunch, dinner, content FROM diary_entries WHERE id = ?', (entry_id,)).fetchone()


def clear_form():
    st.session_state.selected_id = None
    st.session_state.diary_date = date.today()
    for field in ('breakfast', 'lunch', 'dinner', 'content'):
        st.session_state[field] = ''


def select_entry(entry_id):
    row = get_entry(entry_id)
    if row:
        st.session_state.selected_id = entry_id
        st.session_state.diary_date = date.fromisoformat(row[0])
        for field, value in zip(('breakfast', 'lunch', 'dinner', 'content'), row[1:]):
            st.session_state[field] = value or ''


def save_entry():
    data = (st.session_state.diary_date.isoformat(),) + tuple(st.session_state[k].strip() for k in ('breakfast', 'lunch', 'dinner', 'content'))
    with connect() as conn:
        conn.execute('INSERT INTO diary_entries (diary_date, breakfast, lunch, dinner, content) VALUES (?, ?, ?, ?, ?)', data)
    clear_form()
    st.session_state.notice = '日記を保存しました。'


def update_entry():
    entry_id = st.session_state.selected_id
    if entry_id is None:
        st.warning('更新する日記を一覧から選択してください。')
        return
    data = (st.session_state.diary_date.isoformat(),) + tuple(st.session_state[k].strip() for k in ('breakfast', 'lunch', 'dinner', 'content')) + (entry_id,)
    with connect() as conn:
        conn.execute('UPDATE diary_entries SET diary_date=?, breakfast=?, lunch=?, dinner=?, content=? WHERE id=?', data)
    clear_form()
    st.session_state.notice = '日記を更新しました。'


init_db()
if 'selected_id' not in st.session_state:
    clear_form()

st.title('📔 日記帳')
st.caption('食事と日々の出来事を記録できます。')
if st.session_state.pop('notice', None):
    st.success('保存内容を反映しました。')

st.subheader('日記入力・編集')
if st.session_state.selected_id is not None:
    st.info(f'編集中の日記 ID: {st.session_state.selected_id}')

with st.form('diary_form'):
    st.date_input('日付', key='diary_date')
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text_input('朝ごはん', key='breakfast')
    with c2:
        st.text_input('昼ごはん', key='lunch')
    with c3:
        st.text_input('晩ごはん', key='dinner')
    st.text_area('日記本文', key='content', height=180)
    c1, c2 = st.columns(2)
    with c1:
        save = st.form_submit_button('新規保存', use_container_width=True)
    with c2:
        update = st.form_submit_button('更新', use_container_width=True, disabled=st.session_state.selected_id is None)
if save:
    save_entry()
    st.rerun()
if update:
    update_entry()
    st.rerun()

c1, c2 = st.columns(2)
with c1:
    if st.button('入力欄をクリア', use_container_width=True):
        clear_form()
        st.rerun()
with c2:
    if st.session_state.selected_id is not None:
        with st.popover('選択中の日記を削除', use_container_width=True):
            st.warning('この日記を削除しますか？ この操作は取り消せません。')
            if st.button('削除を確定', type='primary'):
                with connect() as conn:
                    conn.execute('DELETE FROM diary_entries WHERE id=?', (st.session_state.selected_id,))
                clear_form()
                st.session_state.notice = '日記を削除しました。'
                st.rerun()

st.divider()
st.subheader('日付検索・日記一覧')
c1, c2 = st.columns([1, 2])
with c1:
    search_day = st.date_input('検索日', value=date.today(), key='search_day')
with c2:
    only_day = st.checkbox('指定した日付のみ表示', value=False)

df = list_entries(search_day if only_day else None)
if df.empty:
    st.info('該当する日記はありません。')
else:
    display = df[['id', 'diary_date', 'breakfast', 'lunch', 'dinner']].rename(columns={
        'id': 'ID', 'diary_date': '日付', 'breakfast': '朝ごはん', 'lunch': '昼ごはん', 'dinner': '晩ごはん'
    })
    st.dataframe(display, hide_index=True, use_container_width=True)
    options = df['id'].astype(int).tolist()
    chosen = st.selectbox('編集する日記を選択（ID）', options=options,
                          format_func=lambda i: f"{df.loc[df['id'] == i, 'diary_date'].iloc[0]}（ID: {i}）",
                          index=None, placeholder='日記を選択してください')
    if st.button('選択した日記を編集欄に読み込む', disabled=chosen is None):
        select_entry(int(chosen))
        st.rerun()

st.divider()
st.subheader('バックアップ・復元')
st.caption('CloudのローカルSQLiteデータは永続保存されません。定期的にバックアップを保存してください。')
with connect() as conn:
    with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
        backup_conn = sqlite3.connect(tmp.name)
        try:
            conn.backup(backup_conn)
        finally:
            backup_conn.close()
        backup_bytes = Path(tmp.name).read_bytes()
st.download_button('日記データベースをバックアップ', data=backup_bytes,
                   file_name=f'diary_backup_{datetime.now():%Y%m%d_%H%M%S}.db', mime='application/octet-stream')

uploaded = st.file_uploader('バックアップ（.db）を復元', type=['db'])
if uploaded is not None:
    st.warning('復元すると現在の全データがバックアップ内容で置き換わります。')
    if st.button('バックアップを復元する', type='primary'):
        try:
            with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
                tmp.write(uploaded.getvalue())
                tmp.flush()
                source = sqlite3.connect(f'file:{tmp.name}?mode=ro', uri=True)
                try:
                    check = source.execute('PRAGMA integrity_check').fetchone()[0]
                    cols = {r[1] for r in source.execute('PRAGMA table_info(diary_entries)')}
                    expected = {'id', 'diary_date', 'breakfast', 'lunch', 'dinner', 'content'}
                    if check != 'ok' or not expected.issubset(cols):
                        raise ValueError('有効な日記データベースではありません。')
                    with connect() as target:
                        source.backup(target)
                finally:
                    source.close()
            clear_form()
            st.success('バックアップを復元しました。')
            st.rerun()
        except (sqlite3.Error, ValueError) as exc:
            st.error(f'復元できませんでした: {exc}')
