import streamlit as st
import time
import json

# --- 設定 ---
GRID_SIZE = 8 # 少し広くしました
CELL_SIZE_PX = 40 # スマホで押しやすいサイズ（約40px）
st.set_page_config(page_title="Magic TD", layout="centered")

# --- 初期化 ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'tower_hp': 20,
        'enemies': [{'id': 1, 'x': 0, 'y': 4, 'hp': 5}], # IDを追加管理
        'towers': {}, # {(x, y): {'type': 'magic'}}
        'money': 50, # MVPに含めなかったが画像表示のために資金を追加
        'tick': 0, # アニメーション用のカウンター
        'running': True
    }

# --- 外部CSS定義（HTMLコンポーネント内で使用） ---
# クリック時の青枠を消すなど、ゲームっぽい見た目にする
GAME_STYLE = """
<style>
    .game-grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 2px;
        max-width: 400px; /* スマホ表示を考慮 */
        margin: auto;
    }
    .cell {
        aspect-ratio: 1 / 1;
        background-color: #e0f2f1; /* 薄い緑 */
        border: 1px solid #b2dfdb;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px; /* 絵文字のサイズ */
        cursor: pointer;
        user-select: none;
        transition: background-color 0.1s;
    }
    .cell:active {
        background-color: #b2dfdb;
    }
    /* パス（道）の色 */
    .cell-path {
        background-color: #fff9c4; 
    }
</style>
"""

def draw_grid():
    """標準のボタンをCSSでカスタムして見た目を整える"""
    # 簡易CSS（ボタンを正方形に近くする）
    st.markdown("""
    <style>
    div[data-testid="column"] { width: 12% !important; padding: 1px !important; }
    button { width: 100% !important; aspect-ratio: 1/1 !important; font-size: 20px !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    state = st.session_state.game_state
    
    for y in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)
        for x in range(GRID_SIZE):
            # 表示内容の決定
            label = "🌱"
            if y == 4: label = "🛤️" # 道
            if (x, y) in state['towers']: label = "🏰"
            for e in state['enemies']:
                if e['x'] == x and e['y'] == y: label = "👿"

            with cols[x]:
                if st.button(label, key=f"btn_{x}_{y}"):
                    # クリック時の処理
                    if y != 4 and (x, y) not in state['towers'] and state['money'] >= 50:
                        state['towers'][(x, y)] = {'type': 'magic'}
                        state['money'] -= 50
                        st.rerun()

def update_game():
    """フェーズ2 & 3: 移動・攻撃ロジック（変更なし）"""
    state = st.session_state.game_state
    path_y = 4 # 固定パス
    
    # アニメーション用カウンターを進める
    state['tick'] += 1
    
    # 敵の移動
    enemies_to_remove = []
    for e in state['enemies']:
        e['x'] += 1
        # ゴール判定
        if e['x'] >= GRID_SIZE:
            state['tower_hp'] -= 1
            enemies_to_remove.append(e['id'])
            
    # ゴールした敵を削除
    state['enemies'] = [e for e in state['enemies'] if e['id'] not in enemies_to_remove]
            
    # タワー攻撃
    for pos, tower in state['towers'].items():
        target = None
        # 単純な射程チェック（隣接8マス）
        for e in state['enemies']:
            if abs(pos[0] - e['x']) <= 1 and abs(pos[1] - e['y']) <= 1:
                target = e
                break # 1体攻撃したら終了
        
        if target:
            target['hp'] -= 2 # タワー攻撃力
            # 撃破時の処理
            if target['hp'] <= 0:
                state['enemies'] = [e for e in state['enemies'] if e['id'] != target['id']]
                state['money'] += 20 # 撃破報酬
    
    # 新しい敵のスポーン（テスト用、一定確率）
    if state['tick'] % 5 == 0: # 5フレームごとに生成
        new_id = state['tick']
        state['enemies'].append({'id': new_id, 'x': 0, 'y': path_y, 'hp': 5})

# --- メイン画面表示 ---
st.title("🏰 Magic Defense Online")

# ステータス表示エリア
col1, col2, col3 = st.columns(3)
col1.metric("Castle HP", f"{st.session_state.game_state['tower_hp']} / 20", delta_color="normal")
col2.metric("Gold", f"{st.session_state.game_state['money']} G")
col3.metric("Enemies", len(st.session_state.game_state['enemies']))

if st.session_state.game_state['tower_hp'] > 0:
    # HTMLベースのグリッド描画関数を呼び出し
    draw_grid_html()
    update_game()
    
    # ゲーム速度調整（HTML使用時は少し短くてもスムーズに見える）
    time.sleep(0.5) 
    st.rerun()
else:
    st.error("GAME OVER! 城が陥落しました...")
    if st.button("リトライ"):
        del st.session_state.game_state
        st.rerun()
